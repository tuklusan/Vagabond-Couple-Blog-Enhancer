#!/usr/bin/env python3
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

from . import config, writer_client, reviewer_client


def run_generative_node(spec, context, max_rounds=None, verbose=True):
    """Run one generative node's writer<->reviewer loop. Returns an outcome dict."""
    max_rounds = max_rounds or config.MAX_NODE_ROUNDS
    prior_output = ""
    revision = ""
    history = []
    output = ""
    verdict = {}
    sources = []

    def log(msg):
        if verbose:
            print(("  [" + spec.id + "] " + msg).encode("ascii", "replace").decode("ascii"))

    for rnd in range(1, max_rounds + 1):
        # --- 1. writer ---
        wsys, wuser = spec.build_writer_prompt(context, prior_output, revision)
        text, wprov = writer_client.chat(
            [{"role": "system", "content": wsys}, {"role": "user", "content": wuser}],
            max_tokens=spec.writer_max_tokens, temperature=spec.temperature,
        )
        output = spec.postprocess(text)

        # --- 2. deterministic pre-screen (cheap; no reviewer tokens) ---
        det_ok, det_findings = spec.deterministic_check(output, context)
        if not det_ok:
            log(f"round {rnd}: deterministic FAIL ({wprov}) -> {det_findings}")
            history.append({"round": rnd, "writer": wprov, "stage": "deterministic",
                            "decision": "REVISE", "findings": det_findings})
            revision = ("Your previous draft failed objective checks. Fix ALL of these "
                        "exactly, keep everything else:\n" + json.dumps(det_findings, ensure_ascii=False))
            prior_output = output
            continue

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
