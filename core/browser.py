from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

from core.utils import ensure_text_file


class BrowserActionable(TypedDict, total=False):
    action_id: str
    role: str
    name: str
    href: str
    in_main: bool
    in_nav: bool
    in_footer: bool
    disabled: bool
    checked: bool
    selected: bool
    tag: str


class BrowserVisitedState(TypedDict, total=False):
    step: str
    matched_label: str
    page_url: str
    title: str
    body_excerpt: str
    content_excerpt: str
    snapshot_excerpt: str
    screenshot_path: str
    progress_label: str
    lesson_label: str
    state_signature: str
    path_actions: list[str]
    actionables: list[BrowserActionable]


class BrowserProbeResult(TypedDict, total=False):
    available: bool
    status: str
    url: str
    page_url: str
    asset_url: str
    lesson_url: str
    lesson_reached: bool
    title: str
    shell_title: str
    body_text: str
    shell_body_text: str
    content_text: str
    snapshot_text: str
    screenshot_path: str
    artifacts: list[str]
    warnings: list[str]
    error: str
    console_summary: str
    visited_states: list[BrowserVisitedState]
    actions_attempted: int
    actions_changed_state: int


_PAGE_TITLE_PATTERN = re.compile(r"- Page Title:\s*(.+)")
_PAGE_URL_PATTERN = re.compile(r"- Page URL:\s*(.+)")
_CONSOLE_PATTERN = re.compile(r"- Console:\s*(.+)")
_COOKIE_BUTTON_PATTERNS = (
    r'button "Reject Non-Essential".*?\[ref=(e\d+)\]',
    r'button "Accept All".*?\[ref=(e\d+)\]',
    r'button "Close this dialog".*?\[ref=(e\d+)\]',
)
_ARTICULATE_ASSET_PATTERN = re.compile(r"https://articulateusercontent\.com/review/uploads/[^\s\"']+/index\.html(?:[?#][^\s\"']*)?")
_GENERIC_IGNORE_LABELS = {
    "current version",
    "feedback",
    "sign in",
    "comments",
    "cancel",
    "post",
    "terms",
    "privacy",
    "support",
    "cookie preferences",
    "close navigation menu",
    "close search menu",
    "skip to lesson",
    "home",
}
_PROGRESSION_TOKENS = ("start", "continue", "next", "ready", "submit", "take again", "start over")


