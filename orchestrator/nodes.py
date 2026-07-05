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
from .schema_builder import _US_STATES, _CA_PROVINCES


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


def temporal_rule(context, for_reviewer=False):
    """The trip-timeframe grounding clause for every fact-INSERTING node
    (TICKET-0207). The writer/reviewer models are trained AFTER the narrated
    trip and know how events evolved since; a fact that is true today but
    postdates the trip is an anachronism the plain truth check cannot catch
    (operator rule, 2026-07-05). Empty when the post carries no usable dates."""
    tf = (context or {}).get("trip_timeframe") or ""
    if not tf:
        return ""
    if for_reviewer:
        return (" TEMPORAL VALIDITY (part of the FACTS criterion): this post narrates a trip "
                "taken in " + tf + ". FAIL any stated fact that concerns something which "
                "happened, opened, closed, changed, or was measured AFTER " + tf + ", even if "
                "it is true today -- the narrator cannot know it yet (anachronism).")
    return (" TEMPORAL RULE: this post narrates a trip taken in " + tf + ". Every fact you "
            "state must have been true AS OF " + tf + " -- never mention anything that "
            "happened, opened, closed, changed, or was measured after it, even if true today.")


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


def _with_lead_link_check(base_check, ctx_key):
    """Wrap a deterministic check: when context[ctx_key] ('prior_post'/'next_post',
    fetched from an operator-supplied live URL) is present, the output must
    literally link to its real URL. Grounds the lead-in/lead-out in something
    real instead of letting the writer silently drop a supplied link or, worse,
    invent one of its own (TICKET-0132)."""
    def _check(output, context):
        ok, findings = base_check(output, context)
        post = context.get(ctx_key)
        if isinstance(post, dict) and post.get("url") and post["url"] not in output:
            findings.append(
                "a real " + ctx_key.replace("_", " ") + " (" + post["url"] + ") was supplied "
                "but is not linked in the output -- include a genuine <a href='" + post["url"] +
                "'>...</a> reference to it, using its real title")
        return (len(findings) == 0, findings)
    return _check


def _no_real_route(context):
    """True when there is no real two-endpoint route to narrate: origin/
    destination missing or identical. Covers both a genuine single-location post
    AND a context-extraction miss (empty origin/destination) -- either way, any
    '[Origin] to [Destination]'/'Overland via ...' framing must not be forced,
    since a writer with nothing concrete to anchor to will invent a whole
    fictional trip to fill the gap (observed on arsenalna1: an invented
    'Kyiv to Lviv' road trip with a fake corridor name and fake detour --
    TICKET-0127/0129/0131/0133)."""
    origin = (context.get("origin") or "").strip().lower()
    dest = (context.get("destination") or "").strip().lower()
    return (not origin) or (not dest) or origin == dest


def route_items(context):
    """The authoritative, grounded ordered route list for this post.

    Prefer the real H2 sections (the post's actual structure), then schema stops,
    then extracted waypoints. This is the ONLY source of place names a route node
    may use -- the reviewer is DeepSeek-only (no web) and cannot catch invented
    geography, so grounding is enforced here in code (TICKET-0054)."""
    for key in ("sections", "stops", "waypoints"):
        # `if v and ...` filters out None/"" so a None entry can't become a fake
        # "None" stop (hallucinated place, TICKET-0068).
        vals = [str(v).strip() for v in (context.get(key) or []) if v and str(v).strip()]
        if vals:
            return vals
    return []


