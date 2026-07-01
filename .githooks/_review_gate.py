#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
DeepSeek dev-review push gate.

Runs the .claude/dev_review.py harness over the files being pushed and decides
whether to BLOCK the push. Policy:
  * BLOCK (exit 1) if any file has an unaddressed CRITICAL finding -- and file a
    ticket for each so it is actionable.
  * FAIL OPEN (exit 0, warn) if DeepSeek is unreachable for EVERY file (an outage
    or missing key must never permanently block pushes).
  * PASS (exit 0) otherwise.

Read the file list from argv, or one-per-line on stdin ('-').
Bypass entirely with `git push --no-verify` or SKIP_DEEPSEEK_REVIEW=1.
"""
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / ".claude"))


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


def decide(results):
    """Pure decision logic (unit-testable, no network).
    Returns (exit_code, message, critical_findings)."""
    reviewed = [r for r in results if not r.get("error") and not r.get("skipped")]
    errored = [r for r in results if r.get("error")]
    criticals = [(r["file"], f) for r in results
                 for f in r.get("findings", [])
                 if str(f.get("severity", "")).lower() == "critical"]
    if criticals:
        return 1, "BLOCK: unaddressed Critical finding(s)", criticals
    if results and not reviewed:
        # Every file failed to review -> treat as an outage, fail OPEN.
        return 0, "FAIL-OPEN: DeepSeek unreachable for all files (" \
                  + str(len(errored)) + "); allowing push", []
    return 0, "PASS: no Critical findings", []


def _load_files():
    args = [a for a in sys.argv[1:] if a != "-"]
    if not args or "-" in sys.argv[1:]:
        args += [ln.strip() for ln in sys.stdin if ln.strip()]
    # de-dup, keep order
    seen, out = set(), []
    for f in args:
        if f and f not in seen and Path(REPO / f).exists():
            seen.add(f)
            out.append(f)
    return out


def main():
    if os.environ.get("SKIP_DEEPSEEK_REVIEW") == "1":
        print("[dev-review] skipped (SKIP_DEEPSEEK_REVIEW=1)")
        return 0
    files = _load_files()
    if not files:
        print("[dev-review] no reviewable files; allowing push.")
        return 0
    try:
        import dev_review
    except Exception as e:
        print(_ascii("[dev-review] harness unavailable (" + str(e)[:120]
                     + "); FAIL-OPEN, allowing push."))
        return 0

    print(_ascii("[dev-review] DeepSeek reviewing " + str(len(files))
                 + " changed file(s) before push..."))
    results = []
    for f in files:
        try:
            r = dev_review.review_file(f)
        except Exception as e:
            r = {"file": f, "findings": [], "error": str(e)[:200]}
            print(_ascii("  [error] " + f + ": " + str(e)[:120]))
        if not r.get("skipped"):
            results.append(r)

    code, msg, criticals = decide(results)
    print(_ascii("[dev-review] " + msg))
    if criticals:
        for fpath, finding in criticals:
            print(_ascii("  CRITICAL  " + fpath + " :: " + str(finding.get("title", ""))))
        # File tickets so the blockers are actionable, then block.
        try:
            created = dev_review.create_tickets(results, min_severity="critical")
            print(_ascii("[dev-review] filed " + str(len(created)) + " ticket(s) for the blockers."))
        except Exception as e:
            print(_ascii("[dev-review] (could not file tickets: " + str(e)[:100] + ")"))
        print("[dev-review] push BLOCKED. Address the Critical finding(s), or bypass with "
              "`git push --no-verify` / SKIP_DEEPSEEK_REVIEW=1.")
    return code


if __name__ == "__main__":
    sys.exit(main())
