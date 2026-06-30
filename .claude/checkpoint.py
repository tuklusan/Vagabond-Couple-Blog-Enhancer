#!/usr/bin/env python3
"""
Commit + push checkpoint -- the ONLY place in this project that pushes.

Policy (see CLAUDE.md). A commit+push checkpoint happens at exactly three points:
  (a) before sending code/docs out for review
  (b) after completing a defect ticket
  (c) after implementing review comments, before sending for review again

Usage:
    python .claude/checkpoint.py --reason "before-review: TICKET-0007"
    python .claude/checkpoint.py --reason "ticket-closed: TICKET-0007"

The commit runs through the hard review gate (.git/hooks/pre-commit, NO --no-verify),
so a checkpoint containing Critical findings is BLOCKED and nothing is pushed.
Use --no-gate only for emergencies.
"""
import argparse
import subprocess
import sys
from datetime import datetime


def safe_write(stream, text):
    stream.write((text or "").encode("ascii", "replace").decode("ascii"))


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reason", required=True, help="why this checkpoint fires (a/b/c + context)")
    ap.add_argument("--no-gate", action="store_true", help="bypass review gate (emergency only)")
    args = ap.parse_args()

    dirty = run(["git", "status", "--porcelain"]).stdout.strip()
    if dirty:
        run(["git", "add", "-A"])
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        msg = "checkpoint(" + args.reason + "): " + ts
        cmd = ["git", "commit", "-m", msg]
        if args.no_gate:
            cmd.insert(2, "--no-verify")
        c = run(cmd)
        safe_write(sys.stdout, c.stdout)
        safe_write(sys.stderr, c.stderr)
        if c.returncode != 0:
            print("[checkpoint] commit BLOCKED/failed -- NOT pushing (fix Critical findings above).")
            sys.exit(1)
        print("[checkpoint] committed: " + msg)
    else:
        print("[checkpoint] working tree clean -- nothing new to commit; will still sync push.")

    p = run(["git", "push"])
    safe_write(sys.stdout, p.stdout)
    safe_write(sys.stderr, p.stderr)
    if p.returncode != 0:
        print("[checkpoint] push FAILED (see above).")
        sys.exit(1)
    print("[checkpoint] pushed to origin. (" + args.reason + ")")
    sys.exit(0)


if __name__ == "__main__":
    main()
