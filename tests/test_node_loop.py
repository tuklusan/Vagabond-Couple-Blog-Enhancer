#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Live integration test of the Tier-1 writer<->reviewer loop on the Step 6 node.

Uses the real writer (OpenRouter free) and reviewer (Claude -> DeepSeek fallback;
DeepSeek today, since the Anthropic key is unfunded). Asserts only structural
invariants -- not the model's judgment -- so it is not flaky on model variance.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import nodes, review_loop  # noqa: E402


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


def main():
    context = {
        "origin": "Ashgabat, Turkmenistan",
        "destination": "Turkmenbashi, Turkmenistan",
        "waypoints": ["Karakum Desert"],
        "method": "overnight Trans-Caspian Railway sleeper train",
        "covers": "the marble capital, two Silk Road mosques, and the overnight train to the Caspian",
    }
    node = nodes.step6_first_body_paragraph()
    outcome = review_loop.run_generative_node(node, context, max_rounds=3, verbose=True)

    status = outcome.get("status", "")
    output = outcome.get("output", "")          # safe access (TICKET-0033)
    history = outcome.get("history", [])
    print()
    print(_ascii("status : " + status))
    print(_ascii("rounds : " + str(outcome.get("rounds"))))
    print(_ascii("output : " + output[:300]))
    print(_ascii("sources: " + str(outcome.get("sources"))[:200]))

    # Live test: if every writer provider was unavailable, skip rather than fail on
    # an external outage (TICKET-0029).
    if status == "ESCALATE" and "writer_unavailable" in str(outcome.get("reason", "")):
        print(_ascii("SKIP: writer providers unavailable -- " + str(outcome.get("reason"))))
        return

    failures = []

    def check(name, cond, detail=""):
        print(_ascii(("[PASS] " if cond else "[FAIL] ") + name + " " + detail))
        if not cond:
            failures.append(name)

    # Structural invariants only -- not model wording, which varies (TICKET-0031).
    check("status_valid", status in ("CERTIFIED", "REVISE", "ESCALATE"), status)
    check("output_nonempty", len(output.strip()) > 0)
    check("output_is_paragraph", "<p" in output.lower(), output[:80])
    check("history_recorded", isinstance(history, list) and len(history) >= 1)
    # A produced (non-escalated) result must carry a verdict with a decision; on an
    # ESCALATE the verdict may legitimately be empty (TICKET-0032).
    if status in ("CERTIFIED", "REVISE"):
        v = outcome.get("verdict")
        check("verdict_has_decision", isinstance(v, dict) and "decision" in v, str(v)[:80])

    print()
    if failures:
        print(_ascii("FAILED: " + str(failures)))
        sys.exit(1)
    print("NODE LOOP TEST PASSED (status=" + outcome["status"] + ")")


if __name__ == "__main__":
    main()
