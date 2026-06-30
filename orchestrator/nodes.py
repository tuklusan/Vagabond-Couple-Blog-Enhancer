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


# ---------------------------------------------------------------------------
# Step 1 -- SEO title  (distinct deterministic check: format, no emoji/brand)
# ---------------------------------------------------------------------------
_EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF☀-➿←-⇿⬀-⯿]")


def title_deterministic_check(output, context):
    t = _plain(output).strip()
    findings = []
    if not t:
        findings.append("empty title")
    if _EMOJI_RE.search(t):
        findings.append("emoji present -- titles must have none")
    if "(" in t or ")" in t:
        findings.append("parentheticals present -- not allowed in title")
    if len(t) > 120:
        findings.append("title overlong (" + str(len(t)) + " chars)")
    findings += writing_rules_findings(t)
    return (len(findings) == 0, findings)


def step1_title() -> GenerativeNode:
    def writer(context, prior, revision):
        system = (
            "You write ONE SEO-optimized blog post title. Format: "
            "'[Origin] to [Destination] Overland via [waypoints or themes]'. The title "
            "must carry the highest-value search keywords (place names, landmarks, route "
            "terms a real searcher types). Default cap THREE waypoints; exceed only if each "
            "extra term is independently high-search-value. NO emoji, NO parentheticals, NO "
            "business brand names, no forbidden words. Output ONLY the title text on one line."
        )
        user = (
            "Origin: " + context["origin"] + "\nDestination: " + context["destination"] +
            "\nWaypoints/themes available: " + ", ".join(context.get("waypoints", [])) +
            "\nKnown high-value landmarks: " + context.get("landmarks", "")
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify a travel-blog SEO title. Use web_search to gauge whether the place "
            "names are real and which terms have genuine search value. Certify: (a) FACTS -- "
            "origin/destination/waypoints are real and correctly spelled; (b) WRITING RULES "
            "-- format '[Origin] to [Destination] Overland via ...', no emoji/parenthetical/"
            "brand/forbidden words, waypoints justified by keyword value; (d) no redundant "
            "terms.\n" + _VERDICT_SHAPE
        )
        user = "Route: " + json.dumps(
            {k: context.get(k) for k in ("origin", "destination", "waypoints")},
            ensure_ascii=False) + "\n\nTitle to certify:\n" + output
        return system, user

    return GenerativeNode(
        id="step1_title", label="Step 1 - SEO title",
        build_writer_prompt=writer, deterministic_check=title_deterministic_check,
        build_review_prompt=review, web_search=True,
        writer_max_tokens=200, review_max_tokens=1200, temperature=0.4,
    )


# ---------------------------------------------------------------------------
# Step 2-F -- search description (<=150 chars, must include ETR)
# ---------------------------------------------------------------------------
def description_deterministic_check(output, context):
    t = _plain(output).strip()
    findings = []
    if len(t) > 150:
        findings.append("description is " + str(len(t)) + " chars (max 150)")
    if "ETR" not in t:
        findings.append("missing 'ETR: N min'")
    findings += writing_rules_findings(t)
    return (len(findings) == 0, findings)


def step2f_search_description() -> GenerativeNode:
    def writer(context, prior, revision):
        etr = context.get("etr_minutes", "")
        system = (
            "You write ONE Blogger search description, MAX 150 characters. Include the "
            "primary route (origin -> destination), the highest-value searchable themes/"
            "landmarks, and the literal token 'ETR: " + str(etr) + " min.'. Do NOT add the "
            "#VagabondCouple hashtag. No forbidden words. Output ONLY the description line."
        )
        user = (
            "Origin: " + context["origin"] + "\nDestination: " + context["destination"] +
            "\nThemes/landmarks: " + context.get("landmarks", "") +
            "\nETR minutes: " + str(etr)
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify a <=150-char Blogger search description. Certify: (a) FACTS -- route "
            "and landmarks accurate; (b) WRITING RULES -- <=150 chars, includes ETR, highest-"
            "value keywords prioritised, no forbidden words/hashtag; (d) no redundancy.\n"
            + _VERDICT_SHAPE
        )
        user = "Length: " + str(len(_plain(output).strip())) + " chars\n\nDescription:\n" + output
        return system, user

    return GenerativeNode(
        id="step2f_search_description", label="Step 2-F - Search description",
        build_writer_prompt=writer, deterministic_check=description_deterministic_check,
        build_review_prompt=review, web_search=False,
        writer_max_tokens=200, review_max_tokens=1000, temperature=0.3,
    )


