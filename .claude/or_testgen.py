#!/usr/bin/env python3
"""
Test artefact generation (OpenRouter-powered).

Usage:
    python .claude/or_testgen.py --target Scripts/foo.py [--output Output/tests/test_foo.py]

Generates a pytest test module for the target file via OpenRouter (free model) and
writes it under Output/tests/ by default. Pure offload -> minimal Claude-Code tokens.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import or_client  # noqa: E402

SYSTEM = (
    "You are a senior Python test engineer. Given a source module, write a thorough "
    "pytest test module covering happy paths, edge cases, and error handling. "
    "Use only the standard library plus pytest. Return ONLY raw Python code -- no "
    "markdown fences, no prose."
)


def strip_fences(text):
    m = re.search(r"```(?:python)?\s*\n?(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--output", default="")
    args = ap.parse_args()

    src = Path(args.target)
    if not src.is_file():
        or_client.safe_print("[testgen] target not found: " + str(src))
        sys.exit(1)
    code = src.read_text(encoding="utf-8", errors="ignore")[:12000]

    out = Path(args.output) if args.output else Path("Output") / "tests" / ("test_" + src.stem + ".py")
    out.parent.mkdir(parents=True, exist_ok=True)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "Module path: " + str(src) + "\n\nSource:\n" + code},
    ]
    tests, provider = or_client.chat(messages, max_tokens=4096)
    out.write_text(strip_fences(tests) + "\n", encoding="utf-8")
    or_client.safe_print("[testgen] " + provider + " -> " + str(out))


if __name__ == "__main__":
    main()
