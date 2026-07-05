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
import json
import os
import re
from dataclasses import dataclass
from typing import Callable

from . import config, validators, review_loop, assembler, context_extractor, nodes as node_specs

# How many times a Pass-1 REVISE may bounce (drop the flagged factoid + reassemble
# + re-certify) before halting for the operator (TICKET-0123).
try:
    MAX_PASS1_BOUNCES = int(os.environ.get("ORCH_MAX_PASS1_BOUNCES", "3"))
except ValueError:
    MAX_PASS1_BOUNCES = 3


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
    # Best-effort durable record of the halt; never let a state-write failure mask
    # the halt itself (TICKET-0120).
    try:
        sctx.state.log("halt", {"node": node.id, "reason": reason, "item": item, "action": action})
        sctx.state.mark_node(node.id, complete=False, gates_ok=False, note=line)
    except Exception as e:
        print(_ascii("   (warning: could not persist halt state: " + str(e)[:120] + ")"))
    return {"status": "HALT", "at": node.id, "reason": reason, "item": item, "action": action}


def run_sequence(nodes, sctx):
    """Run an ordered list of SeqNodes with the G4 step-entry gate.

    A node already marked complete in durable state is SKIPPED, not re-run --
    this is what makes G4's "survives restarts" promise real (TICKET-0174): a
    halted run resumed via --resume re-executes only the incomplete node(s),
    reusing every persisted artifact (424 cached image verdicts, certified
    fragments) instead of regenerating them. On a fresh run no node is complete
    yet, so this is a no-op."""
    prev_id = None
    for node in nodes:
        if sctx.state.node_complete(node.id):
            emit_indicator(node.phase + "  [already complete -- resumed]")
            prev_id = node.id
            continue
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

        # Durable-state writes: a storage/IO failure here must halt cleanly (G4)
        # rather than abort the sequence with an uncaught exception (TICKET-0120).
        try:
            sctx.state.mark_node(node.id, complete=result.get("complete", True),
                                 output_ref=result.get("output_ref"), note=result.get("note", ""))
            sctx.state.log("node_done", {"node": node.id, "status": result.get("status", "ok"),
                                         "note": result.get("note", "")})
        except Exception as e:
            return _halt(sctx, node, "durable-state write failed", str(e)[:160],
                         "check disk/permissions for the run dir, then re-run " + node.id)
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
    ia = state.read_artifact("1J_image_audit")
    if ia and ia.get("status") == "ok":
        parts.append("Image audit (1J): audited " + str(ia.get("images_audited", 0)) + "/"
                     + str(ia.get("images_total", 0)) + " images; contradicted="
                     + str(ia.get("contradicted_count", 0)) + ", corrections to apply="
                     + str(len(ia.get("corrections") or [])))
    elif ia:
        parts.append("Image audit (1J): " + str(ia.get("status")))
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
        outcome = review_loop.run_generative_node(spec, sctx.context, state=sctx.state)
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


def _section_items(sctx):
    """Per-section items for Step 9-F: each top-level H2 (excluding nav headings).
    validators.body_h2_tags() excludes any H2 in the pre-fold zone (before
    <!--more-->) -- not a real content section (some legacy Blogger posts
    style the post's own TITLE as an H2 above the fold; TICKET-0154/0158) --
    generating a section-closing factoid for it would waste a round-trip and
    read as a redundant restatement of the whole post's scope."""
    html = sctx.state.get_working_html()
    out = []
    for h in validators.body_h2_tags(html):
        t = h.get_text(strip=True)
        if t and t.lower() not in ("route at a glance", "next stop", "route summary"):
            out.append({"section_topic": t, "subject": t})
    return out


def _image_pair_items(sctx):
    """Per-pair items for Step 13: each consecutive image pair, subject = its captions."""
    html = sctx.state.get_working_html()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_=lambda c: c and "tr-caption-container" in c)
    caps = []
    for tbl in tables:
        cap = tbl.find("td", class_=lambda c: c and "tr-caption" in c)
        caps.append(cap.get_text(" ", strip=True) if cap else "")
    items = []
    for pair in validators.consecutive_image_pairs(html):
        i, j = pair["image_index"], pair["next_index"]
        subj = " / ".join(x for x in (caps[i] if i < len(caps) else "",
                                      caps[j] if j < len(caps) else "") if x)
        items.append({"subject": subj or "the two adjacent photos",
                      "section_topic": sctx.context.get("post_title", "")})
    return items


