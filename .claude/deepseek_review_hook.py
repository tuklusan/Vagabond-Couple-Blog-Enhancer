#!/usr/bin/env python3
"""
PostToolUse hook: DeepSeek review on every Edit/Write.
- .py files      -> code review prompt
- .md/.txt files -> documentation review prompt
- other/binary   -> skipped
Exits 0 always (non-blocking, advisory only).
"""
import json
import os
import sys
from pathlib import Path

CODE_EXTENSIONS = {".py"}
DOC_EXTENSIONS  = {".md", ".txt", ".rst"}
SKIP_NAMES      = {"blogger_token.json", "client_secrets.json"}
SKIP_EXTENSIONS = {".json", ".png", ".jpg", ".gif", ".ico", ".db"}


def load_deepseek_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    key_file = Path(__file__).parent.parent / "Config" / "_SECRETS" / "deepseek-api-key.txt"
    if key_file.exists():
        for line in key_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def review(api_key: str, prompt: str, label: str) -> None:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.1,
    )
    result = response.choices[0].message.content.strip()
    print(f"\n{'='*60}")
    print(f"[DeepSeek Review] {label}")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    file_path = (hook_input.get("tool_input") or {}).get("file_path") or \
                (hook_input.get("tool_input") or {}).get("filePath")
    if not file_path:
        sys.exit(0)

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        sys.exit(0)
    if path.name in SKIP_NAMES or path.suffix.lower() in SKIP_EXTENSIONS:
        sys.exit(0)

    try:
        content = path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        sys.exit(0)

    if not content:
        sys.exit(0)

    api_key = load_deepseek_key()
    if not api_key:
        print("[DeepSeek Review] DEEPSEEK_API_KEY not found -- skipping.")
        sys.exit(0)

    ext = path.suffix.lower()

    try:
        if ext in CODE_EXTENSIONS:
            prompt = (
                f"You are a Python code reviewer for a travel blog automation project.\n"
                f"Review {path.name} for: correctness, bugs, security issues, edge cases, style.\n"
                f"Group findings as Critical / Warning / Info. Say LGTM if clean.\n\n"
                f"---\n{content[:6000]}\n---"
            )
            review(api_key, prompt, f"CODE: {path.name}")

        elif ext in DOC_EXTENSIONS:
            prompt = (
                f"You are a technical documentation reviewer for a travel blog automation project.\n"
                f"Review {path.name} for: accuracy, completeness, clarity, consistency with a software project, "
                f"and any outdated or contradictory information.\n"
                f"Group findings as Critical / Warning / Info. Say LGTM if clean.\n\n"
                f"---\n{content[:6000]}\n---"
            )
            review(api_key, prompt, f"DOC: {path.name}")

    except Exception as e:
        print(f"[DeepSeek Review] Error: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
