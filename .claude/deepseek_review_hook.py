#!/usr/bin/env python3
"""
PostToolUse advisory review hook (OpenRouter-powered).

Runs on every Edit/Write of a .py / .md / .txt / .rst file.
- Heavy review reasoning happens on OpenRouter (free) -> minimal Claude-Code tokens.
- Full review is written to Output/reviews/ ; only a ONE-LINE verdict is printed,
  so this hook no longer floods Claude's context with review text.
- Advisory only: always exits 0. The blocking gate is .git/hooks/pre-commit.

(Filename kept for settings.json compatibility; provider is now OpenRouter, not DeepSeek.)
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import or_client  # noqa: E402

CODE_EXT = {".py"}
DOC_EXT = {".md", ".txt", ".rst"}
SKIP_NAMES = {"blogger_token.json", "client_secrets.json"}
SKIP_EXT = {".json", ".png", ".jpg", ".gif", ".ico", ".db"}


def main():
    try:
        hook = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = hook.get("tool_input") or {}
    file_path = ti.get("file_path") or ti.get("filePath")
    if not file_path:
        sys.exit(0)

    path = Path(file_path)
    if not path.is_file() or path.name in SKIP_NAMES or path.suffix.lower() in SKIP_EXT:
        sys.exit(0)
    if "_SECRETS" in str(path) or path.suffix.lower() not in (CODE_EXT | DOC_EXT):
        sys.exit(0)

    try:
        content = path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        sys.exit(0)
    if not content:
        sys.exit(0)

    kind = "CODE" if path.suffix.lower() in CODE_EXT else "DOC"
    if kind == "CODE":
        sysmsg = ("You are a Python code reviewer for a travel-blog automation project. "
                  "Review for correctness, bugs, security, edge cases, style. "
                  "Group findings as Critical / Warning / Info. Say LGTM if clean.")
    else:
        sysmsg = ("You are a technical documentation reviewer for a travel-blog automation "
                  "project. Review for accuracy, completeness, clarity, consistency, and "
                  "outdated/contradictory info. Group as Critical / Warning / Info. LGTM if clean.")

    messages = [
        {"role": "system", "content": sysmsg},
        {"role": "user", "content": path.name + "\n\n---\n" + content[:6000] + "\n---"},
    ]

    try:
        review, provider = or_client.chat(messages, max_tokens=1024)
    except Exception as e:
        or_client.safe_print("[review] skipped (" + str(e) + ")")
        sys.exit(0)

    reviews_dir = Path("Output") / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out = reviews_dir / (kind.lower() + "-" + path.stem + "-" + stamp + ".md")
    out.write_text("# " + kind + " review: " + path.name + " (" + provider + ")\n\n" + review + "\n",
                   encoding="utf-8")

    has_critical = "critical" in review.lower() and "lgtm" not in review.lower()
    flag = "CRITICAL" if has_critical else "ok"
    or_client.safe_print("[review:" + flag + "] " + path.name + " -> " + str(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
