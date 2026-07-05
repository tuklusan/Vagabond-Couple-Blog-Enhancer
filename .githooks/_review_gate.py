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
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / ".claude"))


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


def _title_tokens(title):
    return set(re.findall(r"[a-z0-9]{3,}", str(title).lower()))


def load_dismissed_fingerprints(tickets_dir):
    """Fingerprints of findings ALREADY triaged and closed as false-positive/
    duplicate in the ticket tracker (TICKET-0183). The gate re-reviews whole
    files with a fresh model call on every push, so a finding the developer
    already investigated and rejected -- with a written justification in its
    ticket -- would otherwise re-block every later push of the same file
    (observed live: 4 consecutive blocks on one batch; 7 re-rolled false
    positives vs 1 genuine finding). Only tickets whose Notes open with FALSE
    POSITIVE / DUPLICATE / NO ACTION contribute; genuinely-fixed findings do
    NOT (a regression of fixed code must still block)."""
    fps = []
    tdir = Path(tickets_dir)
    if not tdir.is_dir():
        return fps
    for p in sorted(tdir.glob("TICKET-*.md")):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Status: Closed" not in text:
            continue
        notes = text.split("Notes:", 1)[1] if "Notes:" in text else ""
        if not re.search(r"FALSE POSITIVE|DUPLICATE|NO ACTION", notes[:200], re.IGNORECASE):
            continue
        m = re.search(r"^# TICKET-\d+:\s*\[([^\]]+)\]\s*(.+)$", text, re.MULTILINE)
        if m:
            fps.append((m.group(1).strip().lower(), _title_tokens(m.group(2))))
    return fps


def _is_dismissed(file_path, finding, fingerprints):
    """A finding matches a dismissed fingerprint when it targets the same file
    (basename) and its title strongly overlaps the closed ticket's title."""
    base = Path(str(file_path)).name.lower()
    toks = _title_tokens(finding.get("title", ""))
    if not toks:
        return False
    for fp_file, fp_toks in fingerprints:
        if fp_file != base or not fp_toks:
            continue
        overlap = len(toks & fp_toks) / max(len(toks | fp_toks), 1)
        if overlap >= 0.6:
            return True
    return False


def decide(results, fingerprints=None):
    """Pure decision logic (unit-testable, no network).
    Returns (exit_code, message, critical_findings, suppressed_findings)."""
    fingerprints = fingerprints or []
    reviewed = [r for r in results if not r.get("error") and not r.get("skipped")]
    errored = [r for r in results if r.get("error")]
    criticals, suppressed = [], []
    for r in results:
        for f in r.get("findings", []):
            if str(f.get("severity", "")).lower() != "critical":
                continue
            (suppressed if _is_dismissed(r["file"], f, fingerprints)
             else criticals).append((r["file"], f))
    if criticals:
        return 1, "BLOCK: unaddressed Critical finding(s)", criticals, suppressed
    if results and not reviewed:
        # Every file failed to review -> treat as an outage, fail OPEN.
        return 0, "FAIL-OPEN: DeepSeek unreachable for all files (" \
                  + str(len(errored)) + "); allowing push", [], suppressed
    return 0, "PASS: no Critical findings", [], suppressed


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

    fingerprints = load_dismissed_fingerprints(REPO / "Tickets")
    code, msg, criticals, suppressed = decide(results, fingerprints)
    for fpath, finding in suppressed:
        print(_ascii("  suppressed (previously triaged false positive)  " + fpath
                     + " :: " + str(finding.get("title", ""))))
    print(_ascii("[dev-review] " + msg))
    if criticals:
        for fpath, finding in criticals:
            print(_ascii("  CRITICAL  " + fpath + " :: " + str(finding.get("title", ""))))
        # File tickets ONLY for the non-suppressed blockers (TICKET-0183).
        blocked_titles = {(f_path, str(f.get("title", ""))) for f_path, f in criticals}
        ticket_results = [dict(r, findings=[f for f in r.get("findings", [])
                                            if (r["file"], str(f.get("title", ""))) in blocked_titles
                                            or str(f.get("severity", "")).lower() != "critical"])
                          for r in results]
        try:
            created = dev_review.create_tickets(ticket_results, min_severity="critical")
            print(_ascii("[dev-review] filed " + str(len(created)) + " ticket(s) for the blockers."))
        except Exception as e:
            print(_ascii("[dev-review] (could not file tickets: " + str(e)[:100] + ")"))
        print("[dev-review] push BLOCKED. Address the Critical finding(s), or bypass with "
              "`git push --no-verify` / SKIP_DEEPSEEK_REVIEW=1.")
    return code


if __name__ == "__main__":
    sys.exit(main())
