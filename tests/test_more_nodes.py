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
    print(_ascii(name + " -> " + outcome["status"] + " | " + outcome["output"][:160]))
    ok = (outcome["status"] in ("CERTIFIED", "REVISE", "ESCALATE")
          and len(outcome["output"].strip()) > 0
          and len(outcome["history"]) >= 1)
    return ok, outcome


def main():
    failures = []
    for factory, name in [(nodes.step1_title, "step1_title"),
                          (nodes.step2f_search_description, "step2f_search_description")]:
        ok, outcome = run(factory, name)
        print(_ascii(("[PASS] " if ok else "[FAIL] ") + name))
        if not ok:
            failures.append(name)
        # description must respect the deterministic <=150 gate if it certified
        if name == "step2f_search_description" and outcome["status"] == "CERTIFIED":
            length = len(outcome["output"].strip())
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
