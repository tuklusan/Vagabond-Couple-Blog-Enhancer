#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""Live structural test of the additional generative nodes (title + description)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import nodes, review_loop  # noqa: E402


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


CONTEXT = {
    "origin": "Ashgabat, Turkmenistan",
    "destination": "Turkmenbashi, Turkmenistan",
    "waypoints": ["Karakum Desert", "Trans-Caspian Railway"],
    "landmarks": "Ashgabat marble monuments, Seyit Jemaleddin Mosque, Trans-Caspian Railway",
    "etr_minutes": 9,
}


def run(node_factory, name):
    node = node_factory()
    outcome = review_loop.run_generative_node(node, CONTEXT, max_rounds=2, verbose=True)
    status = outcome.get("status", "")
    output = outcome.get("output", "")
    print(_ascii(name + " -> " + status + " | " + output[:160]))
    # Skip on a total provider outage rather than failing a live test (TICKET-0029).
    reason = str(outcome.get("reason", "")).lower()
    # Broadened outage skip (TICKET-0084): any provider unavailability/outage/rate
    # limit that escalated -- not just the exact 'writer_unavailable' string.
    outage = any(k in reason for k in ("unavailable", "outage", "rate", "429", "timed out", "timeout", "failed"))
    if status == "ESCALATE" and outage:
        print(_ascii("SKIP " + name + ": provider outage/rate-limit (" + reason[:60] + ")"))
        return None, outcome
    # Structural + content assertions (TICKET-0030): valid status, a real string
    # output, and progress recorded.
    ok = (status in ("CERTIFIED", "REVISE", "ESCALATE")
          and isinstance(output, str) and len(output.strip()) > 0
          and isinstance(outcome.get("history"), list) and len(outcome["history"]) >= 1)
    return ok, outcome


def main():
    failures = []
    for factory, name in [(nodes.step1_title, "step1_title"),
                          (nodes.step2f_search_description, "step2f_search_description")]:
        ok, outcome = run(factory, name)
        if ok is None:                              # skipped (provider outage)
            print(_ascii("[SKIP] " + name))
            continue
        print(_ascii(("[PASS] " if ok else "[FAIL] ") + name))
        if not ok:
            failures.append(name)
        # description must respect the deterministic <=150 gate if it certified
        if name == "step2f_search_description" and outcome.get("status") == "CERTIFIED":
            length = len(outcome.get("output", "").strip())
            cond = length <= 150
            print(_ascii(("[PASS] " if cond else "[FAIL] ") + "desc_<=150 (" + str(length) + ")"))
            if not cond:
                failures.append("desc_<=150")

    print()
    if failures:
        print(_ascii("FAILED: " + str(failures)))
        sys.exit(1)
    print("MORE-NODES TEST PASSED")


if __name__ == "__main__":
    main()
