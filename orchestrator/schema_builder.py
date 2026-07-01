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

from bs4 import BeautifulSoup

# The author block is a rev-14 constant across every post (validators.author_ok
# checks it exactly).
AUTHOR = {
    "@type": "Person",
    "name": "The Vagabond Couple",
    "sameAs": "https://thevagabondcouple.blogspot.com/",
}

_SKIP_H2 = {"route at a glance", "next stop", "route summary"}


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

    # Bare named entities (waypoints/stops/landmarks) that are not already sections.
    landmarks = context.get("landmarks", "")
    landmark_list = [s.strip() for s in landmarks.split(",")] if landmarks else []
    for name in list(context.get("waypoints", []) or []) + list(context.get("stops", []) or []) + landmark_list:
        key = (name or "").strip().lower()
        if not name or key in seen:
            continue
        seen.add(key)
        parts.append({"@type": "Place", "name": name})

    return parts


def _description(context):
    origin = context.get("origin", "")
    dest = context.get("destination", "")
    covers = (context.get("covers", "") or "").strip()
    etr = context.get("etr_minutes", 0)
    base = covers or (origin + " to " + dest + ".")
    tail = " ETR: " + str(etr) + " min." if etr else ""
    # Keep the description reasonable; the search description (Step 2-F) is separate.
    return (base[:300].rstrip() + tail).strip()


def build_travelaction_schema(context, html="", indent=2):
    """Return the ld+json TravelAction as a dict (see build_schema_script for HTML)."""
    origin = context.get("origin", "") or ""
    dest = context.get("destination", "") or ""
    name = context.get("post_title", "") or (origin + " to " + dest)
    method = context.get("method", "") or "overland"

    schema = {
        "@context": "https://schema.org",
        "@type": "TravelAction",
        "name": name,
        "description": _description(context),
        "touristType": "Overlander",
        "fromLocation": {"@type": "Place", "name": origin},
        "toLocation": {"@type": "Place", "name": dest},
        "instrument": {"@type": "Vehicle", "name": method},
        "author": dict(AUTHOR),
        "hasPart": build_haspart(context, html),
    }
    return schema


def build_schema_script(context, html="", indent=2):
    """Return the full <script type="application/ld+json"> ... </script> block."""
    schema = build_travelaction_schema(context, html, indent=indent)
    body = json.dumps(schema, ensure_ascii=False, indent=indent)
    return '<script type="application/ld+json">\n' + body + '\n</script>'
