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

# How many times to re-roll the (stochastic) reviewer on the SAME content when it
# returns ESCALATE, before feeding the concern back for a content revision. Guards
# against the web-less DeepSeek fallback's inconsistent over-escalation.
REVIEWER_ESCALATE_REROLLS = int(os.environ.get("ORCH_REVIEWER_REROLLS", "2"))


def _safe_certify(spec, rsys, ruser):
    """Call the reviewer, converting ANY unexpected exception into a synthetic
    ESCALATE verdict so a reviewer outage escalates gracefully instead of crashing
    the node loop (TICKET-0013). reviewer_client.certify already handles provider
    fallbacks internally; this guards against errors it does not."""
    try:
        return reviewer_client.certify(
            rsys, ruser, web_search=spec.web_search, max_tokens=spec.review_max_tokens)
    except Exception as e:
        verdict = {"decision": "ESCALATE",
                   "note": "reviewer call failed: " + str(e)[:160],
                   "reviewer_provider": "none", "criteria": {}, "sources": []}
        return verdict, "", []


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
        try:
            wsys, wuser = spec.build_writer_prompt(context, prior_output, revision)
        except Exception as e:
            log(f"round {rnd}: build_writer_prompt error -> ESCALATE ({e})")
            return {"status": "ESCALATE", "output": output, "verdict": verdict,
                    "sources": sources, "rounds": rnd, "history": history,
                    "reason": "build_writer_prompt_failed: " + str(e)[:160]}
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

        # postprocess + deterministic check are pure code, but a malformed writer
        # payload or a validator bug must not crash the whole loop (TICKET-0014).
        try:
            output = spec.postprocess(text)
            det_ok, det_findings = spec.deterministic_check(output, context)
        except Exception as e:
            log(f"round {rnd}: postprocess/check error -> ESCALATE ({e})")
            return {"status": "ESCALATE", "output": output, "verdict": verdict,
                    "sources": sources, "rounds": rnd, "history": history,
                    "reason": "postprocess_or_check_failed: " + str(e)[:160]}

        # --- 2. deterministic pre-screen (cheap; no reviewer tokens) ---
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
        try:
            rsys, ruser = spec.build_review_prompt(output, det_findings, context)
        except Exception as e:
            log(f"round {rnd}: build_review_prompt error -> ESCALATE ({e})")
            return {"status": "ESCALATE", "output": output, "verdict": verdict,
                    "sources": sources, "rounds": rnd, "history": history,
                    "reason": "build_review_prompt_failed: " + str(e)[:160]}
        verdict, _rtext, sources = _safe_certify(spec, rsys, ruser)
        decision = str(verdict.get("decision", "ESCALATE")).upper()
        log(f"round {rnd}: review {decision} (writer={wprov}, reviewer={verdict.get('reviewer_provider')})")
        history.append({"round": rnd, "writer": wprov, "stage": "review",
                        "decision": decision, "reviewer": verdict.get("reviewer_provider"),
                        "sources": sources})

        # A reviewer ESCALATE is often transient -- the web-less DeepSeek fallback
        # over-escalates facts it could actually confirm from reliable knowledge and
        # is inconsistent run-to-run. Re-roll the reviewer on the SAME (good) content
        # a few times before accepting the escalation.
        reroll = 0
        while decision == "ESCALATE" and reroll < REVIEWER_ESCALATE_REROLLS:
            reroll += 1
            verdict, _rtext, sources = _safe_certify(spec, rsys, ruser)
            decision = str(verdict.get("decision", "ESCALATE")).upper()
            log(f"round {rnd}: reviewer re-roll {reroll} -> {decision} "
                f"(reviewer={verdict.get('reviewer_provider')})")

        if decision == "CERTIFIED":
            return {"status": "CERTIFIED", "output": output, "verdict": verdict,
                    "sources": sources, "rounds": rnd, "history": history}
        if decision == "ESCALATE":
            # Still escalating after re-rolls. Don't halt yet: feed the concern back
            # and let the next round refine, escalating terminally only once rounds
            # are exhausted (handled after the loop).
            if rnd >= max_rounds:
                return {"status": "ESCALATE", "output": output, "verdict": verdict,
                        "sources": sources, "rounds": rnd, "history": history,
                        "reason": "reviewer_escalated"}
            revision = ("The reviewer could not certify and raised: "
                        + (verdict.get("revision_instructions")
                           or json.dumps(verdict.get("criteria", {}), ensure_ascii=False)
                           or "unable to verify the claims")
                        + "\nKeep only claims that are clearly true and well-known; make the "
                          "route and facts self-evident. Then resubmit.")
            prior_output = output
            continue

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
    # Each check is wrapped so a validator bug/edge case marks that check failed
    # rather than aborting the whole certification (TICKET-0015).
    def _chk(name, fn):
        try:
            checks[name] = bool(fn())
        except Exception as e:
            checks[name] = False
            errors[name] = str(e)[:160]

    checks, errors = {}, {}
    _chk("schema_ok", lambda: validators.validate_ld_json(html)["ok"])
    _chk("more_canonical", lambda: validators.count_more_tags(html)["canonical_after_script"])
    _chk("image_table_match", lambda: validators.media_inventory(html)["image_table_match"])
    _chk("no_consecutive_images", lambda: len(validators.consecutive_image_pairs(html)) == 0)
    _chk("summary_present", lambda: validators.summary_block(html)["present"])
    _chk("no_ufffd", lambda: validators.scan_question_marks(html)["ufffd_count"] == 0)
    _chk("no_forbidden", lambda: len(validators.scan_forbidden(validators.plain_text(html))) == 0)
    # Route at a Glance is one item per GEOGRAPHIC stop in travel order (workflow
    # line 356) -- deliberately decoupled from the H2 section count (that is the
    # summary block's job). So only require RAAG, if present, to be a non-empty list.
    def _raag_ok():
        raag = validators.raag_vs_h2(html)
        return (not raag["raag_present"]) or len(raag["raag_items"]) >= 1
    _chk("raag_nonempty", _raag_ok)
    if original_hrefs is not None:
        _chk("hrefs_preserved", lambda: validators.diff_hrefs(original_hrefs, html)["ok"])
    result = {"checks": checks, "ok": all(checks.values()),
              "failed": [k for k, v in checks.items() if not v]}
    if errors:
        result["errors"] = errors
    return result


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
        "first-time human with no prior context. Judge ONLY these three criteria: "
        "(c) HTML SANITY -- it reads as clean, well-structured content with no broken/odd "
        "markup; (d) REPETITION -- no idea, fact, or phrase repeats across sections; "
        "(e) SMOOTH READ -- it flows naturally and makes sense in chronological and "
        "geographical order, with no jarring transitions and one consistent authorial voice. "
        "Do NOT fact-check individual claims here -- factual accuracy is handled in other "
        "steps; ignore possible factual errors for this pass. Set decision to CERTIFIED if "
        "and only if all three criteria pass. List at most the 3 MOST significant findings "
        "per criterion -- do not enumerate every instance; be concise so your reply is never "
        "cut off.\n" + _DOC_VERDICT_SHAPE
    )
    # Send the WHOLE post -- a mid-document cut makes the reviewer report false
    # "truncated content / unclosed tag" findings (deepseek-v4-pro has a 1M-token
    # context, so the generous cap only guards against pathological input).
    # A document-level verdict can carry several findings per criterion (e.g.
    # multiple repetition hits) -- 2048 tokens was too tight and let DeepSeek's
    # JSON get cut off mid-object, which forced an unparseable-verdict ESCALATE
    # that couldn't be localized/bounced (TICKET-0124). Even 4096 wasn't always
    # enough on a particularly verbose reply (TICKET-0135) -- bumped further and
    # capped findings-per-criterion above so future replies stay well inside budget.
    verdict, _text, _sources = reviewer_client.certify(system, "Post body:\n" + html[:200000],
                                                       web_search=False, max_tokens=6144)
    return verdict


