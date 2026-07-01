#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
The G4 state machine.

Drives nodes in the canonical order, enforcing Rule G4 (no node may begin until
the prior node is confirmed complete in durable state -- survives restarts),
emitting Rule G1 single-line indicators, and halting in the G1 format
(reason / offending item / action) on any gap. Deterministic nodes run
validators; generative nodes run the Tier-1 loop; operator nodes pause for the
human (Phase 4 approval gate blocks HTML generation).
"""
from dataclasses import dataclass
from typing import Callable

from . import config, validators, review_loop, assembler, context_extractor, nodes as node_specs


@dataclass
class SeqNode:
    id: str
    phase: str          # G1 indicator label, e.g. "Phase 1 / 1C - Media inventory"
    kind: str           # precheck | deterministic | generative | analysis | operator
    handler: Callable    # (StepContext) -> result dict


@dataclass
class StepContext:
    state: object
    context: dict
    operator: object
    mode: str = "auto"            # auto | step | run-to-gate
    dry_generative: bool = False   # stub generative/analysis nodes (test the machinery)
    approve_gates: bool = False    # auto-operator: grant Phase 4 approval (test/CI opt-in only)


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


def emit_indicator(phase):
    print(_ascii(">> " + phase))


def _halt(sctx, node, reason, item, action):
    line = ("HALT -- " + reason + " -- Offending item: " + str(item)
            + ". Action required: " + str(action))
    print(_ascii("[X] " + line))
    sctx.state.log("halt", {"node": node.id, "reason": reason, "item": item, "action": action})
    sctx.state.mark_node(node.id, complete=False, gates_ok=False, note=line)
    return {"status": "HALT", "at": node.id, "reason": reason, "item": item, "action": action}


def run_sequence(nodes, sctx):
    """Run an ordered list of SeqNodes with the G4 step-entry gate."""
    prev_id = None
    for node in nodes:
        # --- G4 step-entry gate ---
        if prev_id is not None and not sctx.state.node_complete(prev_id):
            return _halt(sctx, node, "step-entry gate: prior step incomplete",
                         prev_id, "complete " + prev_id + " before " + node.id)
        sctx.state.set_current_node(node.id)
        emit_indicator(node.phase)
        try:
            result = node.handler(sctx) or {}
        except Exception as e:
            return _halt(sctx, node, "handler error", str(e)[:160], "investigate " + node.id)

        if result.get("halt"):
            return _halt(sctx, node, result.get("halt_reason", "halt"),
                         result.get("item", ""), result.get("action", ""))

        sctx.state.mark_node(node.id, complete=result.get("complete", True),
                             output_ref=result.get("output_ref"), note=result.get("note", ""))
        sctx.state.log("node_done", {"node": node.id, "status": result.get("status", "ok"),
                                     "note": result.get("note", "")})
        if result.get("note"):
            print(_ascii("   " + result["note"]))
        prev_id = node.id
        if result.get("stop_after"):
            return {"status": "STOPPED", "at": node.id, "note": result.get("note", "")}
        # step-through UX: pause after each node unless auto. (run-to-gate only
        # pauses at operator nodes, which prompt inside their own handler.)
        if sctx.mode == "step" and node is not nodes_list_last(nodes):
            if not sctx.operator.confirm("Continue past " + node.id + "?", default=True):
                return {"status": "PAUSED", "at": node.id}
    return {"status": "DONE", "last": prev_id}


def nodes_list_last(nodes):
    return nodes[-1] if nodes else None


# ===========================================================================
# Handlers
# ===========================================================================
def _summarize(node_id, result):
    if "photographs" in result:
        return (f"photos={result['photographs']} tables={result['caption_tables']} "
                f"match={result['image_table_match']} "
                f"int_links={len(result['internal_links'])} ext_links={len(result['external_links'])}")
    if "ufffd_count" in result:
        return f"suspect={result['suspect']} ufffd={result['ufffd_count']}"
    if "data_rows" in result:
        return f"summary_present={result['present']} rows={result['data_rows']}"
    if "canonical_after_script" in result:
        return f"more_count={result['count']} canonical_after_script={result['canonical_after_script']}"
    if "type_is_travelaction" in result:
        return (f"schema valid={result.get('valid_json')} travelaction={result.get('type_is_travelaction')} "
                f"author_ok={result.get('author_ok')}")
    return "ok"


def precheck_node():
    def handler(sctx):
        missing = config.missing_docs()
        if missing:
            return {"halt": True, "halt_reason": "Required project document(s) missing",
                    "item": ", ".join(missing),
                    "action": "add the missing document(s) under ORCH_DOCS_DIR"}
        return {"complete": True, "note": "all 6 required project documents present"}
    return SeqNode("precheck", "Pre-check - Required Project Documents", "precheck", handler)


def deterministic_node(node_id, phase, fn, artifact=None):
    def handler(sctx):
        html = sctx.state.get_working_html()
        result = fn(html)
        ref = sctx.state.save_artifact(artifact or node_id, result)
        return {"complete": True, "output_ref": ref, "status": "ok",
                "note": _summarize(node_id, result)}
    return SeqNode(node_id, phase, "deterministic", handler)


def build_phase4_summary(state):
    parts = []
    inv = state.read_artifact("1C_media_inventory")
    if inv:
        parts.append("Media & Links (1C): " + str(inv["photographs"]) + " photos / "
                     + str(inv["caption_tables"]) + " caption tables (match="
                     + str(inv["image_table_match"]) + "); internal links "
                     + str(len(inv["internal_links"])) + ", external "
                     + str(len(inv["external_links"])) + ", youtube "
                     + str(len(inv["youtube_embeds"])) + ", maps " + str(len(inv["map_embeds"])))
    sch = state.read_artifact("schema_check")
    if sch:
        parts.append("Schema (Step 4): valid_json=" + str(sch.get("valid_json"))
                     + " TravelAction=" + str(sch.get("type_is_travelaction"))
                     + " author_ok=" + str(sch.get("author_ok")))
    sb = state.read_artifact("1F_summary_block")
    if sb:
        parts.append("Summary block (1F): present=" + str(sb["present"]) + " rows=" + str(sb["data_rows"]))
    more = state.read_artifact("step5_more")
    if more:
        parts.append("<!--more--> (Step 5): count=" + str(more["count"])
                     + " canonical_after_script=" + str(more["canonical_after_script"]))
    qm = state.read_artifact("1G_encoding")
    if qm:
        parts.append("Encoding (1G): suspect=" + str(qm["suspect"]) + " ufffd=" + str(qm["ufffd_count"]))
    return "\n".join(parts) if parts else "(no analysis artifacts available)"


def phase4_gate_node():
    def handler(sctx):
        summary = build_phase4_summary(sctx.state)
        approved = sctx.operator.approve("Phase 4 - Proposed Modifications", summary,
                                         default=sctx.approve_gates)
        if not approved:
            return {"halt": True, "halt_reason": "Phase 4 approval withheld",
                    "item": "operator did not approve HTML generation",
                    "action": "review the summary and re-run after approval"}
        return {"complete": True, "note": "operator approved -> HTML generation unlocked"}
    return SeqNode("phase4_gate", "Phase 4 - Approval gate (blocks HTML generation)", "operator", handler)


def build_phase1_deterministic_sequence():
    """Pre-check + the read-only deterministic Phase-1 passes + the Phase 4 gate.

    (The LLM-judgment passes -- 1A facts, 1B readability, 1H repetition, 1I writing
    rules -- and the generative Phase 3 nodes plug in here once providers are live.)
    """
    return [
        precheck_node(),
        deterministic_node("1C_media_inventory", "Phase 1 / 1C - Media & links inventory",
                           validators.media_inventory),
        deterministic_node("1F_summary_block", "Phase 1 / 1F - Summary block audit",
                           validators.summary_block),
        deterministic_node("1G_encoding", "Phase 1 / 1G - Character-encoding audit",
                           validators.scan_question_marks),
        deterministic_node("step5_more", "Phase 3 / Step 5 - <!--more--> placement",
                           validators.count_more_tags),
        deterministic_node("schema_check", "Phase 3 / Step 4 - ld+json TravelAction validity",
                           validators.validate_ld_json),
        phase4_gate_node(),
    ]


# ===========================================================================
# Generative / analysis / phase nodes for the FULL canonical sequence
# ===========================================================================
def generative_node(node_id, phase, spec_factory, optional=False):
    """A Tier-1 writer<->reviewer generative node.

    optional=True marks a node the workflow explicitly allows to be skipped when no
    verifiable, non-duplicative content can be produced (rev-18 Step 9-F factoids;
    Step 13 separators): on escalation it SKIPS (adds nothing, records the reason)
    instead of halting the run. Non-optional nodes still stop for an operator call.
    """
    def handler(sctx):
        if sctx.dry_generative:
            return {"complete": True, "note": "[dry] generative stubbed"}
        spec = spec_factory()
        outcome = review_loop.run_generative_node(spec, sctx.context)
        certified = outcome["status"] == "CERTIFIED"
        sctx.state.save_artifact("gen_" + node_id, {
            # A skipped optional node must contribute no body content.
            "status": outcome["status"],
            "output": outcome["output"] if certified else "",
            "verdict": outcome.get("verdict"), "sources": outcome.get("sources"),
            "rounds": outcome.get("rounds"),
            "skipped": (not certified) and optional,
        })
        if certified:
            return {"complete": True, "output_ref": "gen_" + node_id,
                    "note": "certified in " + str(outcome.get("rounds")) + " round(s)"}
        if optional:
            # Workflow-sanctioned skip (e.g. no verifiable factoid for this pass).
            sctx.operator.info("Node " + node_id + " skipped (optional): "
                               + str(outcome.get("reason", "")))
            return {"complete": True, "output_ref": "gen_" + node_id,
                    "note": "skipped (optional): " + str(outcome.get("reason", ""))}
        # ESCALATE -> operator decision (never silently accept an unverified claim)
        sctx.operator.info("Node " + node_id + " ESCALATED: " + str(outcome.get("reason", "")))
        choice = sctx.operator.choose("How to handle " + node_id + "?",
                                      ["accept output as-is", "abort run"], default_index=1)
        if choice.startswith("accept"):
            return {"complete": True, "output_ref": "gen_" + node_id,
                    "note": "operator accepted escalated output"}
        return {"halt": True, "halt_reason": "operator aborted escalated node",
                "item": node_id, "action": "resolve " + node_id + " and re-run"}
    return SeqNode(node_id, phase, "generative", handler)


def analysis_node(node_id, phase):
    """LLM-judgment Phase-1 pass (1A/1B/1H/1I). Stubbed in dry mode; the live
    reviewer-based implementation plugs in here. The per-node Tier-1 loops and
    the Phase 5 G2 pass already enforce facts/rules/repetition on produced text."""
    def handler(sctx):
        if sctx.dry_generative:
            return {"complete": True, "note": "[dry] analysis stubbed"}
        sctx.state.save_artifact("analysis_" + node_id, {"status": "live_impl_pending"})
        return {"complete": True, "note": "analysis recorded (live reviewer pass pending)"}
    return SeqNode(node_id, phase, "analysis", handler)


def context_extraction_node():
    """Derive the generative context (route, sections, stops, landmarks) from the
    source post -- deterministically, from its existing schema + structure."""
    def handler(sctx):
        ctx = context_extractor.extract_context(sctx.state.get_working_html(),
                                                allow_llm=not sctx.dry_generative)
        sctx.state.save_artifact("context", ctx)
        sctx.context.update(ctx)
        return {"complete": True,
                "note": "context: '" + (ctx.get("origin") or "?") + "' -> '"
                        + (ctx.get("destination") or "?") + "', "
                        + str(len(ctx.get("sections") or [])) + " sections, "
                        + str(len(ctx.get("stops") or [])) + " stops"}
    return SeqNode("context_extraction", "Setup - Source context extraction", "deterministic", handler)


def phase2_url_lock_node():
    def handler(sctx):
        return {"complete": True, "note": "URL stub frozen -- no slug change permitted"}
    return SeqNode("phase2_url_lock", "Phase 2 - URL stub lock", "deterministic", handler)


def phase5_generate_node():
    """Phase 5 HTML generation: assemble the certified fragments into working.html
    (and run the deterministic transforms: strip styles, reapply summary CSS,
    re-emit YouTube, remove ?m=1)."""
    def handler(sctx):
        html = sctx.state.get_working_html()
        mapping = {
            "gen_step3_summary_block": "summary_block",
            "gen_step6_first_body_paragraph": "first_paragraph",
            "gen_step7_route_summary_box": "route_box",
            "gen_step8_route_at_a_glance": "route_at_a_glance",
            "gen_step10_journey_significance": "journey_significance",
        }
        fragments = {}
        for art_key, frag_key in mapping.items():
            art = sctx.state.read_artifact(art_key)
            if art and art.get("status") == "CERTIFIED" and art.get("output"):
                fragments[frag_key] = art["output"]
        sep = sctx.state.read_artifact("gen_step13_separator")
        if sep and sep.get("status") == "CERTIFIED" and sep.get("output"):
            fragments["separators"] = [sep["output"]]
        assembled = assembler.assemble(html, fragments or None)
        sctx.state.set_working_html(assembled)
        return {"complete": True, "note": "assembled HTML (" + str(len(fragments)) + " fragments spliced)"}
    return SeqNode("phase5_generate", "Phase 5 - HTML generation (assemble fragments)", "deterministic", handler)


def phase5_certification_node():
    def handler(sctx):
        cert = review_loop.run_document_certification(sctx.state, run_reviewer=not sctx.dry_generative)
        if not cert["certified"]:
            failed = cert["pass2_deterministic"]["failed"]
            if not failed:
                failed = [str((cert.get("pass1_reviewer") or {}).get("decision"))]
            return {"halt": True, "halt_reason": "Phase 5 G2 certification not clean",
                    "item": str(failed), "action": "fix the failing checks and re-run Phase 5"}
        return {"complete": True, "note": "G2 two-pass clean -> delivery permitted"}
    return SeqNode("phase5_cert", "Phase 5 - HTML sanity certification (G2 two-pass)", "analysis", handler)


def phase6_deliverables_node():
    def handler(sctx):
        sctx.operator.info("Phase 6 - Deliverables ready: (1) updated post body HTML, "
                           "(2) new SEO title, (3) <=150-char search description.")
        return {"complete": True, "note": "deliverables presented"}
    return SeqNode("phase6_deliverables", "Phase 6 - Deliverables", "operator", handler)


def build_full_sequence():
    """The complete rev-18 canonical node order (G4 line 82)."""
    g, a, d = generative_node, analysis_node, deterministic_node
    n = node_specs
    return [
        precheck_node(),
        context_extraction_node(),
        # Phase 1 -- scan & analyze (read-only)
        a("1A_facts", "Phase 1 / 1A - Fact & sanity check"),
        a("1B_readability", "Phase 1 / 1B - Human readability"),
        d("1C_media_inventory", "Phase 1 / 1C - Media & links inventory", validators.media_inventory),
        d("1G_encoding", "Phase 1 / 1G - Character-encoding audit", validators.scan_question_marks),
        d("1F_summary_block", "Phase 1 / 1F - Summary block audit", validators.summary_block),
        a("1H_repetition", "Phase 1 / 1H - Repetition scan"),
        a("1I_writing_rules", "Phase 1 / 1I - Writing-rules audit (existing prose)"),
        # Phase 2
        phase2_url_lock_node(),
        # Phase 3 -- pre-fold zone
        g("step1_title", "Phase 3 / Step 1 - SEO title", n.step1_title),
        g("step2f_search_description", "Phase 3 / Step 2-F - Search description", n.step2f_search_description),
        g("step3_summary_block", "Phase 3 / Step 3 - Summary block", n.step3_summary_block),
        d("schema_check", "Phase 3 / Step 4 - ld+json validity", validators.validate_ld_json),
        d("step5_more", "Phase 3 / Step 5 - <!--more--> placement", validators.count_more_tags),
        # Phase 3 -- body
        g("step6_first_body_paragraph", "Phase 3 / Step 6 - First body paragraph", n.step6_first_body_paragraph),
        g("step7_route_summary_box", "Phase 3 / Step 7 - Route summary box", n.step7_route_summary_box),
        g("step8_route_at_a_glance", "Phase 3 / Step 8 - Route at a Glance", n.step8_route_at_a_glance),
        g("step9f_factoid", "Phase 3 / Step 9-F - Section-closing factoids", n.step9f_factoid, optional=True),
        g("step10_journey_significance", "Phase 3 / Step 10 - Journey significance", n.step10_journey_significance),
        g("step12_resolve", "Phase 3 / Step 12 - Resolve repetition/rules", n.step12_resolve),
        g("step13_separator", "Phase 3 / Step 13 - Image separators", n.step13_separator, optional=True),
        # Phase 4 -- operator approval (blocks HTML generation)
        phase4_gate_node(),
        # Phase 5 -- HTML generation (assemble) then sanity cert (G2 two-pass;
        # Step 14 holistic read is Pass 1)
        phase5_generate_node(),
        phase5_certification_node(),
        # Phase 6 -- deliverables
        phase6_deliverables_node(),
    ]