def _playwright_wrapper_path() -> Path:
    codex_home = Path(os.getenv("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills" / "playwright" / "scripts" / "playwright_cli.sh"


def playwright_is_available() -> bool:
    wrapper = _playwright_wrapper_path()
    if not wrapper.exists():
        return False
    return subprocess.run(
        ["sh", "-lc", "command -v npx >/dev/null 2>&1"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def _run_playwright_command(
    *,
    session_id: str,
    artifacts_dir: Path,
    args: list[str],
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PLAYWRIGHT_CLI_SESSION"] = session_id
    wrapper = str(_playwright_wrapper_path())
    return subprocess.run(
        [wrapper, *args],
        cwd=artifacts_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _extract_first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _extract_eval_result(text: str) -> str:
    marker = "### Result"
    if marker not in text:
        return ""
    trailing = text.split(marker, 1)[1].lstrip()
    if not trailing:
        return ""
    first_line = trailing.splitlines()[0].strip()
    if not first_line:
        return ""
    if first_line.startswith('"') and first_line.endswith('"'):
        try:
            parsed = json.loads(first_line)
            return parsed if isinstance(parsed, str) else str(parsed)
        except json.JSONDecodeError:
            return first_line[1:-1].replace('\\"', '"').strip()
    return first_line


def _best_title_text(raw_text: str) -> str:
    return _extract_first_match(_PAGE_TITLE_PATTERN, raw_text) or _extract_eval_result(raw_text) or raw_text.strip()


def _best_body_text(raw_text: str) -> str:
    return _extract_eval_result(raw_text) or raw_text.strip()


def _extract_console_summary(*texts: str) -> str:
    for text in texts:
        summary = _extract_first_match(_CONSOLE_PATTERN, text)
        if summary:
            return summary
    return ""


def _cookie_banner_ref(snapshot_text: str) -> str:
    for pattern in _COOKIE_BUTTON_PATTERNS:
        match = re.search(pattern, snapshot_text, flags=re.DOTALL)
        if match:
            return match.group(1)
    return ""


def _truncate(text: str, limit: int = 2000) -> str:
    return text[:limit] if text else ""


def _extract_articulate_asset_url(*texts: str) -> str:
    for text in texts:
        if not text:
            continue
        for candidate in (text, _extract_eval_result(text)):
            if not candidate:
                continue
            match = _ARTICULATE_ASSET_PATTERN.search(candidate)
            if match:
                return match.group(0)
    return ""


def _extract_json_eval(text: str) -> dict[str, Any]:
    payload = _extract_eval_result(text)
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {}


def _eval_json(session_id: str, artifacts_dir: Path, expression: str, timeout: int = 120) -> dict[str, Any]:
    result = _run_playwright_command(
        session_id=session_id,
        artifacts_dir=artifacts_dir,
        args=["eval", expression],
        timeout=timeout,
    )
    return _extract_json_eval((result.stdout or result.stderr).strip())


def _wait_for_page(session_id: str, artifacts_dir: Path, milliseconds: int = 900) -> None:
    _run_playwright_command(
        session_id=session_id,
        artifacts_dir=artifacts_dir,
        args=["run-code", f"await page.waitForTimeout({milliseconds});"],
        timeout=max(30, milliseconds // 10 + 30),
    )


def _capture_screenshot(session_id: str, artifacts_dir: Path) -> str:
    before_files = {path.name for path in artifacts_dir.iterdir() if path.is_file()}
    screenshot_run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["screenshot"])
    if screenshot_run.returncode != 0:
        return ""
    after_files = {path.name for path in artifacts_dir.iterdir() if path.is_file()}
    new_files = sorted(after_files - before_files)
    if not new_files:
        return ""
    return str(artifacts_dir / new_files[0])


def _dom_state_expression() -> str:
    return """
(() => {
  const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
  const isVisible = (element) => {
    if (!element || !element.isConnected) return false;
    const style = window.getComputedStyle(element);
    if (!style || style.visibility === 'hidden' || style.display === 'none') return false;
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };
  const inferRole = (element) => {
    const explicit = element.getAttribute('role');
    if (explicit) return explicit.toLowerCase();
    const tag = element.tagName.toLowerCase();
    if (tag === 'a') return 'link';
    if (tag === 'button') return 'button';
    if (tag === 'select') return 'combobox';
    if (tag === 'textarea') return 'textbox';
    if (tag === 'input') {
      const type = (element.getAttribute('type') || 'text').toLowerCase();
      if (type === 'radio') return 'radio';
      if (type === 'checkbox') return 'checkbox';
      if (type === 'submit' || type === 'button') return 'button';
      return 'textbox';
    }
    return tag;
  };
  const textFor = (element) => normalize(
    element.innerText ||
    element.textContent ||
    element.value ||
    element.getAttribute('aria-label') ||
    element.getAttribute('title') ||
    ''
  );
  const mainRoot = document.querySelector('main,[role="main"]') || document.body;
  const lessonHeader = Array.from(document.querySelectorAll('h1,h2,h3,.lesson-title,.section-title'))
    .map((node) => normalize(node.textContent || ''))
    .find(Boolean) || '';
  const progressLabel = Array.from(document.querySelectorAll('[aria-label*="Completed"], img[alt*="Completed"], .progress, [class*="progress"]'))
    .map((node) => normalize(node.getAttribute('aria-label') || node.getAttribute('alt') || node.textContent || ''))
    .find((value) => /\\bcompleted\\b|\\bcomplete\\b/i.test(value)) || '';
  const candidates = Array.from(document.querySelectorAll('a,button,input,select,textarea,[role="button"],[role="tab"],[role="radio"],[role="checkbox"],[role="option"]'));
  const actionables = [];
  let visibleIndex = 0;
  for (const element of candidates) {
    if (!isVisible(element)) continue;
    const role = inferRole(element);
    const name = textFor(element);
    if (!name && !['radio', 'checkbox'].includes(role)) continue;
    const href = element.getAttribute('href') || '';
    const tag = element.tagName.toLowerCase();
    const disabled = !!(element.disabled || element.getAttribute('aria-disabled') === 'true');
    const checked = !!(element.checked || element.getAttribute('aria-checked') === 'true');
    const selected = !!(element.selected || element.getAttribute('aria-selected') === 'true');
    const inMain = !!(mainRoot && mainRoot.contains(element));
    const inNav = !!element.closest('nav,[role="navigation"]');
    const inFooter = !!element.closest('footer');
    const actionId = [role, name, href, inMain ? 'main' : 'other', inNav ? 'nav' : 'body', visibleIndex].join('|');
    visibleIndex += 1;
    actionables.push({
      action_id: actionId,
      role,
      name,
      href,
      in_main: inMain,
      in_nav: inNav,
      in_footer: inFooter,
      disabled,
      checked,
      selected,
      tag,
    });
  }
  const bodyText = normalize(document.body ? document.body.innerText : '');
  const mainText = normalize(mainRoot ? mainRoot.innerText : bodyText);
  return JSON.stringify({
    page_url: location.href,
    title: normalize(document.title || ''),
    body_text: bodyText,
    main_text: mainText,
    progress_label: progressLabel,
    lesson_label: lessonHeader,
    actionables,
  });
})()
""".strip()


def _click_action_expression(action_id: str) -> str:
    target_id = json.dumps(action_id, ensure_ascii=False)
    return f"""
(() => {{
  const targetId = {target_id};
  const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
  const isVisible = (element) => {{
    if (!element || !element.isConnected) return false;
    const style = window.getComputedStyle(element);
    if (!style || style.visibility === 'hidden' || style.display === 'none') return false;
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }};
  const inferRole = (element) => {{
    const explicit = element.getAttribute('role');
    if (explicit) return explicit.toLowerCase();
    const tag = element.tagName.toLowerCase();
    if (tag === 'a') return 'link';
    if (tag === 'button') return 'button';
    if (tag === 'select') return 'combobox';
    if (tag === 'textarea') return 'textbox';
    if (tag === 'input') {{
      const type = (element.getAttribute('type') || 'text').toLowerCase();
      if (type === 'radio') return 'radio';
      if (type === 'checkbox') return 'checkbox';
      if (type === 'submit' || type === 'button') return 'button';
      return 'textbox';
    }}
    return tag;
  }};
  const textFor = (element) => normalize(
    element.innerText ||
    element.textContent ||
    element.value ||
    element.getAttribute('aria-label') ||
    element.getAttribute('title') ||
    ''
  );
  const mainRoot = document.querySelector('main,[role="main"]') || document.body;
  const candidates = Array.from(document.querySelectorAll('a,button,input,select,textarea,[role="button"],[role="tab"],[role="radio"],[role="checkbox"],[role="option"]'));
  let visibleIndex = 0;
  for (const element of candidates) {{
    if (!isVisible(element)) continue;
    const role = inferRole(element);
    const name = textFor(element);
    if (!name && !['radio', 'checkbox'].includes(role)) continue;
    const href = element.getAttribute('href') || '';
    const inMain = !!(mainRoot && mainRoot.contains(element));
    const inNav = !!element.closest('nav,[role="navigation"]');
    const actionId = [role, name, href, inMain ? 'main' : 'other', inNav ? 'nav' : 'body', visibleIndex].join('|');
    visibleIndex += 1;
    if (actionId !== targetId) continue;
    element.scrollIntoView({{ block: 'center', inline: 'center' }});
    element.click();
    return JSON.stringify({{
      clicked: true,
      action_id: actionId,
      matched_label: name,
      href: location.href
    }});
  }}
  return JSON.stringify({{
    clicked: false,
    action_id: targetId,
    matched_label: '',
    href: location.href
  }});
}})()
""".strip()


def _normalize_actionables(raw_actionables: list[dict[str, Any]]) -> list[BrowserActionable]:
    actionables: list[BrowserActionable] = []
    for item in raw_actionables:
        actionables.append(
            {
                "action_id": str(item.get("action_id", "")),
                "role": str(item.get("role", "")),
                "name": str(item.get("name", "")),
                "href": str(item.get("href", "")),
                "in_main": bool(item.get("in_main", False)),
                "in_nav": bool(item.get("in_nav", False)),
                "in_footer": bool(item.get("in_footer", False)),
                "disabled": bool(item.get("disabled", False)),
                "checked": bool(item.get("checked", False)),
                "selected": bool(item.get("selected", False)),
                "tag": str(item.get("tag", "")),
            }
        )
    return actionables


def _state_signature(page_url: str, main_text: str, actionables: list[BrowserActionable]) -> str:
    payload = json.dumps(
        {
            "page_url": page_url,
            "main_text": _truncate(main_text, 1500),
            "actionables": [
                {
                    "role": item.get("role", ""),
                    "name": item.get("name", ""),
                    "href": item.get("href", ""),
                    "disabled": item.get("disabled", False),
                    "checked": item.get("checked", False),
                    "selected": item.get("selected", False),
                }
                for item in actionables[:30]
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _capture_page_state(
    *,
    session_id: str,
    artifacts_dir: Path,
    step: str,
    matched_label: str = "",
    take_screenshot: bool = False,
    path_actions: list[str] | None = None,
) -> BrowserVisitedState:
    snapshot_run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["snapshot"])
    snapshot_text = (snapshot_run.stdout or snapshot_run.stderr).strip()
    dom_payload = _eval_json(session_id, artifacts_dir, _dom_state_expression())

    page_url = str(dom_payload.get("page_url", "")) or _extract_first_match(_PAGE_URL_PATTERN, snapshot_text)
    title_text = str(dom_payload.get("title", "")) or _best_title_text(snapshot_text)
    body_text = str(dom_payload.get("body_text", ""))
    content_text = str(dom_payload.get("main_text", "")) or body_text
    actionables = _normalize_actionables(list(dom_payload.get("actionables", [])))
    signature = _state_signature(page_url, content_text, actionables)

    state: BrowserVisitedState = {
        "step": step,
        "page_url": page_url,
        "title": title_text,
        "body_excerpt": _truncate(body_text, 4000),
        "content_excerpt": _truncate(content_text, 4000),
        "snapshot_excerpt": _truncate(snapshot_text, 4000),
        "progress_label": str(dom_payload.get("progress_label", "")),
        "lesson_label": str(dom_payload.get("lesson_label", "")),
        "state_signature": signature,
        "path_actions": list(path_actions or []),
        "actionables": actionables,
    }
    if matched_label:
        state["matched_label"] = matched_label
    if take_screenshot:
        screenshot_path = _capture_screenshot(session_id, artifacts_dir)
        if screenshot_path:
            state["screenshot_path"] = screenshot_path
    return state


def _resolve_asset_url(session_id: str, artifacts_dir: Path, *evidence_texts: str) -> str:
    expression = (
        "(() => {"
        "const names = performance.getEntriesByType('resource').map((entry) => entry.name);"
        "return names.find((name) => /articulateusercontent\\.com\\/review\\/uploads\\/.+\\/index\\.html(?:[?#].*)?$/.test(name)) || '';"
        "})()"
    )
    asset_run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["eval", expression])
    raw_output = (asset_run.stdout or asset_run.stderr).strip()
    network_run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["network"])
    network_text = (network_run.stdout or network_run.stderr).strip()
    console_texts: list[str] = []
    console_dir = artifacts_dir / ".playwright-cli"
    if console_dir.exists():
        for path in sorted(console_dir.glob("console-*.log"))[-5:]:
            try:
                console_texts.append(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return _extract_articulate_asset_url(raw_output, network_text, *console_texts, *evidence_texts)


def _click_action(session_id: str, artifacts_dir: Path, action_id: str) -> dict[str, Any]:
    payload = _eval_json(session_id, artifacts_dir, _click_action_expression(action_id))
    if payload:
        return payload
    return {"clicked": False, "action_id": action_id, "matched_label": ""}


def _write_json_artifact(path: Path, payload: dict[str, Any]) -> str:
    ensure_text_file(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


def _goto(session_id: str, artifacts_dir: Path, url: str) -> bool:
    run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["goto", url])
    if run.returncode != 0:
        return False
    _wait_for_page(session_id, artifacts_dir, 1200)
    return True


def _replay_path(session_id: str, artifacts_dir: Path, asset_url: str, path_actions: list[str]) -> bool:
    if not _goto(session_id, artifacts_dir, asset_url):
        return False
    for action_id in path_actions:
        click_payload = _click_action(session_id, artifacts_dir, action_id)
        if not click_payload.get("clicked"):
            return False
        _wait_for_page(session_id, artifacts_dir, 1200)
    return True


def _candidate_actions(state: BrowserVisitedState) -> list[BrowserActionable]:
    page_url = str(state.get("page_url", ""))
    lesson_route = "#/lessons/" in page_url
    scored: list[tuple[int, BrowserActionable]] = []

    for action in state.get("actionables", []):
        action_id = str(action.get("action_id", ""))
        name = str(action.get("name", "")).strip()
        normalized_name = name.lower()
        href = str(action.get("href", ""))
        role = str(action.get("role", ""))

        if not action_id or not name:
            continue
        if action.get("disabled") or action.get("in_footer"):
            continue
        if normalized_name in _GENERIC_IGNORE_LABELS:
            continue
        if href.startswith("http://") or href.startswith("https://"):
            continue

        score = 0
        if action.get("in_main"):
            score += 50
        if not action.get("in_nav"):
            score += 15
        if href.startswith("#/lessons/"):
            score += 70 if not lesson_route else -35
        if role == "tab":
            score += 45
        if role in {"radio", "checkbox"}:
            score += 30
        if role == "button":
            score += 20
        if role == "link" and not href.startswith("#/lessons/"):
            score -= 25
        if any(token in normalized_name for token in _PROGRESSION_TOKENS):
            score += 25
        if lesson_route and href.startswith("#/lessons/") and href not in page_url:
            score -= 45
        if action.get("checked") or action.get("selected"):
            score -= 10
        if action.get("in_nav"):
            score -= 15

        scored.append((score, action))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [action for score, action in scored if score > 0]


def run_playwright_probe(url: str, output_dir: Path, request_text: str = "") -> BrowserProbeResult:
    del request_text
    result: BrowserProbeResult = {
        "available": playwright_is_available(),
        "status": "unavailable",
        "url": url,
        "artifacts": [],
        "warnings": [],
        "visited_states": [],
        "lesson_reached": False,
        "actions_attempted": 0,
        "actions_changed_state": 0,
    }
    if not result["available"]:
        result["warnings"].append("Playwright CLI wrapper or npx is not available in the current environment.")
        return result

    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    session_id = f"id-qc-{uuid4().hex[:8]}"
    max_states = 8
    max_depth = 3
    max_actions_per_state = 4

    try:
        open_run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["open", url])
        if open_run.returncode != 0:
            result["status"] = "open_failed"
            result["error"] = open_run.stderr.strip() or open_run.stdout.strip() or "Playwright open failed."
            result["warnings"].append("Playwright could not open the target URL.")
            return result

        _wait_for_page(session_id, artifacts_dir)
        initial_snapshot_run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["snapshot"])
        initial_snapshot_text = (initial_snapshot_run.stdout or initial_snapshot_run.stderr).strip()
        cookie_ref = _cookie_banner_ref(initial_snapshot_text)
        if cookie_ref:
            click_run = _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["click", cookie_ref])
            if click_run.returncode != 0:
                result["warnings"].append(
                    f"Attempted to dismiss cookie banner via {cookie_ref}, but the click did not complete cleanly."
                )
            else:
                _wait_for_page(session_id, artifacts_dir, 700)

        review_state = _capture_page_state(
            session_id=session_id,
            artifacts_dir=artifacts_dir,
            step="review_shell",
            take_screenshot=True,
        )
        result["visited_states"].append(review_state)
        shell_snapshot_text = review_state.get("snapshot_excerpt", "")
        shell_body_text = review_state.get("body_excerpt", "")
        shell_title = review_state.get("title", "")
        console_summary = _extract_console_summary(initial_snapshot_text, shell_snapshot_text)

        _wait_for_page(session_id, artifacts_dir, 2500)
        asset_url = _resolve_asset_url(session_id, artifacts_dir, initial_snapshot_text, shell_snapshot_text, shell_body_text)
        review_shell_payload = {
            "url": url,
            "title": shell_title,
            "page_url": review_state.get("page_url", ""),
            "asset_url": asset_url,
            "body_excerpt": shell_body_text,
            "snapshot_excerpt": shell_snapshot_text,
            "console_summary": console_summary,
            "cookie_banner_ref": cookie_ref,
            "open_status": open_run.returncode,
            "snapshot_status": initial_snapshot_run.returncode,
        }
        review_shell_path = Path(artifacts_dir / "review_shell_probe.json")
        result["artifacts"].append(_write_json_artifact(review_shell_path, review_shell_payload))
        if review_state.get("screenshot_path"):
            result["artifacts"].append(review_state["screenshot_path"])

        if not asset_url:
            result["warnings"].append(
                "Playwright opened the Review 360 shell, but no direct Articulate asset URL was resolved from the page resources."
            )
        elif _goto(session_id, artifacts_dir, asset_url):
            asset_state = _capture_page_state(
                session_id=session_id,
                artifacts_dir=artifacts_dir,
                step="asset_landing",
                take_screenshot=True,
                path_actions=[],
            )
            result["visited_states"].append(asset_state)
            if asset_state.get("screenshot_path"):
                result["artifacts"].append(asset_state["screenshot_path"])

            queue: list[tuple[BrowserVisitedState, int]] = [(asset_state, 0)]
            seen_signatures = {state.get("state_signature", "") for state in result["visited_states"]}
            attempted_action_paths: set[str] = set()

            while queue and len(result["visited_states"]) < max_states:
                current_state, depth = queue.pop(0)
                if depth >= max_depth:
                    continue
                for action in _candidate_actions(current_state)[:max_actions_per_state]:
                    action_id = str(action.get("action_id", ""))
                    attempt_key = f"{current_state.get('state_signature', '')}:{action_id}"
                    if not action_id or attempt_key in attempted_action_paths:
                        continue
                    attempted_action_paths.add(attempt_key)
                    result["actions_attempted"] += 1

                    path_actions = list(current_state.get("path_actions", []))
                    if not _replay_path(session_id, artifacts_dir, asset_url, path_actions):
                        continue
                    click_payload = _click_action(session_id, artifacts_dir, action_id)
                    if not click_payload.get("clicked"):
                        continue
                    _wait_for_page(session_id, artifacts_dir, 1200)
                    next_state = _capture_page_state(
                        session_id=session_id,
                        artifacts_dir=artifacts_dir,
                        step=f"state_{len(result['visited_states'])}",
                        matched_label=str(click_payload.get("matched_label", "")) or action.get("name", ""),
                        take_screenshot=True,
                        path_actions=[*path_actions, action_id],
                    )
                    if next_state.get("state_signature") == current_state.get("state_signature"):
                        continue
                    result["actions_changed_state"] += 1
                    signature = str(next_state.get("state_signature", ""))
                    if signature in seen_signatures:
                        continue
                    seen_signatures.add(signature)
                    result["visited_states"].append(next_state)
                    if next_state.get("screenshot_path"):
                        result["artifacts"].append(next_state["screenshot_path"])
                    queue.append((next_state, depth + 1))
                    if len(result["visited_states"]) >= max_states:
                        break
        else:
            result["warnings"].append("Playwright resolved a Rise asset URL but could not navigate to it.")

        last_state = result["visited_states"][-1] if result["visited_states"] else {}
        lesson_state = next(
            (
                state
                for state in reversed(result["visited_states"])
                if "#/lessons/" in state.get("page_url", "")
            ),
            {},
        )
        lesson_url = lesson_state.get("page_url", "")
        lesson_reached = bool(lesson_url)

        section_probe_payload = {
            "review_url": url,
            "asset_url": asset_url,
            "lesson_url": lesson_url,
            "lesson_reached": lesson_reached,
            "actions_attempted": result["actions_attempted"],
            "actions_changed_state": result["actions_changed_state"],
            "visited_states": result["visited_states"],
        }
        section_probe_path = Path(artifacts_dir / "section_probe.json")
        result["artifacts"].append(_write_json_artifact(section_probe_path, section_probe_payload))

        summary_payload = {
            "url": url,
            "page_url": last_state.get("page_url", review_state.get("page_url", "")),
            "asset_url": asset_url,
            "lesson_url": lesson_url,
            "lesson_reached": lesson_reached,
            "title": last_state.get("title", shell_title),
            "shell_title": shell_title,
            "body_excerpt": last_state.get("body_excerpt", shell_body_text),
            "content_excerpt": last_state.get("content_excerpt", ""),
            "shell_body_excerpt": shell_body_text,
            "visited_state_count": len(result["visited_states"]),
            "actions_attempted": result["actions_attempted"],
            "actions_changed_state": result["actions_changed_state"],
            "console_summary": console_summary,
        }
        probe_path = Path(artifacts_dir / "playwright_probe.json")
        result["artifacts"].append(_write_json_artifact(probe_path, summary_payload))

        result["status"] = "lesson_captured" if lesson_reached else ("asset_captured" if asset_url else "captured")
        result["page_url"] = last_state.get("page_url", review_state.get("page_url", ""))
        result["asset_url"] = asset_url
        result["lesson_url"] = lesson_url
        result["lesson_reached"] = lesson_reached
        result["title"] = last_state.get("title", shell_title)
        result["shell_title"] = shell_title
        result["body_text"] = last_state.get("body_excerpt", shell_body_text)
        result["content_text"] = last_state.get("content_excerpt", "")
        result["shell_body_text"] = shell_body_text
        result["snapshot_text"] = last_state.get("snapshot_excerpt", shell_snapshot_text)
        result["console_summary"] = console_summary
        if last_state.get("screenshot_path"):
            result["screenshot_path"] = last_state["screenshot_path"]
        elif review_state.get("screenshot_path"):
            result["screenshot_path"] = review_state["screenshot_path"]

        if asset_url and not lesson_reached:
            result["warnings"].append(
                "Playwright reached the Rise asset page but did not advance into a lesson-level '#/lessons/...' state."
            )
        if len(result["visited_states"]) >= max_states:
            result["warnings"].append("Playwright traversal hit the current state limit before exhausting every interaction path.")
        if console_summary:
            result["warnings"].append(f"Browser console summary: {console_summary}")
        return result
    finally:
        _run_playwright_command(session_id=session_id, artifacts_dir=artifacts_dir, args=["close"], timeout=30)
