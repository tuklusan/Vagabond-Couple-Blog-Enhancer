#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Source-context extraction (deterministic, no LLM).

Derives the generative-node context from the source post itself -- primarily its
existing TravelAction ld+json (fromLocation/toLocation/hasPart/instrument) and its
H2 structure -- so a raw old post can be fed in and the orchestrator knows the
route, sections, stops, and landmarks without any operator data entry.
"""
import json

from bs4 import BeautifulSoup

from . import validators


import re

_VEHICLE_MAKES = ("Toyota", "Ford", "Jeep", "Chevrolet|Chevy", "GMC", "Ram|Dodge",
                  "Nissan", "Honda", "Subaru", "Land Rover", "Range Rover",
                  "Mercedes", "BMW", "Tesla", "Volkswagen|VW", "Mitsubishi")


def extract_vehicle(html):
    """Best-effort structured vehicle from the prose, e.g. 'Shehzadi (our trusty
    Toyota Tundra)' -> {name, manufacturer, model}. Empty dict if none (TICKET-0103)."""
    from . import validators
    text = validators.plain_text(html)
    makes = "|".join(_VEHICLE_MAKES)
    # A capitalized/named vehicle followed by a parenthetical make+model.
    m = re.search(
        r"([A-Z][A-Za-z']+)\s*\([^)]*?(?:(\d{4})\s+)?(" + makes + r")\s+([A-Z][A-Za-z0-9-]+)",
        text)
    if m:
        make = m.group(3).split("|")[0]
        return {"name": m.group(1), "manufacturer": make, "model": m.group(4)}
    # Bare 'Make Model' with no nickname.
    m = re.search(r"\b(" + makes + r")\s+([A-Z][A-Za-z0-9-]+)\b", text)
    if m:
        make = m.group(1).split("|")[0]
        return {"name": make + " " + m.group(2), "manufacturer": make, "model": m.group(2)}
    return {}


def _schema_name(value):
    """Extract a place/instrument name from an ld+json value that may be a dict
    ({"name": ...}) OR a plain string per Schema.org (TICKET-0009)."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return (value.get("name", "") or "").strip()
    return ""


def parse_schema(html):
    soup = BeautifulSoup(html, "html.parser")
    s = soup.find("script", attrs={"type": "application/ld+json"})
    if not s or not s.string:
        return {}
    try:
        data = json.loads(s.string.strip())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _summary_row_sections(html):
    """Fallback sections: descriptor phrases from the summary block 'What's Covered' table."""
    soup = BeautifulSoup(html, "html.parser")
    for p in soup.find_all("p"):
        if "Post Summary" in (p.get_text() or ""):
            block = p.find_parent("div")
            if not block:
                return []
            tbl = block.find("table")
            if not tbl:
                return []
            out = []
            for tr in tbl.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    right = tds[1].get_text(" ", strip=True)
                    if right and "covered" not in tds[0].get_text(strip=True).lower():
                        # use the part before an em/en dash as the section name
                        name = right.split(" - ")[0].split(" — ")[0].strip()
                        out.append(name or right)
            return out
    return []


def derive_route_from_prose(html, max_chars=9000):
    """When the post has no schema, derive the route from the prose via the
    writer model. Returns {origin, destination, waypoints, method} (best effort)."""
    import json as _json
    from . import validators, writer_client
    text = validators.plain_text(html)[:max_chars]
    # No example JSON in the prompt (weak models echo examples). Route to DeepSeek
    # directly -- it is reliable for this structured extraction.
    system = (
        "You are a travel-route extractor. Read the blog post and output ONLY a compact "
        "JSON object with exactly these keys and real values from the post: "
        "origin (the place THIS post's journey begins, 'City, State'), "
        "destination (where it ends, 'City, State'), "
        "waypoints (array of the notable named stops in between), "
        "method (how they travelled, e.g. 'drove'). "
        "No commentary, no markdown, no code fences -- just the JSON object."
    )
    user = "POST:\n" + text
    try:
        out = writer_client.call_deepseek(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=400)
    except Exception:
        return {}
    if not isinstance(out, str):      # guard against a non-string return (TICKET-0067)
        return {}
    for cand in (out, out[out.find("{"):out.rfind("}") + 1] if "{" in out else ""):
        try:
            obj = _json.loads(cand)
        except Exception:
            continue
        if isinstance(obj, dict) and (str(obj.get("origin", "")).strip() or str(obj.get("destination", "")).strip()):
            return obj
    return {}


