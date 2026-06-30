#!/usr/bin/env python3
"""
Enforces the commit+push rule at workflow events (replaces blanket autocommit).

  --phase pre  : if the about-to-run command sends code/docs for review,
                 checkpoint FIRST  (covers rule a + c).
  --phase post : if the just-run command CLOSED a defect ticket,
                 checkpoint AFTER  (covers rule b).

Reads PreToolUse/PostToolUse JSON on stdin. Advisory: always exits 0, never blocks
the tool. Skips its own git/checkpoint commands to avoid recursion.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REVIEW_PATTERNS = [
    r"step7_review\.py",
    r"step8_quality_gate\.py",
    r"code_agent\.py",
    r"or_review_gate\.py",
]
TICKET_CLOSE = re.compile(
    r"ticket\.py\s+update\b.*--status\s+[\"']?(closed|done|resolved|fixed|complete)",
    re.IGNORECASE,
)


def run_checkpoint(reason):
    here = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(here / "checkpoint.py"), "--reason", reason])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["pre", "post"])
    args = ap.parse_args()

    try:
        hook = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = ((hook.get("tool_input") or {}).get("command")) or ""
    if not cmd:
        sys.exit(0)

    # Never recurse on our own git / checkpoint plumbing.
    if "checkpoint.py" in cmd or re.search(r"(^|\s)git(\s|$)", cmd):
        sys.exit(0)

    if args.phase == "pre":
        if any(re.search(p, cmd) for p in REVIEW_PATTERNS):
            print("[rule] (a/c) checkpoint before sending for review...")
            run_checkpoint("before-review")
    else:  # post
        if TICKET_CLOSE.search(cmd):
            print("[rule] (b) checkpoint after ticket completion...")
            run_checkpoint("ticket-closed")

    sys.exit(0)


if __name__ == "__main__":
    main()
