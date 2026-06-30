#!/usr/bin/env python3
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

from . import config, validators


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
    mode: str = "auto"   # auto | step | run-to-gate


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
    return {"status": "DONE", "last": prev_id}


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
        approved = sctx.operator.approve("Phase 4 - Proposed Modifications", summary, default=False)
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