def _repetition_rule_items(sctx):
    """One Step-12 item per real 1H/1I finding: a repeated sentence, a forbidden
    word/phrase NOT already handled by the deterministic curated-synonym swap
    (assembler._FORBIDDEN_SYNONYMS, applied at Phase 5 assembly -- after this node
    runs), or a first-person narrator violation. Each item carries a `needle` (fed
    to _locate_flagged_passage to find the actual flagged passage) and an `issue`
    description for the writer/reviewer prompts. Before this (TICKET-0164),
    step12_resolve ran as a plain, non-iterating node whose prompts read
    context['issue']/context['passage'] -- keys nothing ever populated -- so it
    silently built an empty prompt every run and never resolved a single 1H/1I
    finding."""
    rep = sctx.state.read_artifact("analysis_1H_repetition") or {}
    rules = sctx.state.read_artifact("analysis_1I_writing_rules") or {}
    items = []
    for sent in (rep.get("repeated_sentences") or [])[:5]:
        items.append({"needle": sent, "kind": "repetition",
                      "issue": "Repeated sentence/phrase in the post: " + sent})
    for hit in (rules.get("forbidden") or []):
        term = hit.get("term", "")
        if not term or term.lower() in assembler._FORBIDDEN_SYNONYMS:
            continue   # curated swap fixes this deterministically at Phase 5
        items.append({"needle": term, "issue": "Forbidden " + hit.get("kind", "word")
                      + " '" + term + "' used in the post"})
    if rules.get("narrator"):
        html = sctx.state.get_working_html()
        text = validators.plain_text(validators._body_below_more(html))
        narrator_hits = 0
        for sent in validators._sentences(text):
            if narrator_hits >= 3:
                break
            if re.search(r"\bI\b", sent) or re.search(r"\bme\b", sent, re.IGNORECASE):
                items.append({"needle": sent, "issue": "First-person narrator voice: " + sent[:200]})
                narrator_hits += 1
    return items


def step12_resolve_node():
    """Step 12: resolve real 1H/1I findings against the actual body passage, one
    item per finding, splicing each certified writer fix in place as it lands
    (TICKET-0164). Uses a custom handler (not the generic iterating_generative_node,
    which only collects outputs for _collect_fragments) because each fix must be
    spliced into the live working HTML immediately -- the next item's passage must
    be located in the POST-splice tree, not a stale copy."""
    node_id = "step12_resolve"

    def handler(sctx):
        if sctx.dry_generative:
            return {"complete": True, "note": "[dry] step12_resolve stubbed"}
        items = _repetition_rule_items(sctx)
        fixed, skipped = [], []
        for it in items:
            # A sentence repeated across many nodes (a running gag in captions)
            # is condensed deterministically -- keep the first instance, strip
            # the rest -- rather than rewriting one node at a time (TICKET-0172).
            if it.get("kind") == "repetition":
                n = _dedupe_repeated_phrase(sctx, it["needle"])
                if n:
                    fixed.append({"item": it, "output": "(deterministic dedupe: "
                                  + str(n) + " duplicate instance(s) condensed)"})
                    continue
            html = sctx.state.get_working_html()
            node = _locate_flagged_passage(html, it["needle"])
            if node is None:
                skipped.append({"item": it, "reason": "could not localize passage"})
                continue
            ctx = dict(sctx.context)
            ctx.update({"issue": it["issue"], "passage": str(node),
                       "existing_facts": sctx.context.get("existing_facts", "")})
            try:
                outcome = review_loop.run_generative_node(node_specs.step12_resolve(), ctx, state=sctx.state)
            except Exception as e:
                # Never let one bad finding take down the rest of the node -- these
                # are best-effort resolutions, not required content (TICKET-0143 precedent).
                skipped.append({"item": it, "reason": "error: " + str(e)[:160]})
                continue
            if outcome["status"] != "CERTIFIED" or not outcome["output"].strip():
                skipped.append({"item": it, "reason": outcome.get("reason", outcome["status"])})
                continue
            if not _splice_passage_fix(sctx, node, outcome["output"]):
                skipped.append({"item": it, "reason": "href diff failed (G3)"})
                continue
            fixed.append({"item": it, "output": outcome["output"], "rounds": outcome.get("rounds")})
        sctx.state.save_artifact("gen_" + node_id, {
            "status": "CERTIFIED" if fixed else "SKIP",
            "fixed": fixed, "skipped": skipped,
        })
        return {"complete": True, "output_ref": "gen_" + node_id,
                "note": "resolved " + str(len(fixed)) + "/" + str(len(items)) + " finding(s)"}
    return SeqNode(node_id, "Phase 3 / Step 12 - Resolve repetition/rules", "generative", handler)


