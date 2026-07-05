#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Tests for the push gate's pure decision logic + false-positive fingerprint
memory (TICKET-0183). No network, no DeepSeek.
"""
import importlib.util
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "_review_gate", REPO_ROOT / ".githooks" / "_review_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

FAILS = []


def check(name, cond, detail=""):
    print((("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail))
          .encode("ascii", "replace").decode("ascii"))
    if not cond:
        FAILS.append(name)


CRIT = {"severity": "Critical", "title": "Null input crash in assemble()",
        "detail": "x", "suggestion": "y"}


def test_critical_blocks():
    code, msg, crits, sup = gate.decide(
        [{"file": "orchestrator/assembler.py", "findings": [CRIT]}])
    check("critical_blocks", code == 1 and len(crits) == 1 and not sup, (code, msg))


def test_fingerprinted_critical_suppressed():
    fps = [("assembler.py", gate._title_tokens("Null input crash in assemble()"))]
    code, msg, crits, sup = gate.decide(
        [{"file": "orchestrator/assembler.py", "findings": [CRIT]}], fps)
    check("fingerprinted_suppressed", code == 0 and not crits and len(sup) == 1, (code, msg))
    # different file, same title -> NOT suppressed
    code2, _m, crits2, _s = gate.decide(
        [{"file": "orchestrator/sequencer.py", "findings": [CRIT]}], fps)
    check("other_file_not_suppressed", code2 == 1 and len(crits2) == 1)
    # same file, unrelated title -> NOT suppressed
    other = dict(CRIT, title="SQL injection in build_query parameters")
    code3, _m, crits3, _s = gate.decide(
        [{"file": "orchestrator/assembler.py", "findings": [other]}], fps)
    check("different_title_not_suppressed", code3 == 1 and len(crits3) == 1)


def test_fail_open_on_total_outage():
    code, msg, crits, sup = gate.decide(
        [{"file": "a.py", "findings": [], "error": "boom"}])
    check("fail_open_outage", code == 0 and "FAIL-OPEN" in msg, msg)


def test_load_fingerprints_from_tickets():
    with tempfile.TemporaryDirectory() as td:
        # false positive -> contributes
        (Path(td) / "TICKET-9001.md").write_text(
            "# TICKET-9001: [assembler.py] Null input crash in assemble()\n"
            "Status: Closed\nNotes: FALSE POSITIVE, NO ACTION. justified.\n",
            encoding="utf-8")
        # genuinely fixed -> must NOT contribute
        (Path(td) / "TICKET-9002.md").write_text(
            "# TICKET-9002: [sequencer.py] Real bug that was fixed\n"
            "Status: Closed\nNotes: VALID, FIXED with a guard.\n", encoding="utf-8")
        # still open -> must NOT contribute
        (Path(td) / "TICKET-9003.md").write_text(
            "# TICKET-9003: [nodes.py] Open false alarm\n"
            "Status: Open\nNotes: FALSE POSITIVE maybe\n", encoding="utf-8")
        fps = gate.load_dismissed_fingerprints(td)
    check("fingerprints_loaded", len(fps) == 1 and fps[0][0] == "assembler.py", fps)


def main():
    test_critical_blocks()
    test_fingerprinted_critical_suppressed()
    test_fail_open_on_total_outage()
    test_load_fingerprints_from_tickets()
    print()
    if FAILS:
        print("FAILED: " + str(FAILS))
        sys.exit(1)
    print("REVIEW-GATE TESTS PASSED")


if __name__ == "__main__":
    main()
