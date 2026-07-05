#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Open-library / academic research retrieval for fact-inserting nodes
(TICKET-0208, user directive: "produce verifiable information from actual
online libraries and academic research papers").

The app's reviewer is permanently web-less (DeepSeek-only), so it cannot
verify world knowledge -- but it CAN verify entailment. This module retrieves
real snippets (Wikipedia REST summaries; OpenAlex academic works with
reconstructed abstracts) for a set of queries; the writer is then constrained
to snippet-supported facts and the reviewer checks each claim against the same
evidence packet. Keyless, free APIs; every fetch goes through the SSRF-safe
redirect-validating getter; every failure degrades to fewer snippets, never an
exception.
"""
from urllib.parse import quote, urlencode

import requests

from .context_extractor import safe_get

USER_AGENT = {"User-Agent": "VagabondCoupleBlogEnhancer/1.0 "
                            "(+https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer; "
                            "fact research)"}
TIMEOUT = 15
SNIPPET_CHARS = 600


def _get_json(url):
    try:
        resp = safe_get(url, timeout=TIMEOUT, headers=USER_AGENT)
        resp.raise_for_status()
        return resp.json()
    except (requests.exceptions.RequestException, ValueError):
        return None


def wikipedia_snippets(query, limit=2):
    """Encyclopedic summaries: REST search -> per-page summary extract."""
    out = []
    data = _get_json("https://en.wikipedia.org/w/rest.php/v1/search/page?"
                     + urlencode({"q": query, "limit": limit}))
    for page in (data or {}).get("pages", [])[:limit]:
        key = page.get("key")
        if not key:
            continue
        summ = _get_json("https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(key))
        extract = (summ or {}).get("extract") or ""
        if extract:
            out.append({"source": "Wikipedia", "title": (summ or {}).get("title") or key,
                        "year": None,
                        "url": "https://en.wikipedia.org/wiki/" + quote(key),
                        "snippet": extract[:SNIPPET_CHARS]})
    return out


def _reconstruct_abstract(inverted):
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the prose."""
    try:
        words = sorted((pos, word) for word, poss in (inverted or {}).items() for pos in poss)
        return " ".join(word for _pos, word in words)
    except Exception:
        return ""


def openalex_snippets(query, limit=2):
    """Academic works (papers/monographs) with reconstructed abstracts."""
    out = []
    data = _get_json("https://api.openalex.org/works?" + urlencode({
        "search": query, "per-page": limit,
        "select": "title,publication_year,doi,abstract_inverted_index"}))
    for work in (data or {}).get("results", [])[:limit]:
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
        title = work.get("title") or ""
        if not title or not abstract:
            continue
        out.append({"source": "OpenAlex (academic)", "title": title,
                    "year": work.get("publication_year"),
                    "url": work.get("doi") or "https://openalex.org",
                    "snippet": abstract[:SNIPPET_CHARS]})
    return out


def research(queries, per_query_wiki=1, per_query_academic=1, max_snippets=6):
    """Gather snippets for a list of queries, deduplicated by title. Best
    effort: an unreachable source just contributes nothing."""
    snippets, seen = [], set()
    for q in queries:
        q = (q or "").strip()
        if not q:
            continue
        for snip in (wikipedia_snippets(q, per_query_wiki)
                     + openalex_snippets(q, per_query_academic)):
            key = snip["title"].lower()
            if key in seen:
                continue
            seen.add(key)
            snippets.append(snip)
            if len(snippets) >= max_snippets:
                return snippets
    return snippets


def format_evidence(snippets):
    """The numbered evidence packet shared verbatim by writer and reviewer."""
    if not snippets:
        return ""
    lines = []
    for i, s in enumerate(snippets, 1):
        year = (" " + str(s["year"])) if s.get("year") else ""
        lines.append("[" + str(i) + "] (" + s["source"] + year + ": " + s["title"] + ") "
                     + s["snippet"] + " <" + s["url"] + ">")
    return "\n".join(lines)
