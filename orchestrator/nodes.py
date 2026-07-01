#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
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
    # First-person 'I' -- but NOT the interstate-highway designation (I-40, I-5,
    # I-10...), which is pervasive in US road-trip content. Exclude 'I' immediately
    # followed by an (optional) hyphen and a digit.
    if re.search(r"\bI\b(?![-‐-―]?\d)", text):
        findings.append("first-person singular 'I' present -- narrator must be we/us")
    # First-person 'me' is the lowercase pronoun. Case-sensitive so we do not flag
    # the state abbreviation 'ME' (Maine) or other all-caps tokens.
    if re.search(r"\bme\b", text):
        findings.append("first-person singular 'me' present -- narrator must be we/us")
    return findings


# Minimum plain-text length below which an output is almost certainly not real
# content but a stray token / moderation artifact (e.g. openrouter/free emitting
# "User Safety: safe"). Catching it deterministically routes it back to the writer
# (and, after WRITER_ESCALATE_AFTER fails, to DeepSeek) instead of letting empty
# junk reach the reviewer and trigger a terminal ESCALATE.
_MIN_CONTENT_CHARS = 40


def standard_deterministic_check(output, context, min_chars=_MIN_CONTENT_CHARS):
    text = _plain(output).strip()
    findings = writing_rules_findings(text)
    if len(text) < min_chars:
        findings.append("output too short (" + str(len(text)) + " chars) -- not a real "
                        "content block; write the full requested content")
    return (len(findings) == 0, findings)


def prose_paragraph_check(min_chars):
    """A stricter standard check for full-paragraph nodes (route-first body, etc.)."""
    def _check(output, context):
        return standard_deterministic_check(output, context, min_chars=min_chars)
    return _check


def route_items(context):
    """The authoritative, grounded ordered route list for this post.

    Prefer the real H2 sections (the post's actual structure), then schema stops,
    then extracted waypoints. This is the ONLY source of place names a route node
    may use -- the reviewer is DeepSeek-only (no web) and cannot catch invented
    geography, so grounding is enforced here in code (TICKET-0054)."""
    for key in ("sections", "stops", "waypoints"):
        vals = [str(v).strip() for v in (context.get(key) or []) if str(v).strip()]
        if vals:
            return vals
    return []


def geographic_stops(context):
    """Ordered GEOGRAPHIC stops for Route at a Glance (workflow line 356: 'one item
    per named stop or location in travel order' -- places, not thematic sections).
    origin -> waypoints/schema stops -> destination, deduped by leading place name."""
    seq = []
    if context.get("origin"):
        seq.append(str(context["origin"]).strip())
    seq += [str(v).strip() for v in (context.get("waypoints") or []) if str(v).strip()]
    seq += [str(v).strip() for v in (context.get("stops") or []) if str(v).strip()]
    if context.get("destination"):
        seq.append(str(context["destination"]).strip())
    out, seen = [], set()
    for s in seq:
        key = _first_place_token(s).lower()
        if s and key not in seen:
            seen.add(key)
            out.append(s)
    return out


def _first_place_token(name):
    """Leading place name from a section/stop label (before a ' - '/':' descriptor)."""
    return re.split(r"\s+[-:–—]\s+", name.strip())[0].strip()