def iterating_generative_node(node_id, phase, spec_factory, items_fn):
    """Run a generative node ONCE PER ITEM (Step 9-F per section, Step 13 per image
    pair -- TICKET-0053). Each item builds its own per-item context; certified
    outputs are collected. Items that cannot certify are skipped (workflow-sanctioned
    for these optional enhancers), so the run never halts here."""
    def handler(sctx):
        if sctx.dry_generative:
            return {"complete": True, "note": "[dry] iterating generative stubbed"}
        items = items_fn(sctx)
        outputs, per_item = [], []
        for it in items:
            # run_generative_node already catches its own internal failures and
            # returns an ESCALATE outcome rather than raising, but a per-item
            # exception here (a bad spec_factory/items_fn value, an unexpected
            # dict shape) must still never take down the whole node -- these are
            # workshop-sanctioned skippable enhancers, not required content
            # (TICKET-0143).
            try:
                spec = spec_factory()
                ctx = dict(sctx.context)
                ctx.update(it)
                outcome = review_loop.run_generative_node(spec, ctx, state=sctx.state)
            except Exception as e:
                per_item.append({"item": it, "skipped": True, "reason": "error: " + str(e)[:160]})
                continue
            if outcome["status"] == "CERTIFIED" and outcome["output"].strip():
                outputs.append(outcome["output"])
                per_item.append({"item": it, "output": outcome["output"],
                                 "rounds": outcome.get("rounds")})
            else:
                per_item.append({"item": it, "skipped": True,
                                 "reason": outcome.get("reason", outcome["status"])})
        sctx.state.save_artifact("gen_" + node_id, {
            "status": "CERTIFIED" if outputs else "SKIP",
            "output": "\n".join(outputs),
            "outputs": outputs,
            "items": per_item,
        })
        return {"complete": True, "output_ref": "gen_" + node_id,
                "note": "certified " + str(len(outputs)) + "/" + str(len(items)) + " item(s)"}
    return SeqNode(node_id, phase, "generative", handler)


# Deterministic Phase-1 analysis passes (TICKET-0003). These audit the ORIGINAL
# prose and produce structured findings for the Phase 4 summary + Step 12; they run
# without an LLM (the DeepSeek-only reviewer can't web-verify, and rules/repetition/
# readability are mechanical anyway).
_ANALYSIS_IMPL = {
    "1A_facts": lambda html: validators.fact_sanity(html),
    "1B_readability": lambda html: validators.readability(html),
    "1H_repetition": lambda html: validators.repetition_scan(html),
    "1I_writing_rules": lambda html: validators.writing_rules_audit(html),
}


def _analysis_note(node_id, data):
    if node_id == "1B_readability":
        return "flesch=" + str(data.get("flesch")) + " target_ok=" + str(data.get("target_ok"))
    if node_id == "1H_repetition":
        return ("repeated sentences=" + str(data.get("repeated_sentence_count", 0))
                + " ngrams=" + str(data.get("repeated_ngram_count", 0)))
    if node_id == "1I_writing_rules":
        return "clean=" + str(data.get("clean")) + " forbidden=" + str(data.get("forbidden_count", 0))
    if node_id == "1A_facts":
        return ("numeric_claims=" + str(data.get("numeric_claims", 0))
                + " sources=" + str(data.get("external_sources", 0)))
    return "analysis recorded"


def analysis_node(node_id, phase):
    """Deterministic Phase-1 analysis pass (1A/1B/1H/1I). Stubbed only in dry mode."""
    def handler(sctx):
        if sctx.dry_generative:
            return {"complete": True, "note": "[dry] analysis stubbed"}
        impl = _ANALYSIS_IMPL.get(node_id)
        if impl is None:
            sctx.state.save_artifact("analysis_" + node_id, {"status": "no_impl"})
            return {"complete": True, "note": "analysis recorded"}
        try:
            data = impl(sctx.state.get_working_html())
        except Exception as e:
            data = {"error": str(e)[:160]}
        sctx.state.save_artifact("analysis_" + node_id, data)
        return {"complete": True, "note": _analysis_note(node_id, data)}
    return SeqNode(node_id, phase, "analysis", handler)


