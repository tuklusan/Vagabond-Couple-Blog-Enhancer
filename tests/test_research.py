#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Tests for the research-augmented separator pipeline (TICKET-0208). Network and
VLM are mocked -- the live smoke happens in real runs.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import nodes, research_client, sequencer  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print((("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail))
          .encode("ascii", "replace").decode("ascii"))
    if not cond:
        FAILS.append(name)


def test_abstract_reconstruction():
    inv = {"Incas": [1], "The": [0], "built": [2], "terraces.": [3]}
    check("abstract_rebuilt",
          research_client._reconstruct_abstract(inv) == "The Incas built terraces.")
    check("abstract_empty_safe", research_client._reconstruct_abstract(None) == "")


def test_format_evidence():
    snips = [{"source": "Wikipedia", "title": "Ollantaytambo", "year": None,
              "url": "https://en.wikipedia.org/wiki/Ollantaytambo", "snippet": "A town in Peru."},
             {"source": "OpenAlex (academic)", "title": "Inca Architecture", "year": 1996,
              "url": "https://doi.org/10.x", "snippet": "How the Incas built."}]
    ev = research_client.format_evidence(snips)
    check("evidence_numbered", ev.startswith("[1] (Wikipedia: Ollantaytambo)"))
    check("evidence_year", "[2] (OpenAlex (academic) 1996: Inca Architecture)" in ev)
    check("evidence_urls", "<https://doi.org/10.x>" in ev)
    check("evidence_empty", research_client.format_evidence([]) == "")


def test_research_merges_and_dedupes():
    orig_w, orig_o = research_client.wikipedia_snippets, research_client.openalex_snippets
    research_client.wikipedia_snippets = lambda q, limit=1: [
        {"source": "Wikipedia", "title": "Same Title", "year": None, "url": "u1", "snippet": "s1"}]
    research_client.openalex_snippets = lambda q, limit=1: [
        {"source": "OpenAlex (academic)", "title": "same title", "year": 2000, "url": "u2", "snippet": "s2"}]
    try:
        out = research_client.research(["q1", "q2", ""])
    finally:
        research_client.wikipedia_snippets, research_client.openalex_snippets = orig_w, orig_o
    check("research_dedup_by_title", len(out) == 1, out)


def test_writer_reviewer_evidence_modes():
    spec = nodes.step13_separator()
    ev = "[1] (Wikipedia: X) Fact one. <u>"
    ctx = {"subject": "a / b", "evidence": ev, "visible": "Two llamas.",
           "trip_timeframe": "December 2022", "existing_facts": ""}
    sw, uw = spec.build_writer_prompt(ctx, "", "")
    sr, ur = spec.build_review_prompt("<p>x</p>", [], ctx)
    check("writer_confined_to_snippets", "MUST be directly supported" in sw and ev in uw)
    check("writer_gets_visible", "Two llamas." in uw)
    check("reviewer_entailment", "EVIDENCE ENTAILMENT" in sr and ev in ur)
    check("reviewer_temporal", "TEMPORAL VALIDITY" in sr)
    sw2, _ = spec.build_writer_prompt({"subject": "x"}, "", "")
    sr2, _ = spec.build_review_prompt("<p>x</p>", [], {"subject": "x"})
    check("no_evidence_falls_back", "guidebook" in sw2 and "web_search" in sr2)


class _FakeState:
    def __init__(self, html):
        self._html = html
    def get_working_html(self):
        return self._html
    def log_ai_call(self, *a, **kw):
        pass


def test_pair_items_enriched():
    """_image_pair_items attaches evidence (mock research) and, with vision
    opted in, visible subjects (mock VLM)."""
    import os
    html = ("<html><body><!--more-->"
            '<table class="tr-caption-container"><tbody><tr><td>'
            '<img src="https://x/img/s640/a.jpg"/></td></tr>'
            '<tr><td class="tr-caption">Pisac terraces</td></tr></tbody></table>'
            '<table class="tr-caption-container"><tbody><tr><td>'
            '<img src="https://x/img/s640/b.jpg"/></td></tr>'
            '<tr><td class="tr-caption">Pisac market</td></tr></tbody></table>'
            "</body></html>")
    sctx = sequencer.StepContext(state=_FakeState(html),
                                 context={"destination": "Cusco, Peru"},
                                 operator=None)
    from orchestrator import research_client as rc, vision_client as vc
    orig_res = rc.research
    rc.research = lambda queries, **kw: [
        {"source": "Wikipedia", "title": "Pisac", "year": None, "url": "u",
         "snippet": "Pisac is a village in the Sacred Valley."}] if queries else []
    orig_fetch, orig_pair = vc.fetch_image, vc.inspect_image_pair
    vc.fetch_image = lambda src: (b"\xff\xd8x", "image/jpeg")
    vc.inspect_image_pair = lambda images, prompt, **kw: (
        {"subjects": ["Pisac terraces"], "visible": "Terraces; a market."}, "raw", "mock")
    os.environ["ORCH_STEP13_VISION"] = "1"
    try:
        items = sequencer._image_pair_items(sctx)
    finally:
        del os.environ["ORCH_STEP13_VISION"]
        rc.research = orig_res
        vc.fetch_image, vc.inspect_image_pair = orig_fetch, orig_pair
    check("pair_items_found", len(items) == 1, len(items))
    it = items[0]
    check("pair_srcs_attached", it.get("pair_srcs") == ["https://x/img/s640/a.jpg",
                                                        "https://x/img/s640/b.jpg"])
    check("pair_evidence_attached", "Pisac is a village" in it.get("evidence", ""), it.get("evidence"))
    check("pair_visible_attached", it.get("visible") == "Terraces; a market.")


def main():
    test_abstract_reconstruction()
    test_format_evidence()
    test_research_merges_and_dedupes()
    test_writer_reviewer_evidence_modes()
    test_pair_items_enriched()
    print()
    if FAILS:
        print("FAILED: " + str(FAILS))
        sys.exit(1)
    print("RESEARCH TESTS PASSED")


if __name__ == "__main__":
    main()
