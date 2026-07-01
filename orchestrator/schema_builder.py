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
    """Expand a trailing 2-letter state and append USA -- 'Oakhurst, CA' ->
    'Oakhurst, California, USA' (TICKET-0108). Leaves already-full names alone."""
    n = (name or "").strip()
    if not n:
        return n
    parts = [p.strip() for p in n.split(",") if p.strip()]
    if len(parts) >= 2 and parts[-1].upper() in _US_STATES:
        parts[-1] = _US_STATES[parts[-1].upper()]
    full = ", ".join(parts)
    if not re.search(r"\b(usa|u\.s\.a\.|united states)\b", full, re.IGNORECASE):
        full += ", USA"
    return full


def _instrument(context):
    """Build the Vehicle instrument from a structured context['vehicle'] -- NEVER
    the method verb like 'drove' (TICKET-0103)."""
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
    return {"@type": "Vehicle", "name": "Overland vehicle"}


def _post_h2_sections(html):
    """Real top-level H2 section names in the (assembled) post body, in order."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for h in soup.find_all("h2"):
        t = h.get_text(strip=True)
        if t and t.lower() not in _SKIP_H2:
            out.append(t)
    return out


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

    sections = _post_h2_sections(html) or context.get("sections", []) or []
    for name in sections:
        key = name.strip().lower()
        if not name or key in seen:
            continue
        seen.add(key)
        part = {"@type": "Place", "name": name}
        desc = lookup.get(key)
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
        "touristType": "Overlander",
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