def image_audit_node():
    """Phase 1 / 1J -- visual image audit (TICKET-0167): a NIM vision model looks
    at every photograph and flags alt/title/caption text the visible content
    CONTRADICTS (subject-category impossibility only -- proper nouns are
    unverifiable from pixels and never flagged). Gated corrections land in the
    1J artifact and are applied deterministically at Phase 5 assembly.

    OFF BY DEFAULT (TICKET-0202): this pass makes real, metered VLM calls per
    image (hundreds on a large post) and was judged something the operator
    should deliberately turn on per-run, not something every run silently pays
    for. Opt in with ORCH_IMAGE_AUDIT=1. An audit outage while enabled (no key,
    all models down) records status=unavailable and continues -- once turned
    on, it must never block the pipeline."""
    def handler(sctx):
        if sctx.dry_generative:
            return {"complete": True, "note": "[dry] image audit stubbed"}
        if os.environ.get("ORCH_IMAGE_AUDIT", "0") != "1":
            sctx.state.save_artifact("1J_image_audit", {"status": "disabled"})
            return {"complete": True, "note": "image audit disabled (default off; set ORCH_IMAGE_AUDIT=1 to enable)"}
        from . import image_audit
        try:
            result = image_audit.audit_images(sctx.state.get_working_html(),
                                              state=sctx.state,
                                              log=lambda m: print(_ascii("   " + m)))
        except Exception as e:
            sctx.state.save_artifact("1J_image_audit",
                                     {"status": "unavailable", "error": str(e)[:200]})
            return {"complete": True,
                    "note": "image audit unavailable (" + str(e)[:120] + ") -- continuing"}
        result["status"] = "ok"
        sctx.state.save_artifact("1J_image_audit", result)
        return {"complete": True, "output_ref": "1J_image_audit",
                "note": ("audited " + str(result["images_audited"]) + "/"
                         + str(result["images_total"]) + " image(s); contradicted="
                         + str(result["contradicted_count"]) + " corrections="
                         + str(len(result["corrections"]))
                         + (" fetch_fail=" + str(result["fetch_failures"])
                            if result["fetch_failures"] else "")
                         + (" review_fail=" + str(result["review_failures"])
                            if result["review_failures"] else ""))}
    return SeqNode("1J_image_audit", "Phase 1 / 1J - Visual image audit (VLM)", "analysis", handler)


def context_extraction_node():
    """Derive the generative context (route, sections, stops, landmarks) from the
    source post -- deterministically, from its existing schema + structure."""
    def handler(sctx):
        ctx = context_extractor.extract_context(sctx.state.get_working_html(),
                                                allow_llm=not sctx.dry_generative)
        # Last-resort grounded fallback (TICKET-0133): no schema, no <h1>, and
        # route derivation found nothing -- rather than leave post_title/origin/
        # destination all empty (which invites downstream nodes to hallucinate a
        # whole fictional trip to fill the gap, as seen on arsenalna1), derive a
        # real subject from the post's own URL slug when the operator supplied
        # --current-url. Never invents facts -- the slug IS the real post.
        if not ctx.get("post_title"):
            fallback = context_extractor.title_from_url_slug(sctx.context.get("current_url"))
            if fallback:
                ctx["post_title"] = fallback
                if not ctx.get("origin"):
                    ctx["origin"] = fallback
                if not ctx.get("destination"):
                    ctx["destination"] = fallback
        sctx.state.save_artifact("context", ctx)
        sctx.context.update(ctx)
        return {"complete": True,
                "note": "context: '" + (ctx.get("origin") or "?") + "' -> '"
                        + (ctx.get("destination") or "?") + "', "
                        + str(len(ctx.get("sections") or [])) + " sections, "
                        + str(len(ctx.get("stops") or [])) + " stops"}
    return SeqNode("context_extraction", "Setup - Source context extraction", "deterministic", handler)


def lead_context_node():
    """If the operator supplied prior/next LIVE post URLs (this post's place in a
    series), fetch their real title+gist so step6/step10 can write a genuine,
    linked lead-in/lead-out instead of inventing one (TICKET-0132). Optional --
    a network failure or missing URL just means no lead-in/lead-out framing is
    attempted; it never halts the run."""
    def handler(sctx):
        notes = []
        for key, ctx_key in (("prior_url", "prior_post"), ("next_url", "next_post")):
            url = sctx.context.get(key)
            if not url:
                continue
            # fetch_post_gist already catches network/parse errors internally and
            # returns None -- this belt-and-suspenders try/except makes sure that
            # promise holds even if something outside its own guarded block raises
            # (TICKET-0138): a lead-in/lead-out fetch must NEVER halt the run.
            try:
                post = context_extractor.fetch_post_gist(url)
            except Exception as e:
                post = None
                notes.append(ctx_key + "=error(" + str(e)[:60] + ")")
                sctx.context[ctx_key] = post
                continue
            sctx.context[ctx_key] = post
            notes.append(ctx_key + ("=" + post.get("title", "")[:40] if post else "=unreachable"))
        # Persist so a --resume can rehydrate the series context without
        # re-fetching (this node is skipped on resume, TICKET-0174).
        sctx.state.save_artifact("lead_context", {
            k: sctx.context.get(k) for k in ("prior_post", "next_post")
            if sctx.context.get(k) is not None})
        return {"complete": True, "note": "lead context: " + (", ".join(notes) if notes else "none supplied")}
    return SeqNode("lead_context", "Setup - Prior/next post lead-in/lead-out context", "deterministic", handler)