def grounded_route_check(output, context, items=None):
    """Guard against hallucinated geography (the DeepSeek-only reviewer can't).

    The output must reflect the grounded route list: at least 70% of the grounded
    items must appear (by a significant token), catching wholesale invention like a
    Scandinavian route substituted for a US one."""
    findings = []
    if items is None:
        items = route_items(context)
    if not items:
        return findings
    text = _plain(output).lower()

    def _covered(item):
        tok = _first_place_token(item).lower()
        if tok and tok in text:
            return True
        # else: any distinctive word (>3 chars) from the item present
        for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", item):
            if w.lower() in text and w.lower() not in ("the", "and", "our", "with", "from", "into"):
                return True
        return False

    covered = sum(1 for it in items if _covered(it))
    if covered < (len(items) * 7 + 9) // 10:  # ceil(0.7 * n)
        findings.append("route content not grounded in the known stops "
                        "(" + str(covered) + "/" + str(len(items)) + " covered) -- "
                        "use ONLY the provided stops, do not invent places")
    return findings


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
        deterministic_check=prose_paragraph_check(120),
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
# Actual emoji blocks only -- NOT arrows/misc-technical symbols, which are valid in
# a title (TICKET-0010): Misc Symbols & Pictographs, Emoticons, Transport & Map,
# Supplemental Symbols & Pictographs, Dingbats, and the two common Misc-Symbols emoji.
_EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF"
    r"\U0001F900-\U0001FAFF☀-⛿✀-➿]")


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
    if not re.search(r"ETR:\s*\d+\s*min", t):   # require the number, not just 'ETR' (TICKET-0011)
        findings.append("missing 'ETR: N min' (with a number)")
    findings += writing_rules_findings(t)
    return (len(findings) == 0, findings)