def extract_context(html, allow_llm=False):
    soup = BeautifulSoup(html, "html.parser")
    schema = parse_schema(html)
    ctx = {
        "origin": "", "destination": "", "post_title": "", "method": "overland",
        "waypoints": [], "stops": [], "landmarks": "", "covers": "",
        "sections": [], "existing_facts": "", "etr_minutes": 0,
        "vehicle": extract_vehicle(html),   # {name,manufacturer,model} or {} (TICKET-0103)
    }

    if schema:
        ctx["origin"] = _schema_name(schema.get("fromLocation"))
        ctx["destination"] = _schema_name(schema.get("toLocation"))
        ctx["post_title"] = schema.get("name", "") or ""
        method = _schema_name(schema.get("instrument"))
        if method:
            ctx["method"] = method
        stops, landmarks, waypoints, facts = [], [], [], []
        for part in schema.get("hasPart", []) or []:
            if not isinstance(part, dict):
                continue
            name = part.get("name")
            ptype = part.get("@type")
            desc = part.get("description")
            # Schema.org allows non-string values; only accept string names/descs so
            # string concatenation below can't crash (TICKET-0092).
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(desc, str) or not desc.strip():
                desc = None
            if desc:
                facts.append(name + ": " + desc)
            if ptype == "Place" and desc:
                stops.append(name)            # legs of the journey, in order
            elif ptype == "TouristAttraction":
                landmarks.append(name)
            elif ptype in ("Place", "Mountain", "LakeBodyOfWater", "Road") and not desc:
                waypoints.append(name)        # bare named entities
        ctx["stops"] = stops
        ctx["landmarks"] = ", ".join(landmarks[:8])
        ctx["waypoints"] = (waypoints or stops)[:5]
        ctx["covers"] = (schema.get("description", "") or "")[:220]
        ctx["existing_facts"] = "\n".join(facts[:25])

    # sections: body H2s first, else summary-block descriptors
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]
    sections = [t for t in h2s if t.lower() not in ("route at a glance", "next stop")]
    if not sections:
        sections = _summary_row_sections(html)
    ctx["sections"] = sections

    if not ctx["post_title"]:
        h1 = soup.find("h1")
        ctx["post_title"] = h1.get_text(strip=True) if h1 else ""

    # Schema-less posts: derive the route from the prose (LLM), when permitted.
    # Never let an LLM/import error here crash extraction -- proceed with what we
    # have (TICKET-0093). derive_route_from_prose already guards its own call, but
    # this wraps import errors and any other surprise too.
    if allow_llm and (not ctx["origin"] or not ctx["destination"]):
        try:
            derived = derive_route_from_prose(html)
        except Exception:
            derived = {}
        if derived:
            ctx["origin"] = ctx["origin"] or derived.get("origin", "") or ""
            ctx["destination"] = ctx["destination"] or derived.get("destination", "") or ""
            if not ctx["waypoints"] and derived.get("waypoints"):
                ctx["waypoints"] = derived["waypoints"][:5]
            if ctx["method"] == "overland" and derived.get("method"):
                ctx["method"] = derived["method"]
            if not ctx["landmarks"] and derived.get("waypoints"):
                ctx["landmarks"] = ", ".join(derived["waypoints"][:8])

    ctx["etr_minutes"] = validators.etr_minutes(html)["etr_minutes"]
    return ctx