def phase2_url_lock_node():
    def handler(sctx):
        return {"complete": True, "note": "URL stub frozen -- no slug change permitted"}
    return SeqNode("phase2_url_lock", "Phase 2 - URL stub lock", "deterministic", handler)


def _collect_fragments(sctx):
    """Gather the certified generative fragments from the run artifacts."""
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
    if sep and sep.get("outputs"):
        fragments["separators"] = list(sep["outputs"])       # one per image pair (0053)
    elif sep and sep.get("status") == "CERTIFIED" and sep.get("output"):
        fragments["separators"] = [sep["output"]]
    fac = sctx.state.read_artifact("gen_step9f_factoid")
    if fac and fac.get("items"):
        factoids = [{"section": it["item"].get("section_topic", ""), "html": it["output"]}
                    for it in fac["items"] if it.get("output")]
        if factoids:
            fragments["factoids"] = factoids
    return fragments


def _assemble_working(sctx):
    """(Re)assemble working.html from the saved pre-assembly source + current
    fragment artifacts. Reusable so the Pass-1 bounce can reassemble after
    regenerating a fragment (TICKET-0123)."""
    source = sctx.state.read_artifact("pre_assembly_source")
    src_html = source.get("html") if isinstance(source, dict) else None
    if src_html is None:
        src_html = sctx.state.get_working_html()          # first pass: working == source
        sctx.state.save_artifact("pre_assembly_source", {"html": src_html})
    fragments = _collect_fragments(sctx)
    # Keyword-rich schema name/description from the certified title/search desc (0107).
    title_art = sctx.state.read_artifact("gen_step1_title")
    if title_art and title_art.get("status") == "CERTIFIED" and title_art.get("output"):
        sctx.context["schema_name"] = title_art["output"].strip()
    desc_art = sctx.state.read_artifact("gen_step2f_search_description")
    if desc_art and desc_art.get("status") == "CERTIFIED" and desc_art.get("output"):
        sctx.context["schema_description"] = desc_art["output"].strip()
    ia = sctx.state.read_artifact("1J_image_audit") or {}
    # Corrections apply only when the audit ran with apply enabled
    # (ORCH_IMAGE_AUDIT_APPLY=1); otherwise they stay findings-only (TICKET-0175).
    corrections = ia.get("corrections") if ia.get("apply_enabled") else None
    assembled = assembler.assemble(src_html, fragments or None, context=sctx.context,
                                   image_corrections=corrections)
    sctx.state.set_working_html(assembled)
    return len(fragments)


def phase5_generate_node():
    """Phase 5 HTML generation: assemble the certified fragments into working.html
    (and run the deterministic transforms: strip styles, reapply summary CSS,
    re-emit YouTube, remove ?m=1)."""
    def handler(sctx):
        n = _assemble_working(sctx)
        return {"complete": True, "note": "assembled HTML (" + str(n)
                + " fragments spliced + pre-fold summary/schema)"}
    return SeqNode("phase5_generate", "Phase 5 - HTML generation (assemble fragments)", "deterministic", handler)


def _drop_flagged_factoid(sctx, pass1):
    """Remove the section-closing factoid whose section the Pass-1 review flags
    (e.g. a chronology/placement problem). Factoids are optional (0053), so dropping
    the offending one yields a clean post while keeping the rest. Returns the dropped
    section name, or None if the REVISE can't be localized to a factoid (TICKET-0123).

    Evidence gate (TICKET-0171): a factoid is only dropped when the review's
    complaint demonstrably concerns the factoid's own TEXT -- a quoted flagged
    phrase appears in its output, or the finding tokens overlap its output
    substantially. Scoring section NAMES alone was observed live (alaska2v1)
    destroying three innocent factoids: a complaint about repeated CAPTION
    phrases mentioned 'Ketchikan'/'Vancouver', which matched factoid section
    titles despite the factoids never containing the flagged phrases. The
    dropped output is preserved in 'dropped_output' (not destroyed) so a bad
    drop is recoverable."""
    fac = sctx.state.read_artifact("gen_step9f_factoid")
    if not fac or not fac.get("items"):
        return None
    rev_text = ((pass1.get("revision_instructions") or "") + " "
                + json.dumps(pass1.get("criteria", {}), ensure_ascii=False))
    rev = rev_text.lower()
    quoted = [_normalize_text(q) for q in _quoted_phrases(rev_text)]
    stop = {"into", "the", "and", "with", "from", "past", "journey", "night"}
    best, best_score = None, 0
    for it in fac["items"]:
        if not it.get("output"):
            continue
        out_norm = _normalize_text(it["output"])
        # Direct evidence: a quoted flagged phrase is IN this factoid's text.
        if any(q and q in out_norm for q in quoted):
            best, best_score = it, 999
            break
        # Circumstantial: substantial overlap between the finding text and the
        # factoid's OUTPUT (not merely its section title).
        sec = (it.get("item") or {}).get("section_topic", "")
        sec_toks = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", sec) if w.lower() not in stop}
        out_toks = _tokens(it["output"])
        score = sum(1 for w in sec_toks if w in rev) + sum(1 for w in out_toks if w in rev)
        if score > best_score:
            best, best_score = it, score
    # Require output-level evidence: either a quoted-phrase hit, or enough of the
    # factoid's own body tokens echoed in the complaint (>= 4 beats coincidental
    # place-name overlap from section titles alone).
    if best is not None and best_score >= 4:
        best["dropped_output"] = best["output"]   # preserve; never destroy (0171)
        best["output"] = ""
        best["dropped_pass1"] = True
        sctx.state.save_artifact("gen_step9f_factoid", fac)
        return (best.get("item") or {}).get("section_topic", "")
    return None