def step2f_search_description() -> GenerativeNode:
    def writer(context, prior, revision):
        etr = context.get("etr_minutes", "")
        system = (
            "You write ONE Blogger search description, MAX 150 characters. Include the "
            "primary route (origin -> destination), the highest-value searchable themes/"
            "landmarks, and the literal token 'ETR: " + str(etr) + " min.'. "
            "ETR means Estimated Time to Read (this blog post's reading time in minutes); "
            "it is a fixed value -- use it verbatim, never change it. Do NOT add the "
            "#VagabondCouple hashtag. No forbidden words. Narrator is 'we/us' -- NEVER write "
            "'I' or 'me'. Output ONLY the single description line (<=150 chars), nothing else "
            "-- no preamble, no explanation, no quotes."
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
            "NOTE: 'ETR: N min.' means Estimated Time to READ this blog post (reading time, "
            "computed deterministically from word count). It is NOT travel/driving time. "
            "The value is locked -- do NOT flag it as unrealistic and do NOT ask to change it.\n"
            + _VERDICT_SHAPE
        )
        user = "Length: " + str(len(_plain(output).strip())) + " chars\n\nDescription:\n" + output
        return system, user

    return GenerativeNode(
        id="step2f_search_description", label="Step 2-F - Search description",
        build_writer_prompt=writer, deterministic_check=description_deterministic_check,
        build_review_prompt=review, web_search=False,
        writer_max_tokens=200, review_max_tokens=1000, temperature=0.1,
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
        build_writer_prompt=writer, deterministic_check=prose_paragraph_check(120),
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


# ---------------------------------------------------------------------------
# Step 3 -- summary block content (label + narrative + one row per H2)
# ---------------------------------------------------------------------------
def step3_summary_block() -> GenerativeNode:
    def writer(context, prior, revision):
        sections = context.get("sections", [])
        system = (
            "You write the TEXT content of a pre-fold summary block: (1) a small-caps label "
            "'[POST TITLE] - Post Summary'; (2) ONE narrative paragraph in the author's voice "
            "describing the full route arc; (3) one 'What's Covered' table row per top-level "
            "H2 section (emoji + 'Section name - brief descriptor'). "
            "NARRATOR IS 'The Vagabond Couple': use ONLY 'we'/'us'/'our'; NEVER write the "
            "word 'I' or 'me' anywhere. No forbidden words. Output as: a LABEL: line, a "
            "NARRATIVE: paragraph, then ROWS: one 'emoji | Section - descriptor' per line. "
            "Output EXACTLY one row per section listed below -- no more, no fewer."
        )
        user = ("Post title: " + context.get("post_title", "") +
                "\nRoute: " + context["origin"] + " -> " + context["destination"] +
                "\nTop-level H2 sections (" + str(len(sections)) + " rows, one each):\n- " +
                "\n- ".join(sections))
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def deterministic(output, context):
        findings = writing_rules_findings(_plain(output))
        sections = context.get("sections", [])
        rows = [ln for ln in output.splitlines() if "|" in ln or " - " in ln]
        # soft check: roughly one row per section (reviewer confirms exact match)
        if sections and len(rows) and abs(len(rows) - len(sections)) > 2:
            findings.append("row count " + str(len(rows)) + " far from section count " + str(len(sections)))
        return (len(findings) == 0, findings)

    def review(output, det_findings, context):
        system = (
            "You certify a summary block's text. Certify: (a) FACTS -- narrative matches the "
            "route; (b) WRITING RULES -- narrator we/us, no forbidden words; (d) the table has "
            "EXACTLY one row per top-level H2 section (no phantom/missing rows).\n" + _VERDICT_SHAPE
        )
        user = ("H2 sections:\n- " + "\n- ".join(context.get("sections", [])) +
                "\n\nSummary block content to certify:\n" + output)
        return system, user

    return GenerativeNode(
        id="step3_summary_block", label="Step 3 - Summary block content",
        build_writer_prompt=writer, deterministic_check=deterministic,
        build_review_prompt=review, web_search=False,
        writer_max_tokens=900, review_max_tokens=1536, temperature=0.2,
    )


# ---------------------------------------------------------------------------
# Step 7 -- route summary box (template fill)
# ---------------------------------------------------------------------------
def step7_route_summary_box() -> GenerativeNode:
    def writer(context, prior, revision):
        system = (
            "You fill a route summary box, EXACT template (tvc-route-summary class, no inline "
            "colour styles):\n"
            '<div class="tvc-route-summary"><strong>Route:</strong> [stops]<br />'
            '<strong>Method:</strong> [method]<br />'
            '<strong>Distance / Time:</strong> Approx. [X] km / [Y] days<br />'
            '<strong>Themes:</strong> [theme] - [theme]<br />'
            '<strong>Vehicle:</strong> Shehzadi (2024 Toyota Tundra)</div>\n'
            "Fill the bracketed fields from the context. No forbidden words. Output ONLY the div."
        )
        user = ("Route stops: " + context["origin"] + " -> " + context["destination"] +
                "\nMethod: " + context.get("method", "overland") +
                "\nThemes: " + context.get("landmarks", "") +
                "\nApprox distance/days: " + context.get("distance_time", "(estimate)"))
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def deterministic(output, context):
        findings = writing_rules_findings(_plain(output))
        for label in ("Route:", "Method:", "Vehicle:"):
            if label not in output:
                findings.append("missing '" + label + "' field")
        if "tvc-route-summary" not in output:
            findings.append("missing tvc-route-summary class")
        if re.search(r"style\s*=\s*[\"'][^\"']*(color|background)", output, re.IGNORECASE):
            findings.append("inline colour style present (forbidden on new elements)")
        return (len(findings) == 0, findings)

    def review(output, det_findings, context):
        system = (
            "You certify a route summary box. Certify: (a) FACTS -- route/method/vehicle "
            "accurate; (b) WRITING RULES -- no forbidden words, no field duplicates a fact "
            "stated elsewhere; (d) no redundancy.\n" + _VERDICT_SHAPE
        )
        return system, "Route summary box to certify:\n" + output

    return GenerativeNode(
        id="step7_route_summary_box", label="Step 7 - Route summary box",
        build_writer_prompt=writer, deterministic_check=deterministic,
        build_review_prompt=review, web_search=False,
        writer_max_tokens=400, review_max_tokens=1200,
    )


# ---------------------------------------------------------------------------
# Step 8 -- Route at a Glance (<ol>, one item per stop in travel order)
# ---------------------------------------------------------------------------
def step8_route_at_a_glance() -> GenerativeNode:
    def writer(context, prior, revision):
        items = geographic_stops(context)
        system = (
            "You write a 'Route at a Glance' navigation list: an <h2>Route at a Glance</h2> "
            "followed by an ORDERED list <ol> with EXACTLY one <li> per stop listed below, "
            "IN THE GIVEN ORDER, each with a brief descriptor. These are the geographic stops "
            "along the drive, in travel order. "
            "CRITICAL: use ONLY the stops listed below -- never add, invent, rename, or "
            "substitute any place; every place you name must be one of these. Use <ol>, "
            "never <ul>. No forbidden words. Output ONLY the <h2> and the <ol>."
        )
        user = ("Geographic stops in travel order (use EXACTLY these, one <li> each, no others):\n- "
                + "\n- ".join(items))
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def deterministic(output, context):
        findings = writing_rules_findings(_plain(output))
        if "<ol" not in output.lower():
            findings.append("must use <ol> (ordered list)")
        if "<ul" in output.lower():
            findings.append("uses <ul> -- must be <ol>")
        li_count = output.lower().count("<li")
        if li_count == 0:
            findings.append("no list items")
        items = geographic_stops(context)
        if items and li_count != len(items):
            findings.append("has " + str(li_count) + " list items; must be exactly "
                            + str(len(items)) + " (one per grounded stop)")
        findings += grounded_route_check(output, context, items=items)
        return (len(findings) == 0, findings)

    def review(output, det_findings, context):
        items = geographic_stops(context)
        system = (
            "You certify a Route at a Glance list -- a navigational <ol> of the GEOGRAPHIC "
            "stops along the drive in travel order (one <li> each). The stops are given below "
            "and are the authoritative, grounded route; treat them as correct and real -- do "
            "NOT ask for more specific locations or reject them as non-specific. Certify: "
            "(a) every <li> corresponds to one of the given stops, in order; (b) WRITING RULES "
            "-- <ol> used, no forbidden words; (d) descriptors do not merely restate the Route "
            "Summary box.\n" + _VERDICT_SHAPE
        )
        user = ("Grounded geographic stops in travel order:\n- " + "\n- ".join(items) +
                "\n\nRoute at a Glance to certify:\n" + output)
        return system, user

    return GenerativeNode(
        id="step8_route_at_a_glance", label="Step 8 - Route at a Glance",
        build_writer_prompt=writer, deterministic_check=deterministic,
        build_review_prompt=review, web_search=True,
        writer_max_tokens=700, review_max_tokens=1536,
    )


# ---------------------------------------------------------------------------
# Step 12 -- resolve a flagged repetition / writing-rules violation
# ---------------------------------------------------------------------------
def step12_resolve() -> GenerativeNode:
    def writer(context, prior, revision):
        system = (
            "You resolve ONE flagged issue (a repeated fact or a writing-rules violation) in a "
            "passage. Prefer cutting the redundant instance; otherwise reword distinctly; "
            "otherwise replace with a NEW, verifiable, non-duplicative fact about the same "
            "subject. Preserve the author's voice. Narrator we/us, no forbidden words. Output "
            "ONLY the corrected passage HTML."
        )
        user = ("Flagged issue: " + context.get("issue", "") +
                "\nPassage to fix:\n" + context.get("passage", "") +
                "\nFacts already in the post (do not reintroduce):\n" + context.get("existing_facts", "(none)"))
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify a repetition/rules fix. Use web_search to verify any replacement "
            "fact. Certify: (a) FACTS -- any new fact is verifiable; (b) WRITING RULES clean; "
            "(d) REPETITION -- the original duplication/violation is resolved and no new "
            "duplication introduced.\n" + _VERDICT_SHAPE
        )
        user = ("Original issue: " + context.get("issue", "") +
                "\nFacts already in post:\n" + context.get("existing_facts", "(none)") +
                "\n\nCorrected passage to certify:\n" + output)
        return system, user

    return GenerativeNode(
        id="step12_resolve", label="Step 12 - Resolve repetition / rules violation",
        build_writer_prompt=writer, deterministic_check=standard_deterministic_check,
        build_review_prompt=review, web_search=True,
        writer_max_tokens=800, review_max_tokens=1536,
    )


# Registry of generative nodes.
GENERATIVE_NODES = {
    "step1_title": step1_title,
    "step2f_search_description": step2f_search_description,
    "step3_summary_block": step3_summary_block,
    "step6_first_body_paragraph": step6_first_body_paragraph,
    "step7_route_summary_box": step7_route_summary_box,
    "step8_route_at_a_glance": step8_route_at_a_glance,
    "step9f_factoid": step9f_factoid,
    "step10_journey_significance": step10_journey_significance,
    "step12_resolve": step12_resolve,
    "step13_separator": step13_separator,
}
