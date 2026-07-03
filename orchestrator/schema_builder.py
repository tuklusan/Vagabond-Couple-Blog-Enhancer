#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Deterministic TravelAction ld+json schema generation (Step 4).

The single biggest fix for a "crawled - currently not indexed" post is a valid
TravelAction structured-data block. Old posts usually have none, so we BUILD one
from the extracted context (route + sections) rather than asking the writer model
-- schema is mechanical and must be byte-stable and hallucination-free, so it is
code, not LLM.

The output matches TRAVELACTION-ld_json-SCHEMA-EXAMPLE.txt and the reference
pre-fold: every field in validators.REQUIRED_SCHEMA_FIELDS is present, @type is
TravelAction, and `author` is the constant Vagabond Couple Person.
"""
import json

import re

from bs4 import BeautifulSoup

# The author block is a rev-14 constant across every post (validators.author_ok
# checks it exactly).
AUTHOR = {
    "@type": "Person",
    "name": "The Vagabond Couple",
    "sameAs": "https://thevagabondcouple.blogspot.com/",
}

_SKIP_H2 = {"route at a glance", "next stop", "route summary"}

# US state abbreviations -> full name, for schema place normalization (TICKET-0108).
_US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


def _place_key(name):
    """Dedup key = the leading place token before any comma, lowercased. Collapses
    'Fresno, CA' and 'Fresno' to one entity (TICKET-0104)."""
    return (name or "").split(",")[0].strip().lower()


def _is_state_fragment(name):
    """A bare 2-letter US state code that leaked from splitting 'City, ST'."""
    n = (name or "").strip()
    return len(n) == 2 and n.upper() in _US_STATES


def _full_place_name(name):
    """Expand a trailing 2-letter US state and append USA -- 'Oakhurst, CA' ->
    'Oakhurst, California, USA' (TICKET-0108). Only a place that actually names a
    US state gets 'USA' appended -- a non-US place ('Kyiv, Ukraine') must be left
    alone, not have the wrong country forced onto it (TICKET-0128). Already-full
    names are untouched either way."""
    n = (name or "").strip()
    if not n:
        return n
    parts = [p.strip() for p in n.split(",") if p.strip()]
    is_us_state = len(parts) >= 2 and parts[-1].upper() in _US_STATES
    if is_us_state:
        parts[-1] = _US_STATES[parts[-1].upper()]
    full = ", ".join(parts)
    if is_us_state and not re.search(r"\b(usa|u\.s\.a\.|united states)\b", full, re.IGNORECASE):
        full += ", USA"
    return full


def _instrument(context):
    """Build the Vehicle instrument from a structured context['vehicle'] -- NEVER
    the method verb like 'drove' (TICKET-0103). With no vehicle at all (a non-car
    post -- transit, on foot, a descent), fall back to the extracted travel
    'method' (e.g. 'escalator', 'subway train') rather than the generic 'Overland
    vehicle', which falsely implies a personal vehicle exists (TICKET-0128)."""
    v = context.get("vehicle")
    if isinstance(v, dict) and (v.get("name") or v.get("model")):
        out = {"@type": "Vehicle", "name": v.get("name") or "Overland vehicle"}
        if v.get("manufacturer"):
            out["manufacturer"] = v["manufacturer"]
        if v.get("model"):
            out["model"] = v["model"]
        return out
    if isinstance(v, str) and v.strip():
        return {"@type": "Vehicle", "name": v.strip()}
    method = (context.get("method") or "").strip()
    if method:
        return {"@type": "Vehicle", "name": method[:1].upper() + method[1:]}
    return {"@type": "Vehicle", "name": "Overland vehicle"}


def _tourist_type(context):
    """'Overlander' only fits an actual road-trip post (a real vehicle in
    context). Everything else (urban sights, transit, museums, single-location
    posts) gets a neutral, non-fabricated default (TICKET-0128)."""
    v = context.get("vehicle")
    if v:
        return "Overlander"
    return "Traveler"


