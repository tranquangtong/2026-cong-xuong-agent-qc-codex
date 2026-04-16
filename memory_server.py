import json
import os
import sqlite3

from fastmcp import FastMCP


mcp = FastMCP("Memory")

# Cấu hình mặc định
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "memory_config.json")
DB_PATH = os.path.expanduser("~/.gemini/antigravity/memory_v1.db")


# Load config từ Google Drive
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tags TEXT,
            project_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_content ON memories(content)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories(tags)")
    conn.commit()
    conn.close()


init_db()


@mcp.tool()
def add_memory(content: str, tags: str = "", project_path: str = "") -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memories (content, tags, project_path) VALUES (?, ?, ?)",
        (content, tags, project_path),
    )
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
    if query:
        sql += " AND content LIKE ?"
        params.append(f"%{query}%")
    if tag:
        sql += " AND tags LIKE ?"
        params.append(f"%{tag}%")
    if project_path:
        sql += " AND project_path LIKE ?"
        params.append(f"%{project_path}%")
    sql += " ORDER BY created_at DESC LIMIT 20"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No matching memories found."

    results = [
        f"[ID: {row[0]}] {row[4]} | Tags: {row[2]} | Path: {row[3]}\nContent: {row[1]}\n---"
        for row in rows
    ]
    return "\n".join(results)


@mcp.tool()
def get_all_memories(limit: int = 50) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, content, tags, created_at FROM memories ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Memory list is empty."

    return "\n".join(
        [
            f"[ID: {row[0]}] {row[3]} | Tags: {row[2]}\nContent: {row[1]}\n---"
            for row in rows
        ]
    )


if __name__ == "__main__":
    mcp.run()