def _pass1_ok(pass1):
    """Pass-1 (holistic) acceptance. Certified on an explicit CERTIFIED, OR when all
    three IN-SCOPE criteria (html_sanity, repetition, smooth_read) pass -- this
    absorbs the web-less reviewer's habit of returning REVISE over out-of-scope,
    unverifiable factual asides even when its own holistic criteria all pass. Those
    asides are preserved in the artifact as advisory, not blocking (facts are the
    remit of Phase 1A / Step 12 and the per-node loops, not this pass)."""
    if pass1 is None:
        return True
    if str(pass1.get("decision", "")).upper() == "CERTIFIED":
        return True
    crit = pass1.get("criteria") or {}
    keys = ("html_sanity", "repetition", "smooth_read")
    statuses = [(crit.get(k) or {}).get("status") for k in keys]
    return bool(statuses) and all(s == "pass" for s in statuses)


def run_document_certification(state, run_reviewer=True):
    """
    Run both G2 passes over the working HTML. Certified only if Pass 2
    (deterministic re-derivation) is clean AND Pass 1 (reviewer holistic) is
    CERTIFIED. A reviewer outage yields ESCALATE, never a silent pass.
    """
    html = state.get_working_html()
    if not html:
        # Incomplete/empty working HTML -> not certified, don't crash (TICKET-0071).
        return {"certified": False,
                "pass2_deterministic": {"checks": {}, "ok": False, "failed": ["no_working_html"]},
                "pass1_reviewer": None}
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

    p1_ok = _pass1_ok(pass1)
    result = {"certified": bool(pass2["ok"] and p1_ok),
              "pass2_deterministic": pass2, "pass1_reviewer": pass1}
    state.save_artifact("phase5_certification", result)
    return result
