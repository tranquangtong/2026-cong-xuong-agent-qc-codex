# 🧠 MCP Memory Onboarding for Codex

Chào Codex! Cậu đang đứng trong "Công xưởng agent QC". Để hiểu được các kiến thức, quyết định kiến trúc và bugfix mà tớ (Antigravity) đã lưu lại, cậu cần kết nối với **MCP Memory Server**.

Do đây là một server tùy chỉnh bằng Python, cậu cần tự "reconstruct" nó theo các bước sau:

## 🛠 1. Source Code (`memory_server.py`)

Hãy dùng tool `write_to_file` để tạo file `memory_server.py` với nội dung sau:

```python
import sqlite3
import os
import json
from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP("Memory")
# Cấu hình mặc định
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "memory_config.json")
DB_PATH = os.path.expanduser("~/.gemini/antigravity/memory_v1.db")

# Load config từ Google Drive
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            db_dir = os.path.expanduser(config.get("db_directory", ""))
            db_name = config.get("db_name", "memory_v1.db")
            if db_dir:
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                DB_PATH = os.path.join(db_dir, db_name)
    except Exception as e:
        print(f"Error loading config: {e}")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tags TEXT,
            project_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_content ON memories(content)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories(tags)')
    conn.commit()
    conn.close()

init_db()

@mcp.tool()
def add_memory(content: str, tags: str = "", project_path: str = "") -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memories (content, tags, project_path) VALUES (?, ?, ?)", (content, tags, project_path))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return f"Memory added (ID: {new_id}): {content[:50]}..."

@mcp.tool()
def search_memories(query: str = "", tag: str = "", project_path: str = "") -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = "SELECT id, content, tags, project_path, created_at FROM memories WHERE 1=1"
    params = []
    if query: sql += " AND content LIKE ?"; params.append(f"%{query}%")
    if tag: sql += " AND tags LIKE ?"; params.append(f"%{tag}%")
    if project_path: sql += " AND project_path LIKE ?"; params.append(f"%{project_path}%")
    sql += " ORDER BY created_at DESC LIMIT 20"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "No matching memories found."
    results = [f"[ID: {r[0]}] {r[4]} | Tags: {r[2]} | Path: {r[3]}\nContent: {r[1]}\n---" for r in rows]
    return "\n".join(results)

@mcp.tool()
def get_all_memories(limit: int = 50) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, tags, created_at FROM memories ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Memory list is empty."
    return "\n".join([f"[ID: {r[0]}] {r[3]} | Tags: {r[2]}\nContent: {r[1]}\n---" for r in rows])

if __name__ == "__main__":
    mcp.run()
```

## 🛠 2. Dependencies & Cấu hình

1.  **Cài đặt thư viện**: `pip install fastmcp`
2.  **Tạo file `memory_config.json`** cùng thư mục với `memory_server.py`:
    ```json
    {
      "db_directory": "G:/My Drive/MCP_Memory",
      "db_name": "memory_v1.db"
    }
    ```

## 🛠 3. Cấu hình MCP Settings (VS Code)

Hãy cập nhật `mcp_settings.json` của cậu (Cline/Roo Code):

```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": [
        "ĐƯỜNG_DẪN_ĐẾN_FILE/memory_server.py"
      ]
    }
  }
}
```

---

## 🎯 4. Nhiệm vụ đầu tiên cho Codex

Sau khi cài đặt xong, hãy chạy lệnh sau để kiểm tra kết nối:
1. **Lệnh**: `search_memories(query="migration")`
2. **Kỳ vọng**: Cậu sẽ thấy các Memory về dự án này.

---
*File này chứa toàn bộ source code để Codex có thể tự cài đặt mà không cần User can thiệp.*
