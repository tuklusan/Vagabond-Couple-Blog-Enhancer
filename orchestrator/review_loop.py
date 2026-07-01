#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Tier-1 writer<->reviewer certification loop.

For a generative node:
  1. WRITER (cheap/free) drafts the content.
  2. DETERMINISTIC pre-screen (validators) runs first -- if it fails, we feed the
     exact findings back to the writer WITHOUT spending a reviewer call.
  3. Only once deterministic checks pass does the REVIEWER (Claude/DeepSeek)
     adjudicate the judgment criteria -- (a) facts (web-grounded), (b) writing
     rules nuance, (d) local repetition -- and return a CERTIFIED/REVISE/ESCALATE
     verdict.
  4. Loop until CERTIFIED, or ESCALATE to the operator after MAX_NODE_ROUNDS so an
     unverifiable claim never loops forever (rev-18: "even if it takes a long
     time" -- but not infinitely).

This is the structural anti-hallucination guarantee: the writer never finalises a
claim; the reviewer must certify it (with sources) before it persists.
"""
import json
import os

from . import config, writer_client, reviewer_client, validators

# Consecutive objective (deterministic) failures on the primary writer before the
# loop escalates the writer to DeepSeek for the remaining rounds. Keeps the free
# model primary (cost) while guaranteeing convergence on tight-constraint nodes.
WRITER_ESCALATE_AFTER = int(os.environ.get("ORCH_WRITER_ESCALATE_AFTER", "2"))


def run_generative_node(spec, context, max_rounds=None, verbose=True):
    """Run one generative node's writer<->reviewer loop. Returns an outcome dict."""
    max_rounds = max_rounds or config.MAX_NODE_ROUNDS
    prior_output = ""
    revision = ""
    history = []
    output = ""
    verdict = {}
    sources = []
    det_fail_count = 0            # consecutive objective-check failures on the writer

    def log(msg):
        if verbose:
            print(("  [" + spec.id + "] " + msg).encode("ascii", "replace").decode("ascii"))

    for rnd in range(1, max_rounds + 1):
        # --- 1. writer ---
        # After the free model repeatedly fails a node's OBJECTIVE checks, escalate
        # the writer to DeepSeek (reliable instruction-follower) instead of burning
        # the remaining rounds on a model that cannot meet the constraints.
        prefer_deepseek = det_fail_count >= WRITER_ESCALATE_AFTER
        if prefer_deepseek and det_fail_count == WRITER_ESCALATE_AFTER:
            log(f"round {rnd}: escalating writer -> DeepSeek after {det_fail_count} objective-check failures")
        wsys, wuser = spec.build_writer_prompt(context, prior_output, revision)
        try:
            text, wprov = writer_client.chat(
                [{"role": "system", "content": wsys}, {"role": "user", "content": wuser}],
                max_tokens=spec.writer_max_tokens, temperature=spec.temperature,
                prefer_deepseek=prefer_deepseek,
            )
        except Exception as e:
            # Every writer provider is down -> escalate rather than crash.
            log(f"round {rnd}: writer unavailable -> ESCALATE ({e})")
            return {"status": "ESCALATE", "output": output, "verdict": verdict,
                    "sources": sources, "rounds": rnd, "history": history,
                    "reason": "writer_unavailable: " + str(e)[:160]}
        output = spec.postprocess(text)

        # --- 2. deterministic pre-screen (cheap; no reviewer tokens) ---
        det_ok, det_findings = spec.deterministic_check(output, context)
        if not det_ok:
            det_fail_count += 1
            log(f"round {rnd}: deterministic FAIL ({wprov}) -> {det_findings}")
            history.append({"round": rnd, "writer": wprov, "stage": "deterministic",
                            "decision": "REVISE", "findings": det_findings})
            revision = ("Your previous draft failed objective checks. Fix ALL of these "
                        "exactly, keep everything else:\n" + json.dumps(det_findings, ensure_ascii=False))
            prior_output = output
            continue
        det_fail_count = 0        # a clean draft resets the escalation counter

        # --- 3. reviewer (judgment) ---
        rsys, ruser = spec.build_review_prompt(output, det_findings, context)
        verdict, _rtext, sources = reviewer_client.certify(
            rsys, ruser, web_search=spec.web_search, max_tokens=spec.review_max_tokens)
        decision = str(verdict.get("decision", "ESCALATE")).upper()
        log(f"round {rnd}: review {decision} (writer={wprov}, reviewer={verdict.get('reviewer_provider')})")
        history.append({"round": rnd, "writer": wprov, "stage": "review",
                        "decision": decision, "reviewer": verdict.get("reviewer_provider"),
                        "sources": sources})

        if decision == "CERTIFIED":
            return {"status": "CERTIFIED", "output": output, "verdict": verdict,
                    "sources": sources, "rounds": rnd, "history": history}
        if decision == "ESCALATE":
            return {"status": "ESCALATE", "output": output, "verdict": verdict,
                    "sources": sources, "rounds": rnd, "history": history,
                    "reason": "reviewer_escalated"}

        # REVISE -> feed instructions back to the writer
        revision = (verdict.get("revision_instructions")
                    or json.dumps(verdict.get("criteria", {}), ensure_ascii=False))
        prior_output = output

    # rounds exhausted without certification -> operator decision
    return {"status": "ESCALATE", "output": output, "verdict": verdict, "sources": sources,
            "rounds": max_rounds, "history": history, "reason": "max_rounds"}


# ===========================================================================
# Tier-2 -- document-level certification (Step 14 + Phase 5, Rule G2 two-pass)
# ===========================================================================
def document_deterministic_checklist(html, original_hrefs=None):
    """
    G2 Pass 2 -- re-derive every mechanical fact from the assembled output (not
    from memory of the per-node verdicts). Pure code; no LLM.
    """
    checks = {}
    checks["schema_ok"] = validators.validate_ld_json(html)["ok"]
    checks["more_canonical"] = validators.count_more_tags(html)["canonical_after_script"]
    media = validators.media_inventory(html)
    checks["image_table_match"] = media["image_table_match"]
    checks["no_consecutive_images"] = len(validators.consecutive_image_pairs(html)) == 0
    checks["summary_present"] = validators.summary_block(html)["present"]
    checks["no_ufffd"] = validators.scan_question_marks(html)["ufffd_count"] == 0
    checks["no_forbidden"] = len(validators.scan_forbidden(validators.plain_text(html))) == 0
    raag = validators.raag_vs_h2(html)
    checks["raag_h2_match"] = (not raag["raag_present"]) or raag["counts_match"]
    if original_hrefs is not None:
        checks["hrefs_preserved"] = validators.diff_hrefs(original_hrefs, html)["ok"]
    return {"checks": checks, "ok": all(checks.values()),
            "failed": [k for k, v in checks.items() if not v]}


_DOC_VERDICT_SHAPE = (
    'Output ONLY a JSON verdict:\n'
    '{"decision":"CERTIFIED|REVISE|ESCALATE","criteria":{'
    '"html_sanity":{"status":"pass|fail","findings":["..."]},'
    '"repetition":{"status":"pass|fail","findings":["..."]},'
    '"smooth_read":{"status":"pass|fail","findings":["..."]}},'
    '"revision_instructions":"which section/node to fix if REVISE"}'
)


def _document_review(html):
    """G2 Pass 1 -- reviewer reads the whole post for the holistic criteria."""
    system = (
        "You are the final certifying reviewer for a travel blog post body. Read it as a "
        "first-time human with no prior context. Certify: (c) HTML SANITY -- it reads as "
        "clean, well-structured content with no broken/odd markup; (d) REPETITION -- no "
        "idea, fact, or phrase repeats across sections; (e) SMOOTH READ -- it flows "
        "naturally and makes sense in chronological and geographical order, with no jarring "
        "transitions and one consistent authorial voice.\n" + _DOC_VERDICT_SHAPE
    )
    verdict, _text, _sources = reviewer_client.certify(system, "Post body:\n" + html[:18000],
                                                       web_search=False, max_tokens=2048)
    return verdict


def run_document_certification(state, run_reviewer=True):
    """
    Run both G2 passes over the working HTML. Certified only if Pass 2
    (deterministic re-derivation) is clean AND Pass 1 (reviewer holistic) is
    CERTIFIED. A reviewer outage yields ESCALATE, never a silent pass.
    """
    html = state.get_working_html()
    inv = state.read_artifact("1C_media_inventory")
    original_hrefs = None
    if inv:
        original_hrefs = (inv.get("internal_links") or []) + (inv.get("external_links") or [])

    pass2 = document_deterministic_checklist(html, original_hrefs)
    pass1 = None
    if run_reviewer:
        try:
            pass1 = _document_review(html)
        except Exception as e:
            pass1 = {"decision": "ESCALATE", "note": "reviewer unavailable: " + str(e)[:140]}

    p1_ok = pass1 is None or str(pass1.get("decision", "")).upper() == "CERTIFIED"
    result = {"certified": bool(pass2["ok"] and p1_ok),
              "pass2_deterministic": pass2, "pass1_reviewer": pass1}
    state.save_artifact("phase5_certification", result)
    return result
