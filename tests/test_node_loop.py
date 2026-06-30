#!/usr/bin/env python3
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

    print()
    print(_ascii("status : " + outcome["status"]))
    print(_ascii("rounds : " + str(outcome["rounds"])))
    print(_ascii("output : " + outcome["output"][:300]))
    print(_ascii("sources: " + str(outcome.get("sources"))[:200]))

    failures = []

    def check(name, cond, detail=""):
        print(_ascii(("[PASS] " if cond else "[FAIL] ") + name + " " + detail))
        if not cond:
            failures.append(name)

    check("status_valid", outcome["status"] in ("CERTIFIED", "REVISE", "ESCALATE"), outcome["status"])
    check("output_nonempty", len(outcome["output"].strip()) > 0)
    check("history_recorded", isinstance(outcome["history"], list) and len(outcome["history"]) >= 1)
    # route-first: origin & destination should appear in the produced paragraph
    low = outcome["output"].lower()
    check("mentions_origin", "ashgabat" in low)
    check("mentions_destination", "turkmenbashi" in low)
    # a verdict object was produced by the reviewer on at least one round
    check("verdict_has_decision", isinstance(outcome.get("verdict"), dict)
          and "decision" in outcome.get("verdict", {}))

    print()
    if failures:
        print(_ascii("FAILED: " + str(failures)))
        sys.exit(1)
    print("NODE LOOP TEST PASSED (status=" + outcome["status"] + ")")


if __name__ == "__main__":
    main()
