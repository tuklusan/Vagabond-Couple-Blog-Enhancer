#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Dry tests for the G4 sequencer -- no LLM. Verifies the step-entry gate, artifact
persistence, the Phase 4 approval gate (block + pass), all on the reference HTML.
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


def _src_html():
    ref = config.resolve_doc("reference_prefold")
    return Path(ref).read_text(encoding="utf-8", errors="ignore")


FAILS = []


def check(name, cond, detail=""):
    print(_ascii(("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail)))
    if not cond:
        FAILS.append(name)


def test_gate_blocks_at_phase4():
    state = RunState.create(_src_html(), run_id="test_block")
    op = Operator(auto=True)  # auto withholds Phase 4 approval (safe default)
    sctx = sequencer.StepContext(state=state, context={}, operator=op, mode="auto")
    result = sequencer.run_sequence(sequencer.build_phase1_deterministic_sequence(), sctx)
    check("phase4_halts_when_withheld", result["status"] == "HALT" and result["at"] == "phase4_gate", result)
    # deterministic passes before the gate completed + artifacts saved
    check("1C_artifact_saved", state.has_artifact("1C_media_inventory"))
    check("schema_artifact_saved", state.has_artifact("schema_check"))
    check("det_nodes_complete", state.node_complete("1C_media_inventory") and state.node_complete("schema_check"))


def test_gate_passes_when_approved():
    state = RunState.create(_src_html(), run_id="test_approve")
    op = Operator(auto=False, input_fn=lambda *_a: "y")  # simulate operator approving
    sctx = sequencer.StepContext(state=state, context={}, operator=op, mode="step")
    result = sequencer.run_sequence(sequencer.build_phase1_deterministic_sequence(), sctx)
    check("run_done_when_approved", result["status"] == "DONE", result)
    check("phase4_complete", state.node_complete("phase4_gate"))


def test_g4_step_entry_gate():
    state = RunState.create(_src_html(), run_id="test_g4")
    op = Operator(auto=True)
    sctx = sequencer.StepContext(state=state, context={}, operator=op, mode="auto")

    def incomplete_handler(_sctx):
        return {"complete": False, "note": "intentionally incomplete"}

    def should_not_run(_sctx):
        return {"complete": True, "note": "SHOULD NOT REACH"}

    nodes = [
        sequencer.SeqNode("nodeA", "test - A (incomplete)", "deterministic", incomplete_handler),
        sequencer.SeqNode("nodeB", "test - B (blocked)", "deterministic", should_not_run),
    ]
    result = sequencer.run_sequence(nodes, sctx)
    check("g4_blocks_nodeB", result["status"] == "HALT" and result["at"] == "nodeB", result)
    check("nodeB_never_completed", not state.node_complete("nodeB"))


def main():
    test_gate_blocks_at_phase4()
    test_gate_passes_when_approved()
    test_g4_step_entry_gate()
    print()
    if FAILS:
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    print("SEQUENCER TESTS PASSED")


if __name__ == "__main__":
    main()