def _post_h2_sections(html):
    """Real top-level H2 section names in the (assembled) post body, in order."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for h in soup.find_all("h2"):
        t = h.get_text(strip=True)
        if t and t.lower() not in _SKIP_H2:
            out.append(t)
    return out


# Road designations and attraction suffixes for mining named entities from prose
# (TICKET-0108).
_ROAD_RE = re.compile(
    r"\b(Interstate\s+\d+|I-\d+|Historic\s+Route\s+66|Route\s+66|US-\d+|U\.S\.\s+\d+|"
    r"[A-Z]{2}-\d+|Highway\s+\d+)\b")
_ATTRACTION_RE = re.compile(
    r"\b([A-Z][A-Za-z'&]+(?:\s+[A-Z][A-Za-z'&]+){0,4}\s+"
    r"(?:Resort|National\s+Preserve|National\s+Park|National\s+Forest|State\s+Park|"
    r"Dunes|Monument|Museum|Caverns|Cafe|Railway))\b")


def _section_terms(h2):
    """Distinctive bold/link terms inside an H2 section (its siblings up to the next
    H2). These proper nouns form a compact, POSTED-style fact-list description."""
    out, seen = [], set()
    for sib in h2.next_siblings:
        if getattr(sib, "name", None) == "h2":
            break
        if hasattr(sib, "find_all"):
            for t in sib.find_all(["b", "strong", "a"]):
                txt = t.get_text(" ", strip=True)
                k = txt.lower()
                if txt and 1 < len(txt) < 60 and k not in seen:
                    seen.add(k)
                    out.append(txt)
    return out[:12]


def _mine_roads_and_attractions(html):
    """Return (roads, attractions) proper-noun lists mined from the post prose."""
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    roads, seen_r = [], set()
    for m in _ROAD_RE.finditer(text):
        v = re.sub(r"\s+", " ", m.group(1)).strip()
        if v.lower() not in seen_r:
            seen_r.add(v.lower())
            roads.append(v)
    attractions, seen_a = [], set()
    for m in _ATTRACTION_RE.finditer(text):
        v = re.sub(r"\s+", " ", m.group(1)).strip()
        if v.lower() not in seen_a:
            seen_a.add(v.lower())
            attractions.append(v)
    return roads[:8], attractions[:8]


def _facts_lookup(existing_facts):
    """Map 'Name: description' lines (from context.existing_facts) by lowercased name."""
    lookup = {}
    for line in (existing_facts or "").splitlines():
        if ":" in line:
            name, desc = line.split(":", 1)
            lookup[name.strip().lower()] = desc.strip()
    return lookup


def build_haspart(context, html=""):
    """Assemble the hasPart array from the post's real sections + route entities.

    Sections become Place legs (with a description when we have one from the source
    facts); bare route waypoints/stops/landmarks are appended as named Place/
    TouristAttraction entities. Everything here traces to extracted context -- no
    invented places.
    """
    lookup = _facts_lookup(context.get("existing_facts", ""))
    parts = []
    seen = set()

    # Map H2 element -> its distinctive terms, for section-leg descriptions (0108).
    soup = BeautifulSoup(html, "html.parser") if html else None
    h2_terms = {}
    if soup is not None:
        for h in soup.find_all("h2"):
            t = h.get_text(strip=True)
            if t and t.lower() not in _SKIP_H2:
                h2_terms[t.strip().lower()] = _section_terms(h)

    sections = _post_h2_sections(html) or context.get("sections", []) or []
    for name in sections:
        key = name.strip().lower()
        if not name or key in seen:
            continue
        seen.add(key)
        part = {"@type": "Place", "name": name}
        # description: source facts if we have them, else the section's proper-noun
        # fact list (TICKET-0108).
        desc = lookup.get(key)
        if not desc:
            terms = h2_terms.get(key) or []
            if terms:
                desc = ", ".join(terms)
        if desc:
            part["description"] = desc
        parts.append(part)

    # Bare named entities (waypoints/stops/landmarks). Skip 2-letter state fragments
    # that leaked from splitting 'City, ST', and dedupe by leading place token so
    # 'Fresno, CA' and 'Fresno' collapse to one (TICKET-0104). Waypoints are stored
    # as full 'City, ST' strings; landmarks is a comma-joined string of possibly
    # 'City, ST' pairs, so re-pair split fragments before use.
    landmarks_field = context.get("landmarks", "")
    landmark_list = _rejoin_city_state(landmarks_field) if isinstance(landmarks_field, str) else []
    for name in _as_str_list(context.get("waypoints")) + _as_str_list(context.get("stops")) + landmark_list:
        name = (name or "").strip()
        if not name or _is_state_fragment(name):
            continue
        key = _place_key(name)
        if key in seen:
            continue
        seen.add(key)
        parts.append({"@type": "Place", "name": name})

    # Roads + landmark attractions mined from the prose (TICKET-0108).
    roads, attractions = _mine_roads_and_attractions(html) if html else ([], [])
    for name in attractions:
        key = _place_key(name)
        if key not in seen:
            seen.add(key)
            parts.append({"@type": "TouristAttraction", "name": name})
    for name in roads:
        key = name.strip().lower()
        if key not in seen:
            seen.add(key)
            parts.append({"@type": "Road", "name": name})

    return parts


def _rejoin_city_state(csv):
    """Split a comma-joined string but recombine 'City, ST' pairs so a 2-letter
    state stays attached to its city instead of becoming its own item (TICKET-0104)."""
    toks = [t.strip() for t in csv.split(",") if t.strip()]
    out, i = [], 0
    while i < len(toks):
        if i + 1 < len(toks) and _is_state_fragment(toks[i + 1]):
            out.append(toks[i] + ", " + toks[i + 1])
            i += 2
        else:
            out.append(toks[i])
            i += 1
    return out


def _as_str_list(v):
    """Coerce a context field to a list of non-empty strings. A bare string becomes
    a single-element list (NOT split into characters); None/other -> [] (TICKET-0074)."""
    if isinstance(v, str):
        return [v.strip()] if v.strip() else []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if x and str(x).strip()]
    return []


def _coerce_etr(v):
    """Return a positive int ETR, or 0 if missing/non-numeric (TICKET-0074)."""
    try:
        n = int(v)
        return n if n > 0 else 0
    except (TypeError, ValueError):
        return 0


def _description(context):
    origin = context.get("origin", "") or ""
    dest = context.get("destination", "") or ""
    covers = (context.get("covers", "") or "").strip()
    etr = _coerce_etr(context.get("etr_minutes", 0))
    base = covers or (origin + " to " + dest + ".")
    tail = " ETR: " + str(etr) + " min." if etr else ""
    # Keep the description reasonable; the search description (Step 2-F) is separate.
    return (base[:300].rstrip() + tail).strip()


def build_travelaction_schema(context, html="", indent=2):
    """Return the ld+json TravelAction as a dict (see build_schema_script for HTML)."""
    origin = context.get("origin", "") or ""
    dest = context.get("destination", "") or ""
    # Prefer the certified Step-1 SEO title / Step-2F search description for the
    # schema name/description (keyword-rich) over the bare route (TICKET-0107).
    name = (context.get("schema_name") or context.get("post_title")
            or (origin + " to " + dest))
    description = context.get("schema_description") or _description(context)

    schema = {
        "@context": "https://schema.org",
        "@type": "TravelAction",
        "name": name,
        "description": description,
        "touristType": _tourist_type(context),
        "fromLocation": {"@type": "Place", "name": _full_place_name(origin)},
        "toLocation": {"@type": "Place", "name": _full_place_name(dest)},
        "instrument": _instrument(context),
        "author": dict(AUTHOR),
        "hasPart": build_haspart(context, html),
    }
    return schema


def build_schema_script(context, html="", indent=2):
    """Return the full <script type="application/ld+json"> ... </script> block."""
    schema = build_travelaction_schema(context, html, indent=indent)
    body = json.dumps(schema, ensure_ascii=False, indent=indent)
    # Prevent a value containing '</script>' from closing the tag early (TICKET-0073).
    # In JSON, '<\/' is an equivalent escaping of '</', so parsers still read it as '</'.
    body = body.replace("</", "<\\/")
    return '<script type="application/ld+json">\n' + body + '\n</script>'
