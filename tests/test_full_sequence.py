#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Dry walk of the FULL canonical sequence (generative/analysis stubbed) over the
reference HTML, with an approving operator. Verifies the whole G4 chain wires
together end-to-end: pre-check -> Phase 1 -> Phase 2 -> Steps 1..13 -> Phase 4
approval -> Phase 5 G2 cert -> Phase 6. No LLM.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import config, sequencer  # noqa: E402
from orchestrator.operator import Operator  # noqa: E402
from orchestrator.state import RunState  # noqa: E402


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


FAILS = []


def check(name, cond, detail=""):
    print(_ascii(("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail)))
    if not cond:
        FAILS.append(name)


def main():
    html = Path(config.resolve_doc("reference_prefold")).read_text(encoding="utf-8", errors="ignore")
    state = RunState.create(html, run_id="test_full")
    # operator that approves the Phase 4 gate (simulated 'y')
    op = Operator(auto=False, input_fn=lambda *_a: "y")
    sctx = sequencer.StepContext(state=state, context={}, operator=op,
                                 mode="auto", dry_generative=True)

    seq = sequencer.build_full_sequence()
    print(_ascii("sequence length: " + str(len(seq)) + " nodes"))
    result = sequencer.run_sequence(seq, sctx)

    print()
    check("run_done", result.get("status") == "DONE", result)
    # every node confirmed complete in durable state (G4)
    incomplete = [node.id for node in seq if not state.node_complete(node.id)]
    check("all_nodes_complete", not incomplete, "incomplete=" + str(incomplete))
    check("phase4_complete", state.node_complete("phase4_gate"))
    check("phase5_complete", state.node_complete("phase5_cert"))
    check("phase6_complete", state.node_complete("phase6_deliverables"))
    check("cert_artifact", state.has_artifact("phase5_certification"))

    print()
    if FAILS:
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    print("FULL-SEQUENCE DRY WALK PASSED")


if __name__ == "__main__":
    main()
