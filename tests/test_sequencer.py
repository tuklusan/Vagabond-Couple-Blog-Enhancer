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

from orchestrator import config, sequencer, review_loop  # noqa: E402
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


def test_locate_flagged_passage_finds_best_match():
    html = (
        "<html><body><!--more-->"
        "<p>We arrived in Seward under grey skies and boarded our tour boat.</p>"
        "<h2>Denali</h2>"
        "<p>Yes, we took the photo. No, we can't control the weather.</p>"
        "<p>Yes, we took the photo. No, we can't control the weather.</p>"
        "</body></html>"
    )
    node = sequencer._locate_flagged_passage(
        html, "the caption Yes we took the photo No we cant control the weather repeats")
    check("locate_finds_repeated_passage", node is not None
          and "took the photo" in node.get_text())


def test_locate_flagged_passage_no_match_returns_none():
    html = "<html><body><!--more--><p>Completely unrelated content about kayaking.</p></body></html>"
    node = sequencer._locate_flagged_passage(html, "denali highway parks highway nostalgic backway")
    check("locate_no_match_none", node is None)


def test_remediate_flagged_passage_rewrites_and_preserves_hrefs():
    html = (
        "<html><body><!--more-->"
        '<p>We drove the Denali Highway, opened in 1957, see <a href="https://example.com/denali">details</a>.</p>'
        "</body></html>"
    )
    state = RunState.create(html, run_id="test_remediate_passage")
    sctx = sequencer.StepContext(state=state, context={"existing_facts": ""},
                                 operator=Operator(auto=True))
    pass1 = {"revision_instructions": "",
             "criteria": {"repetition": {"findings": [
                 "The Denali Highway / 1957 fact is restated verbatim elsewhere"]}}}

    def fake_run_generative_node(spec, ctx, state=None):
        check("remediate_receives_passage", "Denali Highway" in ctx.get("passage", ""))
        return {"status": "CERTIFIED",
                "output": '<p>We continued on, see <a href="https://example.com/denali">details</a>.</p>'}

    orig = review_loop.run_generative_node
    review_loop.run_generative_node = fake_run_generative_node
    try:
        fixed = sequencer._remediate_flagged_passage(sctx, pass1)
    finally:
        review_loop.run_generative_node = orig
    check("remediate_reports_fix", bool(fixed))
    new_html = state.get_working_html()
    check("remediate_applied_new_text", "We continued on" in new_html)
    check("remediate_preserved_href", 'href="https://example.com/denali"' in new_html)


def test_remediate_flagged_passage_rejects_dropped_href():
    html = (
        "<html><body><!--more-->"
        '<p>The Salmon Capital of the World claim appears here, see <a href="https://example.com/salmon">source</a>.</p>'
        "</body></html>"
    )
    state = RunState.create(html, run_id="test_remediate_drop_href")
    sctx = sequencer.StepContext(state=state, context={"existing_facts": ""},
                                 operator=Operator(auto=True))
    pass1 = {"revision_instructions": "Salmon Capital of the World repeats",
             "criteria": {"repetition": {"findings": ["Salmon Capital of the World repeats"]}}}

    def fake_run_generative_node(spec, ctx, state=None):
        return {"status": "CERTIFIED", "output": "<p>The claim appears here, no link now.</p>"}

    orig = review_loop.run_generative_node
    review_loop.run_generative_node = fake_run_generative_node
    try:
        fixed = sequencer._remediate_flagged_passage(sctx, pass1)
    finally:
        review_loop.run_generative_node = orig
    check("remediate_rejects_href_drop", fixed is None)
    check("remediate_left_original_intact", "example.com/salmon" in state.get_working_html())


def main():
    test_gate_blocks_at_phase4()
    test_gate_passes_when_approved()
    test_g4_step_entry_gate()
    test_locate_flagged_passage_finds_best_match()
    test_locate_flagged_passage_no_match_returns_none()
    test_remediate_flagged_passage_rewrites_and_preserves_hrefs()
    test_remediate_flagged_passage_rejects_dropped_href()
    print()
    if FAILS:
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    print("SEQUENCER TESTS PASSED")


if __name__ == "__main__":
    main()