_STOPWORDS = {"the", "and", "with", "from", "into", "that", "this", "for", "was",
              "were", "its", "are", "have", "has", "had", "but", "not", "you",
              "your", "our", "after", "before", "then", "also", "each", "along",
              "near", "over", "when", "while", "here", "there", "which", "still"}


def _normalize_text(s):
    """Lowercase, alnum+space only, collapsed -- makes phrase matching immune to
    apostrophe variants (can't / can’t), punctuation, and case."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (s or "").lower())).strip()


def _quoted_phrases(text, min_len=15):
    """Concrete flagged phrases quoted inside a reviewer's finding text
    ('...' or \"...\"), long enough to be a real phrase and not a stray word."""
    out = []
    for m in re.finditer(r"'([^']{%d,220}?)'|\"([^\"]{%d,220}?)\"" % (min_len, min_len), text or ""):
        out.append(m.group(1) or m.group(2))
    return out


_SENTENCE_RE = re.compile(r"[^.!?]*[.!?]+|[^.!?]+$")


def _dedupe_html(html, phrase):
    """Deterministically condense a phrase repeated across the document
    (TICKET-0172): keep its FIRST occurrence, remove the sentence(s) carrying it
    from every later body paragraph/caption/list item. Matching is normalized
    (case/punctuation/apostrophe-proof); edits touch only the NavigableString
    that holds the sentence, so markup and every <a href> survive verbatim (G3).
    A sentence is removed when its normalized text contains the phrase OR is a
    substantial (>=10 chars) fragment of it (handles a two-sentence running gag
    where the deterministic 1H scan only keyed on one half). Returns
    (new_html, instances_condensed)."""
    from bs4 import BeautifulSoup, NavigableString
    norm_phrase = _normalize_text(phrase)
    if len(norm_phrase) < 10:
        return html, 0
    soup = BeautifulSoup(html, "html.parser")
    first_kept = False
    condensed = 0
    # Walk text nodes in document order, tracking whether we're past <!--more-->.
    from bs4 import Comment
    more_seen = not ("<!--more-->" in html)
    for node in soup.descendants:
        if isinstance(node, Comment) and node.strip() == "more":
            more_seen = True
            continue
        if not more_seen or not isinstance(node, NavigableString) or isinstance(node, Comment):
            continue
        parent = node.parent.name if node.parent else ""
        if parent in ("script", "style"):
            continue
        text = str(node)
        if norm_phrase not in _normalize_text(text):
            continue
        if not first_kept:
            first_kept = True          # the first instance stays as-is
            continue
        sentences = _SENTENCE_RE.findall(text)
        kept = []
        removed_any = False
        for s in sentences:
            ns = _normalize_text(s)
            if ns and (norm_phrase in ns or (len(ns) >= 10 and ns in norm_phrase)):
                removed_any = True
                continue
            kept.append(s)
        if removed_any:
            node.replace_with(NavigableString("".join(kept)))
            condensed += 1
    return str(soup), condensed


def _dedupe_repeated_phrase(sctx, phrase):
    """Apply _dedupe_html to the working HTML AND the saved pre-assembly source
    (when it exists), so a later bounce's reassembly-from-source does not
    resurrect the duplicates just removed. Returns instances condensed."""
    html = sctx.state.get_working_html()
    new_html, n = _dedupe_html(html, phrase)
    if not n:
        return 0
    sctx.state.set_working_html(new_html)
    source = sctx.state.read_artifact("pre_assembly_source")
    if isinstance(source, dict) and source.get("html"):
        src_new, _src_n = _dedupe_html(source["html"], phrase)
        sctx.state.save_artifact("pre_assembly_source", {"html": src_new})
    return n


def _tokens(s):
    return {w for w in re.findall(r"[A-Za-z]{4,}", (s or "").lower()) if w not in _STOPWORDS}


def _root(node):
    """Walk up from a Tag to the document root (the BeautifulSoup object itself is
    the top of the tree), so a mutated node can be serialized back to full HTML."""
    while node.parent is not None:
        node = node.parent
    return node


def _locate_flagged_passage(html, needle):
    """Find the single best-matching body paragraph/caption/list-item whose text
    token-overlaps a Pass-1 finding (needle) the most -- the same token-overlap
    approach already used to localize factoid drops (TICKET-0123), generalized so a
    flagged REPETITION or SMOOTH_READ (whiplash) passage rooted in the post's own
    prose can be localized and rewritten in place, rather than accepted as an
    unfixable source defect (TICKET-0163). Returns the matching Tag (belonging to a
    live, mutable soup) or None if nothing clears a minimal overlap bar."""
    needle_toks = _tokens(needle)
    if not needle_toks:
        return None
    best, best_score = None, 0
    for el in validators.body_content_tags(html, ("p", "td", "li")):
        text = el.get_text(" ", strip=True)
        if len(text) < 20:
            continue
        score = len(_tokens(text) & needle_toks)
        if score > best_score:
            best, best_score = el, score
    # A short needle (a single forbidden word like 'Leverage') can only ever
    # score 1, so the bar must scale with the needle -- a fixed >=2 silently
    # made every single-word Step-12 item unlocalizable (TICKET-0173).
    return best if best_score >= min(2, len(needle_toks)) else None


def _splice_passage_fix(sctx, node, new_html):
    """Splice a Step-12-style passage fix into the live working HTML in place,
    preserving every original <a href> in the passage (G3). Shared by the Pass-1
    bounce remediation (TICKET-0163) and the Step 12 findings-resolution node
    (TICKET-0164) so the splice logic (href diff -> replace_with -> re-serialize
    from the root) is derived once. Returns False (no-op) if the fix would drop a
    link, True once applied."""
    before_inv = validators.href_inventory(str(node))
    if not validators.diff_hrefs(before_inv, new_html)["ok"]:
        return False   # writer dropped a link from the passage -- don't apply (G3)
    root = _root(node)   # capture BEFORE replace_with detaches `node` from the tree
    node.replace_with(assembler._frag(new_html))
    sctx.state.set_working_html(str(root))
    return True


def _remediate_flagged_passage(sctx, pass1):
    """When a Pass-1 REVISE (REPETITION or SMOOTH_READ/whiplash finding) can't be
    localized to a droppable factoid, localize it to the actual body passage and
    have the writer rewrite it in place via the step12_resolve loop (TICKET-0163).
    This applies regardless of whether the flagged wording originated in the
    original author's prose or content this pipeline added -- repetition/whiplash
    is a real defect either way, not an accepted stopping point. Returns a short
    description of what was fixed, or None if it couldn't localize the passage or
    the rewrite didn't certify (falls through to the operator halt)."""
    crit = pass1.get("criteria") or {}
    findings = []
    for key in ("repetition", "smooth_read"):
        findings.extend((crit.get(key) or {}).get("findings") or [])
    needle = (pass1.get("revision_instructions") or "") + " " + " ".join(findings)
    if not needle.strip():
        return None
    html = sctx.state.get_working_html()
    node = _locate_flagged_passage(html, needle)
    if node is None:
        return None
    ctx = dict(sctx.context)
    ctx.update({
        "issue": (findings[0] if findings else pass1.get("revision_instructions", ""))[:400],
        "passage": str(node),
        "existing_facts": sctx.context.get("existing_facts", ""),
    })
    outcome = review_loop.run_generative_node(node_specs.step12_resolve(), ctx, state=sctx.state)
    if outcome["status"] != "CERTIFIED" or not outcome["output"].strip():
        return None
    if not _splice_passage_fix(sctx, node, outcome["output"]):
        return None
    return (findings[0] if findings else "flagged passage")[:80]


def phase5_certification_node():
    def handler(sctx):
        for attempt in range(MAX_PASS1_BOUNCES + 1):
            cert = review_loop.run_document_certification(
                sctx.state, run_reviewer=not sctx.dry_generative, context=sctx.context)
            if cert.get("certified"):
                note = "G2 two-pass clean -> delivery permitted"
                if attempt:
                    note += " (after " + str(attempt) + " Pass-1 bounce(s))"
                return {"complete": True, "note": note}
            # A real DETERMINISTIC (Pass-2) failure can't be auto-fixed -> halt.
            failed = (cert.get("pass2_deterministic") or {}).get("failed", [])
            if failed:
                return {"halt": True, "halt_reason": "Phase 5 G2 Pass-2 not clean",
                        "item": str(failed), "action": "fix the failing checks and re-run Phase 5"}
            # Pass-1 (holistic) REVISE with a clean Pass-2: bounce (TICKET-0123).
            if attempt >= MAX_PASS1_BOUNCES:
                break
            pass1 = cert.get("pass1_reviewer") or {}
            # FIRST: a repeated phrase quoted in the findings that occurs in
            # multiple body/caption text nodes is condensed deterministically --
            # keep the first instance, strip the rest (TICKET-0172). This
            # targets the reviewer's ACTUAL complaint before any content is
            # sacrificed; observed live (alaska2v1): a 9-caption running gag
            # burned all 3 bounces on innocent factoids and still halted.
            rep_findings = " ".join(
                ((pass1.get("criteria") or {}).get("repetition") or {}).get("findings") or [])
            deduped_total = 0
            for phrase in _quoted_phrases((pass1.get("revision_instructions") or "")
                                          + " " + rep_findings):
                deduped_total += _dedupe_repeated_phrase(sctx, phrase)
            if deduped_total:
                sctx.operator.info("Pass-1 flagged repeated phrase(s); condensed "
                                   + str(deduped_total)
                                   + " duplicate instance(s) and re-certifying...")
                continue
            dropped = _drop_flagged_factoid(sctx, pass1)
            if dropped:
                sctx.operator.info("Pass-1 flagged content; dropped the factoid for '"
                                   + dropped + "' and reassembling...")
                _assemble_working(sctx)
                continue
            # Not a factoid -- try localizing + rewriting the actual flagged passage
            # (repetition/whiplash rooted in the post's own prose, TICKET-0163).
            fixed = _remediate_flagged_passage(sctx, pass1)
            if not fixed:
                break   # couldn't localize/certify a fix -> halt for operator
            sctx.operator.info("Pass-1 flagged content; rewrote the passage about '"
                               + fixed + "' and re-certifying...")
        # Exhausted bounces or unlocalizable REVISE.
        p1 = cert.get("pass1_reviewer") or {}
        return {"halt": True, "halt_reason": "Phase 5 G2 Pass-1 not clean",
                "item": str((p1.get("revision_instructions") or p1.get("decision")))[:160],
                "action": "review the holistic finding and re-run Phase 5"}
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
    ig = iterating_generative_node
    n = node_specs
    return [
        precheck_node(),
        context_extraction_node(),
        lead_context_node(),
        # Phase 1 -- scan & analyze (read-only)
        a("1A_facts", "Phase 1 / 1A - Fact & sanity check"),
        a("1B_readability", "Phase 1 / 1B - Human readability"),
        d("1C_media_inventory", "Phase 1 / 1C - Media & links inventory", validators.media_inventory),
        d("1G_encoding", "Phase 1 / 1G - Character-encoding audit", validators.scan_question_marks),
        d("1F_summary_block", "Phase 1 / 1F - Summary block audit", validators.summary_block),
        a("1H_repetition", "Phase 1 / 1H - Repetition scan"),
        a("1I_writing_rules", "Phase 1 / 1I - Writing-rules audit (existing prose)"),
        image_audit_node(),   # 1J -- visual image audit (TICKET-0167)
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
        # Step 9-F / Step 13 iterate PER ITEM: one factoid per H2 section, one
        # separator per consecutive-image pair (TICKET-0053).
        ig("step9f_factoid", "Phase 3 / Step 9-F - Section-closing factoids",
           n.step9f_factoid, _section_items),
        g("step10_journey_significance", "Phase 3 / Step 10 - Journey significance", n.step10_journey_significance),
        # Step 12 resolves violations flagged by 1H/1I: one item per real finding,
        # spliced into working.html as each certifies (TICKET-0164). Never halts --
        # unresolved findings are just skipped and recorded.
        step12_resolve_node(),
        ig("step13_separator", "Phase 3 / Step 13 - Image separators",
           n.step13_separator, _image_pair_items),
        # Phase 4 -- operator approval (blocks HTML generation)
        phase4_gate_node(),
        # Phase 5 -- HTML generation (assemble) then sanity cert (G2 two-pass;
        # Step 14 holistic read is Pass 1)
        phase5_generate_node(),
        phase5_certification_node(),
        # Phase 6 -- deliverables
        phase6_deliverables_node(),
    ]