def geographic_stops(context):
    """Ordered GEOGRAPHIC stops for Route at a Glance (workflow line 356: 'one item
    per named stop or location in travel order' -- places, not thematic sections).
    origin -> waypoints/schema stops -> destination, deduped by leading place name."""
    seq = []
    if context.get("origin"):
        seq.append(str((context.get("origin") or "")).strip())
    seq += [str(v).strip() for v in (context.get("waypoints") or []) if v and str(v).strip()]
    seq += [str(v).strip() for v in (context.get("stops") or []) if v and str(v).strip()]
    if context.get("destination"):
        seq.append(str((context.get("destination") or "")).strip())
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
        prior_post = context.get("prior_post")
        prior_post = prior_post if isinstance(prior_post, dict) and prior_post.get("url") else None
        no_route = _no_real_route(context)
        subject = (context.get("post_title") or (context.get("sections") or [""])[0]
                   or "the subject of this post")
        shape = (
            # No real origin/destination -- NEVER let the writer invent a drive to fill
            # the gap (observed: a fully fictional 'Kyiv to Lviv' road trip with a fake
            # corridor and a fake detour, TICKET-0133). Ground on the real subject only.
            "There is no real point-to-point route here (a single-location post, or route "
            "extraction found nothing) -- do NOT invent an origin, destination, drive, or "
            "corridor to fill this gap. Open with the REAL subject instead ('" + subject +
            "'). Shape:\n[One sentence establishing what/where this post is actually about, "
            "using ONLY the given subject/sections/landmarks below -- no invented place "
            "names, route, or method]. [one sentence on what made this notable]. [one "
            "sentence on what this post covers]."
            if no_route else
            "HARD RULE: origin, destination, and primary route method must appear before "
            "any atmosphere or character. Shape:\n"
            "We drove from [ORIGIN] to [DESTINATION] via [KEY WAYPOINTS / METHOD]. "
            "[one sentence on what made this stretch notable]. "
            "[one sentence on what this post covers]."
        )
        system = (
            "You are a travel-blog editor for The Vagabond Couple. Narrator is 'we'/'us' "
            "(NEVER 'I'/'me'). Write ONLY the FIRST body paragraph that appears below the "
            "fold. " + shape + "\n"
            "Output ONLY the paragraph wrapped in a single <p>...</p>. No preamble. "
            "Avoid all marketing/transition cliche words." + (
                " A PRIOR post in this series is given below (real title/URL/gist, already "
                "fetched) -- open with a genuine one-clause lead-in referencing it BEFORE the "
                "rest of the paragraph (e.g. 'As promised in our [Prior Title] post, ...'), "
                "with a real <a href='" + prior_post["url"] + "'>" + (prior_post.get("title") or "link")
                + "</a> link. Base the reference ONLY on the real title/gist given -- never "
                "invent what the prior post covered."
                if prior_post else ""
            )
        )
        user = (
            "Origin: " + (context.get("origin") or "") + "\n"
            "Destination: " + (context.get("destination") or "") + "\n"
            "Waypoints: " + ", ".join(context.get("waypoints", [])) + "\n"
            "Method: " + (context.get("method") or "overland") + "\n"
            "Known sections/subject (ground the paragraph in these if there's no route): " +
            ("; ".join(context.get("sections") or []) or subject) + "\n"
            "What this post covers: " + (context.get("covers") or "")
        )
        if prior_post:
            user += ("\n\nPrior post (for the lead-in): title='" + (prior_post.get("title") or "") +
                     "', url='" + prior_post["url"] + "', gist='" + (prior_post.get("gist") or "") + "'")
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        prior_post = context.get("prior_post")
        prior_post = prior_post if isinstance(prior_post, dict) and prior_post.get("url") else None
        no_route = _no_real_route(context)
        system = (
            "You certify a travel blog's FIRST body paragraph. Use web_search to confirm "
            "the named places and the stated route method are real and plausible. Certify "
            "against: (a) FACTS -- " + (
                "there is no real route here, so do NOT require an origin/destination/drive "
                "-- instead verify the paragraph's subject matches the known sections/subject "
                "given below and invents no place, route, or method"
                if no_route else
                "origin, destination and route method accurate and named"
            ) + (
                "; the lead-in reference to the prior post must match its real title/gist "
                "given below, not an invented summary"
                if prior_post else ""
            ) + "; (b) WRITING RULES -- narrator we/us, route-first order, no forbidden words; "
            "(d) REPETITION -- no idea repeated within the paragraph.\n" + _VERDICT_SHAPE
        )
        user = (
            "Route context: " + json.dumps(
                {k: context.get(k) for k in ("origin", "destination", "waypoints", "method")},
                ensure_ascii=False) +
            ("\n\nPrior post (real): " + json.dumps(prior_post, ensure_ascii=False) if prior_post else "") +
            "\n\nParagraph to certify:\n" + output
        )
        return system, user

    return GenerativeNode(
        id="step6_first_body_paragraph",
        label="Step 6 - First body paragraph (route-first)",
        build_writer_prompt=writer,
        deterministic_check=_with_lead_link_check(prose_paragraph_check(120), "prior_post"),
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
            + temporal_rule(context)
        )
        user = (
            "Section topic: " + (context.get("section_topic") or "") + "\n"
            "Place/object/event: " + (context.get("subject") or "") + "\n"
            "Already-covered facts to AVOID duplicating:\n" + (context.get("existing_facts") or "(none)")
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
            "true, OR explicitly framed as folklore/legend/disputed if not settled;"
            + temporal_rule(context, for_reviewer=True) +
            " (b) WRITING RULES -- narrator we/us, no forbidden words, no contrast framing; "
            "(d) REPETITION -- the fact is not already in the post.\n" + _VERDICT_SHAPE +
            "\nNever CERTIFY an unframed claim you cannot verify -- REVISE (add framing or "
            "swap to a verifiable fact) or ESCALATE."
        )
        user = (
            "Section: " + (context.get("section_topic") or "") +
            "\nAlready-covered facts:\n" + (context.get("existing_facts") or "(none)") +
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
    # TICKET-0127: a "via X" clause must name a REAL waypoint grounded in the
    # extracted context, never an invented place. Seen on the Arsenalna run: with
    # no waypoints available the writer fabricated "via Chernihiv" (a real city,
    # but never mentioned anywhere in the source) and the web-less reviewer
    # certified it as fact. Catch this deterministically -- title-case terms
    # after "via" must appear in the known origin/destination/waypoints/landmarks.
    m = re.search(r"\bvia\s+(.+)$", t, re.IGNORECASE)
    if m:
        # A trailing region name is legitimate shared-suffix usage ('... via X,
        # Y, and Z, Alaska' -- the TICKET-0176 recommended form), so the full
        # state/province names for any 2-letter codes present in the context
        # count as known, not fabricated waypoints.
        codes = re.findall(r",\s([A-Z]{2})\b", " ".join([
            context.get("origin") or "", context.get("destination") or "",
            " ".join(context.get("waypoints") or [])]))
        region_names = " ".join((_US_STATES.get(c) or _CA_PROVINCES.get(c) or "")
                                for c in codes)
        known = " ".join([
            context.get("origin") or "", context.get("destination") or "",
            " ".join(context.get("waypoints") or []), context.get("landmarks") or "",
            context.get("post_title") or "", region_names,
        ]).lower()
        dest = (context.get("destination") or context.get("origin") or "the destination")
        for term in re.split(r",| and ", m.group(1)):
            term = term.strip(" .")
            if term and term[0].isupper() and term.lower() not in known:
                findings.append(
                    "waypoint '" + term + "' in the title is not present in the extracted "
                    "origin/destination/waypoints/landmarks -- this is a FABRICATION, do not "
                    "invent any other place name to replace it either. Output EXACTLY this "
                    "format instead: '" + dest + ": <2-6 word real theme from the post subject "
                    "or Known high-value landmarks>' -- no 'Overland via' clause at all.")
    # TICKET-0176: stacked state/province suffixes read as keyword-stuffing
    # (seen live: '... via Ketchikan, AK, Glacier Bay, AK, and Denali National
    # Park, AK'). State the shared region ONCE, on the last term.
    suffixes = re.findall(r",\s([A-Z]{2})\b", t)
    for code in set(suffixes):
        if suffixes.count(code) >= 2:
            findings.append("state/province suffix ', " + code + "' appears "
                            + str(suffixes.count(code)) + "x -- name the shared region once, "
                            "after the LAST waypoint only (e.g. '... via Ketchikan, Glacier "
                            "Bay, and Denali National Park, Alaska')")
    # TICKET-0176: 'Overland' is wrong for a journey that is partly by sea
    # (context method like 'sailed and drove' -- the hybrid-journey assumption
    # problem again, same family as TICKET-0155).
    method = (context.get("method") or "").lower()
    if "overland" in t.lower() and any(w in method for w in ("sail", "cruise", "boat", "ferr", "ship")):
        findings.append("title says 'Overland' but the journey method is '"
                        + context.get("method", "") + "' -- use a mode-accurate phrase "
                        "instead (e.g. 'Cruise & Road Trip' or 'by Sea and Road')")
    return (len(findings) == 0, findings)


def _journey_mode_phrase(method):
    """Deterministic journey word for the title format, from the extracted
    method (TICKET-0203). The old prompt HARD-CODED 'Overland' in its default
    format while a separate sentence said not to use 'Overland' on sea
    journeys -- observed live (alaska3v1): the writer anchored to the template
    word for 6 straight rounds against the deterministic check and escalated.
    Pick the word in code so the prompt never argues with itself."""
    m = (method or "").lower()
    sea = any(w in m for w in ("sail", "cruise", "boat", "ferr", "ship"))
    land = any(w in m for w in ("driv", "drove", "car", "road", "overland", "bus", "train"))
    if sea and land:
        return "Cruise & Road Trip"
    if sea:
        return "Cruise"
    return "Overland"


def step1_title() -> GenerativeNode:
    def writer(context, prior, revision):
        origin = context.get("origin") or ""
        dest = context.get("destination") or ""
        single_location = _no_real_route(context)
        subject = dest or origin or context.get("post_title") or "the post"
        mode = _journey_mode_phrase(context.get("method"))
        system = (
            "You write ONE SEO-optimized blog post title. Default format: "
            "'[Origin] to [Destination] " + mode + " via [waypoints or themes]'. "
            "Use EXACTLY the journey phrase '" + mode + "' -- do not substitute "
            "another travel word. The title "
            "must carry the highest-value search keywords (place names, landmarks, route "
            "terms a real searcher types). Default cap THREE waypoints; exceed only if each "
            "extra term is independently high-search-value. NEVER invent a waypoint, detour, "
            "or place name that is not given to you below." + (
                " There is no real two-endpoint route here (origin/destination missing or "
                "identical -- a single-location post: an urban sight, a descent, a museum, "
                "NOT a multi-town overland trip): do NOT use 'Overland via ...' or '[Origin] "
                "to [Destination]' at all, even if a 'waypoint' below is just an interior "
                "landmark (e.g. a lobby/room), not a separate place. Use this format instead: "
                "'" + subject + ": [2-6 word real theme/subject]'."
                if single_location else ""
            ) + " A 2-letter state/province code (', AK', ', BC') may appear AT MOST ONCE in "
            "the whole title; when the destination already carries it, do NOT repeat it on "
            "any waypoint -- instead write the full region name once after the LAST waypoint "
            "(e.g. '... via Ketchikan, Glacier Bay, and Denali National Park, Alaska'). "
            "NO emoji, NO parentheticals, NO business brand names, no forbidden words. "
            "Output ONLY the title text on one line."
        )
        user = (
            "Origin: " + origin + "\nDestination: " + dest +
            "\nWaypoints/themes available: " + ", ".join(context.get("waypoints", [])) +
            "\nKnown high-value landmarks: " + (context.get("landmarks") or "") +
            "\nJourney method: " + (context.get("method") or "unknown")
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        single_location = _no_real_route(context)
        mode = _journey_mode_phrase(context.get("method"))
        system = (
            "You certify a travel-blog SEO title. Use web_search to gauge whether the place "
            "names are real and which terms have genuine search value. Certify: (a) FACTS -- "
            "every place/waypoint named in the title is real, correctly spelled, AND appears "
            "in the 'Route' context given below (origin/destination/waypoints) -- a real place "
            "that is simply ABSENT from that context is a FABRICATION and must FAIL, even if "
            "the place itself genuinely exists; (b) WRITING RULES -- " + (
                "there is NO real two-endpoint route here (origin/destination missing or "
                "identical), so the '[Origin] to [Destination] ... via ...' format does "
                "NOT apply -- do not fail the title merely for lacking an origin/destination/"
                "journey clause; instead require format '[Subject]: [theme]'."
                if single_location else
                "format '[Origin] to [Destination] " + mode + " via ...' (the journey phrase "
                "'" + mode + "' is mode-accurate for this trip -- do not demand a different "
                "travel word)"
            ) + ", no emoji/parenthetical/brand/forbidden words, "
            "waypoints justified by keyword value; (d) no redundant terms. If you find a "
            "problem with a waypoint, your revision_instructions must NEVER suggest a "
            "replacement place name of your own (e.g. 'try via Brovary instead') -- that is "
            "you fabricating content, exactly what this check exists to prevent. The only "
            "valid revision instruction for a bad/missing waypoint is to drop the 'via ...' "
            "clause and title on the real subject instead.\n" + _VERDICT_SHAPE
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
            "Origin: " + (context.get("origin") or "") + "\nDestination: " + (context.get("destination") or "") +
            "\nThemes/landmarks: " + (context.get("landmarks") or "") +
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
        next_post = context.get("next_post")
        next_post = next_post if isinstance(next_post, dict) and next_post.get("url") else None
        no_route = _no_real_route(context)
        thesis = (
            # No real route to connect to a "wider expedition" -- that framing is
            # exactly what invented a fake "Georgian stretch of our overland route"
            # full of fabricated Silk Road imagery on arsenalna1 (TICKET-0133).
            "You write ONE closing-thought paragraph that reflects on THIS post's real "
            "subject/sections (given below) -- do NOT connect it to a wider overland "
            "expedition or invent a route/journey that doesn't exist here."
            if no_route else
            "You write ONE 'journey significance' paragraph that connects this post's stops "
            "to the wider overland expedition (Silk Road context where relevant)."
        )
        system = (
            thesis + " Give the post a thesis beyond individual stops. Narrator we/us, no "
            "forbidden words, no 'X is not just a Y' framing, no 'we learned/realized "
            "that'." + (
                " A NEXT post in this series is given below (real title/URL/gist, already "
                "fetched) -- end this paragraph with a genuine lead-out sentence to it (e.g. "
                "'From here, our travels carried us onward to [Next Title].'), with a real "
                "<a href='" + next_post["url"] + "'>" + (next_post.get("title") or "link") +
                "</a> link. Base the reference ONLY on the real title/gist given below -- "
                "never invent what the next post covers, and do not drift into abstract/"
                "philosophical language to fill space; keep the lead-out concrete."
                if next_post else ""
            ) + temporal_rule(context) + " Output ONLY a single <p>...</p>."
        )
        user = (
            "Post route: " + (context.get("origin") or "") + " -> " + (context.get("destination") or "") +
            "\nThemes/sections: " + ((context.get("landmarks") or "") or "; ".join(context.get("sections") or [])) +
            "\nFacts already in the post (do not repeat):\n" + (context.get("existing_facts") or "(none)")
        )
        if next_post:
            user += ("\n\nNext post (for the lead-out): title='" + (next_post.get("title") or "") +
                     "', url='" + next_post["url"] + "', gist='" + (next_post.get("gist") or "") + "'")
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        next_post = context.get("next_post")
        next_post = next_post if isinstance(next_post, dict) and next_post.get("url") else None
        no_route = _no_real_route(context)
        system = (
            "You certify a journey-significance paragraph. Use web_search to verify any "
            "historical/geographic claim (e.g. Silk Road links). Certify: (a) FACTS accurate"
            + temporal_rule(context, for_reviewer=True) + (
                "; there is no real route/wider-expedition connection here, so the paragraph "
                "must NOT invent one (e.g. a fabricated route, region, or historical-trade "
                "theme not grounded in this post's real subject/sections) -- FAIL if it does"
                if no_route else ""
            ) + (
                "; the lead-out reference to the next post must match its real title/gist "
                "given below, not an invented summary"
                if next_post else ""
            ) + "; (b) WRITING RULES -- narrator we/us, no forbidden words, no contrast framing; "
            "(d) REPETITION -- introduces no fact already in the post.\n" + _VERDICT_SHAPE
        )
        user = ("Facts already in post:\n" + (context.get("existing_facts") or "(none)") +
                ("\n\nNext post (real): " + json.dumps(next_post, ensure_ascii=False) if next_post else "") +
                "\n\nParagraph to certify:\n" + output)
        return system, user

    return GenerativeNode(
        id="step10_journey_significance", label="Step 10 - Journey significance",
        build_writer_prompt=writer,
        deterministic_check=_with_lead_link_check(prose_paragraph_check(120), "next_post"),
        build_review_prompt=review, web_search=True,
        writer_max_tokens=600, review_max_tokens=1536,
    )


# ---------------------------------------------------------------------------
# Step 13 -- image separator paragraph (facts-critical, non-repetitive)
# ---------------------------------------------------------------------------
def step13_separator() -> GenerativeNode:
    def writer(context, prior, revision):
        evidence = context.get("evidence") or ""
        system = (
            "You write ONE separator paragraph (2-4 sentences) to sit between two adjacent "
            "photos. It must add genuine, factual information about what the photos show -- "
            "history, construction, cultural significance, or sensory reality -- NOT restate "
            "anything already in the post. " + (
                "RESEARCH SNIPPETS from real library/academic sources are given below: every "
                "factual claim you make MUST be directly supported by one of the numbered "
                "snippets (paraphrase them; no [n] markers in the output prose). You may also "
                "plainly describe what the photos visibly show. Do NOT add any fact from "
                "memory that the snippets do not support."
                if evidence else
                "PREFER well-established, widely-documented facts (the kind found in any "
                "guidebook) over obscure specifics -- a modest verifiable fact beats an "
                "impressive unverifiable one."
            ) + " Narrator we/us where natural; no forbidden words, no category-colon "
            "openers. Output ONLY a single <p>...</p>."
            + temporal_rule(context)
        )
        user = (
            "Between photos of: " + (context.get("subject") or "") +
            ("\nVisible in the photos: " + context["visible"] if context.get("visible") else "") +
            "\nSection: " + (context.get("section_topic") or "") +
            ("\n\nRESEARCH SNIPPETS (your ONLY permitted fact sources):\n" + evidence
             if evidence else "") +
            "\nFacts already in the post (do not repeat):\n" + (context.get("existing_facts") or "(none)")
        )
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        evidence = context.get("evidence") or ""
        system = (
            "You certify an image-separator paragraph. Certify: (a) " + (
                "EVIDENCE ENTAILMENT -- every factual claim in the paragraph must be "
                "directly supported by one of the numbered RESEARCH SNIPPETS given below "
                "(or be a plain description of the stated visible photo content). FAIL any "
                "claim the snippets do not support, even if you believe it is true -- the "
                "snippets are the only admissible sources;"
                if evidence else
                "FACTS verifiable (use web_search to verify);"
            )
            + temporal_rule(context, for_reviewer=True) +
            " (b) WRITING RULES -- narrator we/us, no "
            "forbidden words, no label openers; (d) REPETITION -- adds nothing already in the "
            "post.\n" + _VERDICT_SHAPE +
            "\nNever CERTIFY an unsupported factual claim -- REVISE or ESCALATE. When a "
            "claim is unsupported but the evidence contains usable facts, prefer REVISE "
            "steering the writer to the supported facts over ESCALATE."
        )
        user = (("RESEARCH SNIPPETS (the only admissible sources):\n" + evidence +
                 ("\nVisible in the photos: " + context["visible"] if context.get("visible") else "")
                 + "\n\n") if evidence else "") + \
               ("Facts already in post:\n" + (context.get("existing_facts") or "(none)") +
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
            "in the form '<Post title> - Post Summary' using the ACTUAL post title given below "
            "(do NOT write the literal words 'POST TITLE' or any bracketed placeholder); "
            "(2) ONE narrative paragraph in the author's voice describing the full route arc; "
            "(3) one 'What's Covered' table row per top-level H2 section (emoji + "
            "'Section name - brief descriptor'). "
            "NARRATOR IS 'The Vagabond Couple': use ONLY 'we'/'us'/'our'; NEVER write the "
            "word 'I' or 'me' anywhere. No forbidden words. Output as: a LABEL: line, a "
            "NARRATIVE: paragraph, then ROWS: one 'emoji | Section - descriptor' per line. "
            "Every row MUST be complete (section name, ' - ', then a descriptor); never cut a "
            "row off. Output EXACTLY one row per section listed below -- no more, no fewer."
        )
        user = ("Post title: " + (context.get("post_title") or "") +
                "\nRoute: " + (context.get("origin") or "") + " -> " + (context.get("destination") or "") +
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
        # completeness: each row must have a descriptor after the section name and be
        # a full line -- catches a truncated final row like 'A Luxurious' when the
        # writer was cut off by max_tokens (TICKET-0121).
        for r in rows:
            descriptor = r.split("|", 1)[-1].strip() if "|" in r else r
            if " - " not in descriptor and " — " not in descriptor:
                findings.append("incomplete/truncated summary row (no descriptor): '"
                                + descriptor[:40] + "'")
                break
        # the writer must SUBSTITUTE the title, not echo the '[POST TITLE]' placeholder
        if "[post title]" in output.lower() or "post title]" in output.lower():
            findings.append("literal '[POST TITLE]' placeholder not substituted")
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
        # 900/1536 was tuned against posts with ~6-14 sections. A post with many
        # more sections (observed: 17, the alaska-cruise post) needs a full label
        # + narrative + one complete row per section in a single completion --
        # the writer kept truncating well short of all rows at the old budget
        # (TICKET-0156). Bumped generously so row count scales with real posts.
        writer_max_tokens=2200, review_max_tokens=2400, temperature=0.2,
    )


# ---------------------------------------------------------------------------
# Step 7 -- route summary box (template fill)
# ---------------------------------------------------------------------------
def step7_route_summary_box() -> GenerativeNode:
    def _last_label(context):
        """'Vehicle:' only makes sense when a real personal vehicle is in context
        (a road trip). Everything else (transit, on foot, a descent) gets the
        neutral 'Transit:' label -- matching how the human workflow labels a
        non-road-trip post -- instead of forcing a vehicle that doesn't exist
        (TICKET-0129)."""
        return "Vehicle:" if context.get("vehicle") else "Transit:"

    def writer(context, prior, revision):
        stops = geographic_stops(context)
        route_chain = " &rarr; ".join(stops) if stops else (
            (context.get("origin") or "") + " &rarr; " + (context.get("destination") or ""))
        last_label = _last_label(context)
        system = (
            "You fill a route summary box, EXACT template (tvc-route-summary class, no inline "
            "colour styles):\n"
            '<div class="tvc-route-summary"><strong>Route:</strong> [full stop chain]<br />'
            '<strong>Method:</strong> [how they travelled, name the roads]<br />'
            '<strong>Themes:</strong> [2-4 topical themes joined by ·]<br />'
            '<strong>' + last_label + '</strong> [' +
            ('vehicle' if last_label == "Vehicle:" else 'how they got around -- transit line, on foot, etc.') +
            ']</div>\n'
            "RULES: Route = the FULL stop chain given below with &rarr; between stops (do "
            "NOT shorten to just the endpoints). Themes are TOPICS (e.g. 'Route 66', 'Punjabi "
            "dhaba road food', 'desert geology') inferred from the section titles -- NOT a list "
            "of the stops/towns. Include a 'Distance / Time:' line ONLY if a real figure is "
            "given below; otherwise OMIT that line -- NEVER invent a distance or duration. Use "
            "the EXACT last-field label '" + last_label + "' given above -- do not substitute "
            "a different label." + (
                " Method and Transit must say DIFFERENT things: Method is the physical "
                "movement/mechanism (e.g. 'two-stage escalator descent'), Transit is the named "
                "system/operator (e.g. 'Kyiv Metro'). If they would be identical, OMIT the "
                "Transit line entirely rather than repeat Method verbatim."
                if last_label == "Transit:" else ""
            ) + " No forbidden words. Output ONLY the div."
        )
        vehicle = context.get("vehicle") or {}
        if isinstance(vehicle, dict) and vehicle.get("name"):
            veh = vehicle["name"] + (
                " (" + " ".join(x for x in (vehicle.get("manufacturer"), vehicle.get("model")) if x) + ")"
                if vehicle.get("model") else "")
        elif vehicle:
            veh = str(vehicle)
        else:
            veh = context.get("method") or "on foot"
        user = ("Full stop chain (use ALL, in order): " + route_chain +
                "\nMethod: " + (context.get("method") or "overland") +
                "\nSection titles (infer themes from these): " + "; ".join(context.get("sections") or []) +
                "\n" + last_label[:-1] + ": " + veh +
                "\nReal distance/time (blank = omit the line): " + (context.get("distance_time") or ""))
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def deterministic(output, context):
        findings = writing_rules_findings(_plain(output))
        required = ["Route:", "Method:"]
        # 'Vehicle:' is mandatory (a real vehicle is genuinely new information).
        # 'Transit:' is advisory only -- when there's no vehicle, Method may
        # already say everything worth saying, and forcing a redundant Transit
        # line just fights the reviewer's own no-redundancy criterion (0129).
        if context.get("vehicle"):
            required.append("Vehicle:")
        for label in required:
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
            "You resolve ONE flagged issue in a passage: a repeated fact/phrase, a "
            "writing-rules violation, or WHIPLASH (the passage jumps back to an earlier "
            "waypoint/timeline point after the narrative already moved on, with no flashback "
            "framing). For repetition: prefer cutting the redundant instance; otherwise reword "
            "distinctly; otherwise replace with a NEW, verifiable, non-duplicative fact about "
            "the same subject. For whiplash: reorder or reframe so the passage reads as a "
            "single forward pass through the timeline/route (add explicit flashback framing "
            "only if the backward reference is truly necessary). Preserve the author's voice, "
            "every existing <a href> in the passage VERBATIM (same href and link text), and any "
            "genuinely new/kept fact must remain verifiable. Narrator we/us, no forbidden "
            "words. Output ONLY the corrected passage HTML." + temporal_rule(context)
        )
        user = ("Flagged issue: " + context.get("issue", "") +
                "\nPassage to fix:\n" + context.get("passage", "") +
                "\nFacts already in the post (do not reintroduce):\n" + (context.get("existing_facts") or "(none)"))
        if prior:
            user += "\n\nYour previous draft:\n" + prior
        if revision:
            user += "\n\n" + revision
        return system, user

    def review(output, det_findings, context):
        system = (
            "You certify a repetition/rules/whiplash fix. Use web_search to verify any "
            "replacement fact. Certify: (a) FACTS -- any new fact is verifiable;"
            + temporal_rule(context, for_reviewer=True) + " (b) WRITING "
            "RULES clean; (d) REPETITION/WHIPLASH -- the original duplication, violation, or "
            "backward timeline/route jump is resolved, no new duplication or oscillation "
            "introduced, and every original <a href> in the passage is still present "
            "verbatim.\n" + _VERDICT_SHAPE
        )
        user = ("Original issue: " + context.get("issue", "") +
                "\nFacts already in post:\n" + (context.get("existing_facts") or "(none)") +
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
