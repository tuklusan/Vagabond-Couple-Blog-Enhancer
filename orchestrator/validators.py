#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Deterministic validators -- the reliability core of the orchestrator.

Everything the rev-18 workflow asks for that a computer can verify exactly lives
here (NOT in the LLM): href byte-for-byte diff, literal-`?`/U+FFFD scan, ld+json
validity, ETR word count, <=150-char check, consecutive-image detection,
forbidden-word scan, `<!--more-->` count/position, image<->table counts, and
Route-at-a-Glance <-> H2 correspondence.

Pure functions over an HTML string; all return JSON-serialisable results so they
double as run artifacts and feed Rule G2 Pass 2 (re-derive from source).
"""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, Comment

from . import config

CAPTION_TABLE_CLASS = "tr-caption-container"
PROSE_TAGS = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]
INTERNAL_HOST = "thevagabondcouple.blogspot.com"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def plain_text(html: str) -> str:
    """Visible prose only (excludes tags AND HTML comments)."""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


# ===========================================================================
# Writing-rules term scanning (1I / Phase 5) -- terms LOADED from the file
# ===========================================================================
def load_writing_rules_terms(path=None):
    """
    Parse forbidden Words and Phrases from english-writing-rules_v2.txt.
    Returns (words: list[str], phrases: list[str]). Loaded from the file per
    rev-18 ("do not apply from memory").
    """
    if path is None:
        path = config.resolve_doc("writing_rules")
    words, phrases = [], []
    if not path or not Path(path).exists():
        return words, phrases
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        low = line.lower()
        if "forbidden words" in low and ":" in line:
            rhs = line.split(":", 1)[1]
            for term in rhs.split(","):
                t = term.strip().strip(".").strip()
                if t:
                    words.append(t)
        elif "forbidden phrases" in low and ":" in line:
            rhs = line.split(":", 1)[1]
            quoted = re.findall(r'"([^"]+)"', rhs)
            items = quoted if quoted else [p.strip() for p in rhs.split(",")]
            for ph in items:
                t = ph.strip().strip(".").strip('"').strip()
                t = re.sub(r"\.\.\.$", "", t).strip()
                if t:
                    phrases.append(t)
    return words, phrases


def scan_forbidden(text: str, words=None, phrases=None):
    """Return a list of forbidden-term hits: {term, kind, count}."""
    if words is None or phrases is None:
        w, p = load_writing_rules_terms()
        words = words if words is not None else w
        phrases = phrases if phrases is not None else p
    hits = []
    for word in words:
        n = len(re.findall(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE))
        if n:
            hits.append({"term": word, "kind": "word", "count": n})
    for phrase in phrases:
        n = len(re.findall(re.escape(phrase), text, re.IGNORECASE))
        if n:
            hits.append({"term": phrase, "kind": "phrase", "count": n})
    return hits


# ===========================================================================
# 1G -- character-encoding audit
# ===========================================================================
def scan_question_marks(text: str):
    """
    Flag suspicious literal `?`, runs of 2+, and U+FFFD. A `?` embedded in a
    word/identifier is suspect; a `?` after whitespace/at sentence end is likely
    legitimate punctuation.
    """
    findings = []
    for m in re.finditer(r"\?{2,}", text):
        s = max(0, m.start() - 25)
        findings.append({"type": "multi", "match": m.group(0),
                         "context": text[s:m.end() + 25]})
    # single ? glued to a word character on either side (transliteration corruption)
    for m in re.finditer(r"(?<=\w)\?|\?(?=\w)", text):
        s = max(0, m.start() - 25)
        snippet = text[s:m.end() + 25]
        if "??" in snippet:
            continue  # already captured by the multi rule
        findings.append({"type": "embedded", "pos": m.start(),
                         "context": snippet})
    fffd = text.count("�")
    return {"embedded_or_multi": findings, "ufffd_count": fffd,
            "suspect": bool(findings) or fffd > 0}


# ===========================================================================
# 1C -- media / links / embeds inventory  +  G3 href preservation
# ===========================================================================
def href_inventory(html: str):
    soup = _soup(html)
    items = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        items.append({
            "href": href,
            "kind": "internal" if INTERNAL_HOST in href else "external",
            "rel": a.get("rel"),
            "target": a.get("target"),
            "has_m1": "?m=1" in href,
        })
    return items


def diff_hrefs(before_inventory, after_html):
    """Compare an href inventory (from href_inventory) against output HTML."""
    before = [i["href"] for i in before_inventory]
    after = [i["href"] for i in href_inventory(after_html)]
    bset, aset = set(before), set(after)
    return {
        "removed": sorted(bset - aset),
        "added": sorted(aset - bset),
        "preserved_count": len(bset & aset),
        "ok": bset.issubset(aset),  # every original href still present
    }


def media_inventory(html: str):
    soup = _soup(html)
    tables = soup.find_all("table", class_=lambda c: c and CAPTION_TABLE_CLASS in c)
    images = []
    for img in soup.find_all("img"):
        images.append({"src": img.get("src"), "alt": img.get("alt"),
                       "has_alt": bool(img.get("alt"))})
    youtube, maps, other = [], [], []
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "") or ""
        if "youtube" in src:
            youtube.append(src)
        elif "google.com/maps" in src or "openstreetmap" in src or "/d/" in src:
            maps.append(src)
        else:
            other.append(src)
    hrefs = href_inventory(html)
    return {
        "photographs": len(images),
        "images": images,
        "caption_tables": len(tables),
        "image_table_match": len(images) == len(tables),
        "internal_links": [h for h in hrefs if h["kind"] == "internal"],
        "external_links": [h for h in hrefs if h["kind"] == "external"],
        "youtube_embeds": youtube,
        "map_embeds": maps,
        "other_iframes": other,
    }


def consecutive_image_pairs(html: str):
    """
    Step 13: two tr-caption-container tables adjacent with no intervening <p> of
    prose. Whitespace, empty <p></p>, and .separator divs do NOT separate.
    """
    soup = _soup(html)
    tables = soup.find_all("table", class_=lambda c: c and CAPTION_TABLE_CLASS in c)
    pairs = []
    for idx, tbl in enumerate(tables[:-1]):
        nxt = tables[idx + 1]
        # walk siblings between this table and the next caption table
        separated = False
        node = tbl
        while True:
            node = node.next_sibling
            if node is None or node is nxt:
                break
            name = getattr(node, "name", None)
            if name == "table" and node is nxt:
                break
            if name == "p" and node.get_text(strip=True):
                separated = True
                break
            # a prose <p> nested isn't a sibling here; also check descendants path
        if not separated:
            # confirm the next caption table is actually the immediate next one in doc order
            between = []
            for el in tbl.next_elements:
                if el is nxt:
                    break
                if getattr(el, "name", None) == "p" and el.get_text(strip=True):
                    between.append(el)
            if not between:
                pairs.append({"image_index": idx, "next_index": idx + 1})
    return pairs


# ===========================================================================
# <!--more--> position (Step 5)
# ===========================================================================
def count_more_tags(html: str):
    """
    Locate the canonical <!--more--> (immediately after the ld+json </script>).
    `count` is the raw token count (a real post body has exactly one); the
    canonical-placement check tolerates stray textual mentions so it stays
    meaningful even on documentation fixtures.
    """
    occurrences = [m.start() for m in re.finditer(r"<!--more-->", html)]
    count = len(occurrences)
    after_script = 0
    real_pos = -1
    for pos in occurrences:
        idx = html.rfind("</script>", 0, pos)
        if idx != -1 and html[idx + len("</script>"):pos].strip() == "":
            after_script += 1
            real_pos = pos
    return {
        "count": count,
        "position": real_pos if real_pos != -1 else (occurrences[0] if occurrences else -1),
        "after_script_count": after_script,
        "immediately_after_script": after_script >= 1,
        "canonical_after_script": after_script == 1,
        "ok": count == 1,
    }


# ===========================================================================
# Step 4 -- ld+json TravelAction validity
# ===========================================================================
REQUIRED_SCHEMA_FIELDS = ["@context", "@type", "name", "description",
                          "touristType", "fromLocation", "toLocation",
                          "instrument", "author", "hasPart"]


def validate_ld_json(html: str):
    soup = _soup(html)
    script = soup.find("script", attrs={"type": "application/ld+json"})
    if not script or not script.string:
        return {"present": False, "valid_json": False, "ok": False,
                "missing_fields": REQUIRED_SCHEMA_FIELDS}
    raw = script.string.strip()
    try:
        data = json.loads(raw)
    except Exception as e:
        return {"present": True, "valid_json": False, "error": str(e), "ok": False}
    missing = [f for f in REQUIRED_SCHEMA_FIELDS if f not in data]
    author = data.get("author", {})
    author_ok = (isinstance(author, dict)
                 and author.get("@type") == "Person"
                 and author.get("name") == "The Vagabond Couple"
                 and author.get("sameAs") == "https://thevagabondcouple.blogspot.com/")
    return {
        "present": True, "valid_json": True,
        "type_is_travelaction": data.get("@type") == "TravelAction",
        "missing_fields": missing,
        "author_ok": author_ok,
        "ok": data.get("@type") == "TravelAction" and not missing and author_ok,
    }


# ===========================================================================
# ETR + char count (Step 2 / 2-F)
# ===========================================================================
def _body_below_more(html: str) -> str:
    pos = html.find("<!--more-->")
    return html[pos + len("<!--more-->"):] if pos != -1 else html


def etr_minutes(html: str):
    """Count human-readable words below <!--more--> (exclude ld+json), /238."""
    below = _body_below_more(html)
    soup = _soup(below)
    for s in soup.find_all(["script", "style"]):
        s.decompose()
    text = soup.get_text(separator=" ", strip=True)
    words = len(re.findall(r"\b\w[\w'-]*\b", text))
    minutes = max(1, round(words / 238)) if words else 0
    return {"body_words": words, "etr_minutes": minutes}


def char_count(s: str):
    return {"chars": len(s), "ok_150": len(s) <= 150}


# ===========================================================================
# 1F -- summary block structural presence
# ===========================================================================
def summary_block(html: str):
    soup = _soup(html)
    # the canonical block is a <div> with saddlebrown small-caps label + table
    label = soup.find("p", string=re.compile(r"Post Summary", re.IGNORECASE))
    block = None
    if label:
        block = label.find_parent("div")
    present = block is not None
    rows = 0
    if block:
        tbl = block.find("table")
        if tbl:
            # data rows = rows after the "What's Covered" header row
            trs = tbl.find_all("tr")
            rows = max(0, len(trs) - 1)
    # position: should appear before the ld+json script
    pos_ok = True
    if present:
        script = soup.find("script", attrs={"type": "application/ld+json"})
        if script:
            pos_ok = html.find(str(block)[:60]) < html.find("application/ld+json")
    return {"present": present, "data_rows": rows, "before_schema": pos_ok}


# ===========================================================================
# 14A -- Route at a Glance <-> H2 correspondence
# ===========================================================================
def raag_vs_h2(html: str):
    soup = _soup(html)
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]
    section_h2 = [t for t in h2s if t.lower() not in ("route at a glance", "next stop")]
    raag = None
    for h in soup.find_all("h2"):
        if h.get_text(strip=True).lower() == "route at a glance":
            ol = h.find_next("ol")
            if ol:
                raag = [li.get_text(strip=True) for li in ol.find_all("li")]
            break
    return {
        "h2_sections": section_h2,
        "raag_items": raag if raag is not None else [],
        "raag_present": raag is not None,
        "counts_match": raag is not None and len(raag) == len(section_h2),
    }