# ---------------------------------------------------------------------------
# Step 10 -- journey significance paragraph (prose; facts + repetition)
# ---------------------------------------------------------------------------
def step10_journey_significance() -> GenerativeNode:
    def writer(context, prior, revision):
        system = (
            "You write ONE 'journey significance' paragraph that connects this post's stops "
            "to the wider overland expedition (Silk Road context where relevant). Give the "
            "post a thesis beyond individual stops. Narrator we/us, no forbidden words, no "
            "'X is not just a Y' framing, no 'we learned/realized that'. Output ONLY a single "
            "<p>...</p>."
        )
        user = (
            "Post route: " + context["origin"] + " -> " + context["destination"] +
            "\nThemes: " + context.get("landmarks", "") +
            "\nFacts already in the post (do not repeat):\n" + context.get("existing_facts", "(none)")
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify a journey-significance paragraph. Use web_search to verify any "
            "historical/geographic claim (e.g. Silk Road links). Certify: (a) FACTS accurate; "
            "(b) WRITING RULES -- narrator we/us, no forbidden words, no contrast framing; "
            "(d) REPETITION -- introduces no fact already in the post.\n" + _VERDICT_SHAPE
        )
        user = ("Facts already in post:\n" + context.get("existing_facts", "(none)") +
                "\n\nParagraph to certify:\n" + output)
        return system, user

    return GenerativeNode(
        id="step10_journey_significance", label="Step 10 - Journey significance",
        build_writer_prompt=writer, deterministic_check=standard_deterministic_check,
        build_review_prompt=review, web_search=True,
        writer_max_tokens=600, review_max_tokens=1536,
    )


# ---------------------------------------------------------------------------
# Step 13 -- image separator paragraph (facts-critical, non-repetitive)
# ---------------------------------------------------------------------------
def step13_separator() -> GenerativeNode:
    def writer(context, prior, revision):
        system = (
            "You write ONE separator paragraph (2-4 sentences) to sit between two adjacent "
            "photos. It must add genuine, factual information about what the photos show -- "
            "history, construction, cultural significance, or sensory reality -- NOT restate "
            "anything already in the post. Narrator we/us where natural; no forbidden words, "
            "no category-colon openers. Output ONLY a single <p>...</p>."
        )
        user = (
            "Between photos of: " + context.get("subject", "") +
            "\nSection: " + context.get("section_topic", "") +
            "\nFacts already in the post (do not repeat):\n" + context.get("existing_facts", "(none)")
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify an image-separator paragraph. Use web_search to verify its factual "
            "claims. Certify: (a) FACTS verifiable; (b) WRITING RULES -- narrator we/us, no "
            "forbidden words, no label openers; (d) REPETITION -- adds nothing already in the "
            "post.\n" + _VERDICT_SHAPE +
            "\nNever CERTIFY an unverifiable factual claim -- REVISE or ESCALATE."
        )
        user = ("Facts already in post:\n" + context.get("existing_facts", "(none)") +
                "\n\nSeparator to certify:\n" + output)
        return system, user

    return GenerativeNode(
        id="step13_separator", label="Step 13 - Image separator paragraph",
        build_writer_prompt=writer, deterministic_check=standard_deterministic_check,
        build_review_prompt=review, web_search=True,
        writer_max_tokens=400, review_max_tokens=1536,
    )


# Registry of generative nodes implemented so far.
GENERATIVE_NODES = {
    "step1_title": step1_title,
    "step2f_search_description": step2f_search_description,
    "step6_first_body_paragraph": step6_first_body_paragraph,
    "step9f_factoid": step9f_factoid,
    "step10_journey_significance": step10_journey_significance,
    "step13_separator": step13_separator,
}
