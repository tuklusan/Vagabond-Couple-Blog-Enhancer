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
    try:
        outcome = review_loop.run_generative_node(node, context, max_rounds=3, verbose=True)
    except Exception as e:
        # A raw exception from the live call is a clean failure, not a traceback
        # (TICKET-0086). run_generative_node normally escalates rather than raising.
        print(_ascii("[FAIL] node_loop raised: " + str(e)[:160]))
        sys.exit(1)

    status = outcome.get("status", "")
    output = outcome.get("output") or ""        # None-safe (TICKET-0033/0097)
    history = outcome.get("history", [])
    print()
    print(_ascii("status : " + status))
    print(_ascii("rounds : " + str(outcome.get("rounds"))))
    print(_ascii("output : " + output[:300]))
    print(_ascii("sources: " + str(outcome.get("sources"))[:200]))

    # Live test: skip on any external provider outage/rate-limit that escalated --
    # not just the exact 'writer_unavailable' string (TICKET-0029/0087).
    reason = str(outcome.get("reason", "")).lower()
    # Specific outage/rate-limit markers only -- NOT generic 'failed'/'error', which
    # could mask a real bug (TICKET-0096).
    if status == "ESCALATE" and any(k in reason for k in
                                    ("unavailable", "outage", "rate", "429", "timeout", "timed out")):
        print(_ascii("SKIP: external provider outage/rate-limit -- " + reason[:80]))
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
