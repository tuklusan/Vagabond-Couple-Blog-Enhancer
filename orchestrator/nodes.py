#!/usr/bin/env python3
"""
Generative node registry.

Each GenerativeNode bundles the three things the Tier-1 loop needs:
  * build_writer_prompt  -> (system, user) for the cheap writer
  * deterministic_check  -> (ok, findings) run BEFORE the reviewer (free, exact)
  * build_review_prompt  -> (system, user) asking the reviewer for a JSON verdict

Deterministic checks own the mechanical rules (forbidden words, narrator); the
reviewer owns judgment (facts via web search, smoothness, repetition nuance).
"""
import json
import re
from dataclasses import dataclass
from typing import Callable

from bs4 import BeautifulSoup

from . import validators


def _strip_fences(text: str) -> str:
    m = re.search(r"```(?:html)?\s*\n?(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def _plain(html: str) -> str:
    """Visible prose only (strip tags) for rule scanning."""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


@dataclass
class GenerativeNode:
    id: str
    label: str
    build_writer_prompt: Callable
    deterministic_check: Callable
    build_review_prompt: Callable
    web_search: bool = True
    writer_max_tokens: int = 1024
    review_max_tokens: int = 2048
    temperature: float = 0.3
    postprocess: Callable = _strip_fences


# ---------------------------------------------------------------------------
# Shared deterministic writing-rules check (forbidden terms + narrator)
# ---------------------------------------------------------------------------
def writing_rules_findings(text: str):
    findings = []
    for hit in validators.scan_forbidden(text):
        findings.append("forbidden " + hit["kind"] + ": '" + hit["term"] + "' x" + str(hit["count"]))
    if re.search(r"\bI\b", text):
        findings.append("first-person singular 'I' present -- narrator must be we/us")
    if re.search(r"\bme\b", text, re.IGNORECASE):
        findings.append("first-person singular 'me' present -- narrator must be we/us")
    return findings


def standard_deterministic_check(output, context):
    findings = writing_rules_findings(_plain(output))
    return (len(findings) == 0, findings)


_VERDICT_SHAPE = (
    'Output ONLY a JSON verdict (no prose outside it):\n'
    '{"decision":"CERTIFIED|REVISE|ESCALATE","criteria":{'
    '"facts":{"status":"pass|fail","findings":["..."],"sources":["url"]},'
    '"writing_rules":{"status":"pass|fail","findings":["..."]},'
    '"repetition":{"status":"pass|fail","findings":["..."]}},'
    '"revision_instructions":"what to change if REVISE, else empty"}\n'
    'CERTIFIED only if every criterion passes. REVISE with concrete fixes if any '
    'fails and you know how to fix it. ESCALATE only if a fact cannot be verified.'
)


# ---------------------------------------------------------------------------
# Step 6 -- first body paragraph (route-first)
# ---------------------------------------------------------------------------
def step6_first_body_paragraph() -> GenerativeNode:
    def writer(context, prior, revision):
        system = (
            "You are a travel-blog editor for The Vagabond Couple. Narrator is 'we'/'us' "
            "(NEVER 'I'/'me'). Write ONLY the FIRST body paragraph that appears below the "
            "fold. HARD RULE: origin, destination, and primary route method must appear "
            "before any atmosphere or character. Shape:\n"
            "We drove from [ORIGIN] to [DESTINATION] via [KEY WAYPOINTS / METHOD]. "
            "[one sentence on what made this stretch notable]. "
            "[one sentence on what this post covers].\n"
            "Output ONLY the paragraph wrapped in a single <p>...</p>. No preamble. "
            "Avoid all marketing/transition cliche words."
        )
        user = (
            "Origin: " + context["origin"] + "\n"
            "Destination: " + context["destination"] + "\n"
            "Waypoints: " + ", ".join(context.get("waypoints", [])) + "\n"
            "Method: " + context.get("method", "overland") + "\n"
            "What this post covers: " + context.get("covers", "")
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify a travel blog's FIRST body paragraph. Use web_search to confirm "
            "the named places and the stated route method are real and plausible. Certify "
            "against: (a) FACTS -- origin, destination and route method accurate and named; "
            "(b) WRITING RULES -- narrator we/us, route-first order, no forbidden words; "
            "(d) REPETITION -- no idea repeated within the paragraph.\n" + _VERDICT_SHAPE
        )
        user = (
            "Route context: " + json.dumps(
                {k: context.get(k) for k in ("origin", "destination", "waypoints", "method")},
                ensure_ascii=False) +
            "\n\nParagraph to certify:\n" + output
        )
        return system, user

    return GenerativeNode(
        id="step6_first_body_paragraph",
        label="Step 6 - First body paragraph (route-first)",
        build_writer_prompt=writer,
        deterministic_check=standard_deterministic_check,
        build_review_prompt=review,
        web_search=True,
        writer_max_tokens=512,
        review_max_tokens=1536,
    )


# ---------------------------------------------------------------------------
# Step 9-F -- section-closing factoid (facts-critical, folklore must be framed)
# ---------------------------------------------------------------------------
def step9f_factoid() -> GenerativeNode:
    def writer(context, prior, revision):
        system = (
            "You write ONE short, genuinely interesting section-closing factoid for a "
            "travel blog. It must be specific to the section's place/object/event, "
            "factually accurate and verifiable. If the fact is folklore or disputed, you "
            "MUST frame it as such ('Local legend holds that...'). Narrator we/us, no "
            "forbidden words, no 'X is not just a Y' framing. 1-3 sentences. Output ONLY "
            "the factoid text (a single <p>...</p>), no label opener unless told otherwise."
        )
        user = (
            "Section topic: " + context.get("section_topic", "") + "\n"
            "Place/object/event: " + context.get("subject", "") + "\n"
            "Already-covered facts to AVOID duplicating:\n" + context.get("existing_facts", "(none)")
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify a section-closing travel factoid. Use web_search to VERIFY the "
            "claim against authoritative sources. Certify against: (a) FACTS -- verifiably "
            "true, OR explicitly framed as folklore/legend/disputed if not settled; "
            "(b) WRITING RULES -- narrator we/us, no forbidden words, no contrast framing; "
            "(d) REPETITION -- the fact is not already in the post.\n" + _VERDICT_SHAPE +
            "\nNever CERTIFY an unframed claim you cannot verify -- REVISE (add framing or "
            "swap to a verifiable fact) or ESCALATE."
        )
        user = (
            "Section: " + context.get("section_topic", "") +
            "\nAlready-covered facts:\n" + context.get("existing_facts", "(none)") +
            "\n\nFactoid to certify:\n" + output
        )
        return system, user

    return GenerativeNode(
        id="step9f_factoid",
        label="Step 9-F - Section-closing factoid",
        build_writer_prompt=writer,
        deterministic_check=standard_deterministic_check,
        build_review_prompt=review,
        web_search=True,
        writer_max_tokens=400,
        review_max_tokens=1536,
    )


# Registry of generative nodes implemented so far.
GENERATIVE_NODES = {
    "step6_first_body_paragraph": step6_first_body_paragraph,
    "step9f_factoid": step9f_factoid,
}
