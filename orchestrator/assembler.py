#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
HTML assembler -- the deterministic Phase-5 "HTML generation" transform.

Turns the source post + certified generated fragments into the canonical enhanced
post body. Pure code (no LLM): strip inline styles (1D), reapply the canonical
summary-block CSS (Step 3), re-emit YouTube embeds via the project template,
remove ?m=1 from internal links (Rule G3), and splice certified fragments into
their canonical positions.
"""
import re

from bs4 import BeautifulSoup

from . import config
from .validators import INTERNAL_HOST, CAPTION_TABLE_CLASS

# ---------------------------------------------------------------------------
# Canonical summary-block CSS (Step 3 template) -- the single authoritative form
# ---------------------------------------------------------------------------
_SB_OUTER = ("background: #fdf8f2; border: 2px solid rgb(139, 69, 19); "
             "border-radius: 8px; padding: 18px 22px; margin: 1.5em 0; "
             "font-family: Georgia, serif;")
_SB_LABEL = ("font-variant: small-caps; font-size: 0.85em; color: saddlebrown; "
             "letter-spacing: 0.08em; margin: 0 0 10px 0;")
_SB_NARR = "margin: 0 0 14px 0;"
_SB_TABLE = "width: 100%; border-collapse: collapse; font-size: 0.92em;"
_SB_HEADER_TR = "border-top: 1px solid rgb(139, 69, 19);"
_SB_HEADER_TD = "padding: 6px 8px; color: saddlebrown; font-weight: bold; white-space: nowrap;"
_SB_DATA_TR = "border-top: 1px solid #e8d5b7;"
_SB_DATA_TD_L = "padding: 6px 8px; color: saddlebrown;"
_SB_DATA_TD_R = "padding: 6px 8px;"


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def canonical_summary_block(label, narrative, rows):
    """Build the canonical summary block. rows = list of (emoji, descriptor)."""
    out = ['<div style="' + _SB_OUTER + '">']
    out.append('  <p style="' + _SB_LABEL + '">' + _esc(label) + '</p>')
    out.append('  <p style="' + _SB_NARR + '">' + _esc(narrative) + '</p>')
    out.append('  <table style="' + _SB_TABLE + '">')
    out.append('    <tbody>')
    out.append('      <tr style="' + _SB_HEADER_TR + '">')
    out.append('        <td style="' + _SB_HEADER_TD + '">What&#39;s Covered</td>')
    out.append('        <td style="' + _SB_DATA_TD_R + '"></td>')
    out.append('      </tr>')
    for emoji, descriptor in rows:
        out.append('      <tr style="' + _SB_DATA_TR + '">')
        out.append('        <td style="' + _SB_DATA_TD_L + '">' + _esc(emoji) + '</td>')
        out.append('        <td style="' + _SB_DATA_TD_R + '">' + _esc(descriptor) + '</td>')
        out.append('      </tr>')
    out.append('    </tbody>')
    out.append('  </table>')
    out.append('</div>')
    return "\n".join(out)


def _find_summary_block(soup):
    for p in soup.find_all("p"):
        if "Post Summary" in (p.get_text() or ""):
            return p, p.find_parent("div")
    return None, None


def reapply_summary_block(html):
    """Strip the summary block's source CSS and rebuild it from the canonical
    template, preserving label / narrative / rows. Returns (html, changed)."""
    soup = BeautifulSoup(html, "html.parser")
    label_p, block = _find_summary_block(soup)
    if not block:
        return html, False
    label_text = label_p.get_text(strip=True)
    narrative_text = ""
    for p in block.find_all("p"):
        if p is label_p:
            continue
        narrative_text = p.get_text(" ", strip=True)
        break
    rows = []
    tbl = block.find("table")
    if tbl:
        for tr in tbl.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            left = tds[0].get_text(strip=True)
            right = tds[1].get_text(" ", strip=True)
            if not right and "covered" in left.lower():
                continue  # header row
            rows.append((left, right))
    new_node = BeautifulSoup(canonical_summary_block(label_text, narrative_text, rows), "html.parser")
    block.replace_with(new_node)
    return str(soup), True


# ---------------------------------------------------------------------------
# 1D -- strip inline styles (except summary block + YouTube wrappers)
# ---------------------------------------------------------------------------
def _protected_ids(soup):
    protected = set()
    _label_p, block = _find_summary_block(soup)
    if block:
        protected.add(id(block))
        for el in block.find_all(True):
            protected.add(id(el))
    for iframe in soup.find_all("iframe"):
        if "youtube" in (iframe.get("src", "") or ""):
            inner = iframe.parent
            outer = inner.parent if inner is not None else None
            for cand in (iframe, inner, outer):
                if cand is not None and hasattr(cand, "find_all"):
                    protected.add(id(cand))
                    for el in cand.find_all(True):
                        protected.add(id(el))
    return protected


def strip_body_inline_styles(html):
    soup = BeautifulSoup(html, "html.parser")
    protected = _protected_ids(soup)
    removed = 0
    for el in soup.find_all(style=True):
        if id(el) in protected:
            continue
        del el["style"]
        removed += 1
    return str(soup), removed


# ---------------------------------------------------------------------------
# Step 12 -- remediate forbidden AI-cliche words in EXISTING body prose
# ---------------------------------------------------------------------------
# Curated safe replacements: only forbidden descriptive/analytical/marketing words
# that are effectively never proper nouns in travel prose, so a whole-word swap is
# safe (unlike e.g. "Foster"/"Explore", which can be place/section names -- those
# are left to the generative Step 12, TICKET-0057). Empty string = delete the word.
_FORBIDDEN_SYNONYMS = {
    "landscape": "scenery", "realm": "domain", "tapestry": "mix",
    "delve": "dig", "comprehensive": "complete", "holistic": "overall",
    "multifaceted": "varied", "nestled": "set", "nestling": "sitting",
    "amplify": "boost", "propel": "push", "ignite": "spark",
    "furthermore": "also", "consequently": "so", "substantially": "greatly",
    "unwavering": "steady", "heartfelt": "sincere", "unprecedented": "rare",
    "ponder": "consider",
}


def _match_case(original, replacement):
    if not replacement:
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def remediate_forbidden_prose(html):
    """Swap safe forbidden words in visible body text (not markup/urls). Returns
    (html, replacements). Words not in the curated map are left for the generative
    Step 12 pass."""
    from bs4 import NavigableString
    soup = BeautifulSoup(html, "html.parser")
    count = 0

    def _sub(text):
        nonlocal count
        def repl(m):
            nonlocal count
            count += 1
            out = _match_case(m.group(0), _FORBIDDEN_SYNONYMS[m.group(0).lower()])
            return out
        for word in _FORBIDDEN_SYNONYMS:
            text = re.sub(r"\b" + re.escape(word) + r"\b", repl, text, flags=re.IGNORECASE)
        return text

    for node in list(soup.find_all(string=True)):
        parent = node.parent.name if node.parent else ""
        if parent in ("script", "style"):
            continue
        new = _sub(str(node))
        if new != str(node):
            node.replace_with(NavigableString(new))
    # collapse any double spaces a deletion may have left
    return str(soup), count


# ---------------------------------------------------------------------------
# Rule G3 -- remove ?m=1 from internal links
# ---------------------------------------------------------------------------
def remove_m1_internal(html):
    soup = BeautifulSoup(html, "html.parser")
    n = 0
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if INTERNAL_HOST in h and "?m=1" in h:
            a["href"] = h.replace("?m=1", "")
            n += 1
    return str(soup), n


# ---------------------------------------------------------------------------
# 1E / Phase 5 -- re-emit YouTube embeds via the project template
# ---------------------------------------------------------------------------
def _youtube_template():
    path = config.resolve_doc("youtube_embed")
    if path and path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    return None


def _video_id(src):
    m = re.search(r"/embed/([A-Za-z0-9_-]{6,})", src or "")
    return m.group(1) if m else None


def reemit_youtube(html):
    """Normalise every YouTube embed to the project template (preserve id+caption)."""
    template = _youtube_template()
    if not template:
        return html, 0
    soup = BeautifulSoup(html, "html.parser")
    count = 0
    for iframe in list(soup.find_all("iframe")):
        src = iframe.get("src", "") or ""
        if "youtube" not in src:
            continue
        vid = _video_id(src)
        if not vid:
            continue
        title = iframe.get("title", "") or ""
        # caption: nearest tr-caption <p> in the embed wrapper, else iframe title
        wrapper = iframe.parent.parent if (iframe.parent and iframe.parent.parent) else iframe.parent
        caption = ""
        if wrapper is not None and hasattr(wrapper, "find"):
            cap = wrapper.find("p", class_=lambda c: c and "tr-caption" in c)
            if cap:
                caption = cap.get_text(" ", strip=True)
        block = (template.replace("[VIDEO_ID]", vid)
                 .replace("YJ354Qhiae0", vid)  # template ships with a sample id
                 .replace("[VIDEO TITLE]", title or caption or "Video")
                 .replace("[CAPTION TEXT]", caption or title or ""))
        new_node = BeautifulSoup(block, "html.parser")
        target = wrapper if (wrapper is not None and wrapper.name == "div") else iframe
        target.replace_with(new_node)
        count += 1
    return str(soup), count


# ---------------------------------------------------------------------------
# Pre-fold zone: build a NEW summary block + schema for posts that lack them
# ---------------------------------------------------------------------------
def _find_more_comment(soup):
    """The real fold marker is the comment whose content is exactly 'more' -- NOT
    any doc-comment that merely mentions the word (e.g. the reference pre-fold's
    header comment documents the <!--more--> rule)."""
    from bs4 import Comment
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if c.strip() == "more":
            return c
    return None


def _looks_like_row(line):
    return "|" in line


def parse_summary_fragment(text):
    """Parse the Step-3 writer fragment into (label, narrative, rows).

    Tolerates the loose LLM shapes seen in practice: a bracketed/`LABEL:` title on
    the first line, one narrative paragraph, then 'emoji | Section - descriptor'
    rows. rows = list of (emoji, descriptor).
    """
    lines = [ln.strip() for ln in (text or "").replace("\r", "").split("\n")]
    lines = [ln for ln in lines if ln]
    label, narrative_parts, rows = "", [], []
    for ln in lines:
        clean = ln.strip().lstrip("*").rstrip("*").strip()
        low = clean.lower()
        if _looks_like_row(clean):
            emoji, _, rest = clean.partition("|")
            rows.append((emoji.strip(), rest.strip()))
            continue
        if not label and ("post summary" in low or clean.startswith("[") or low.startswith("label")):
            label = clean.strip("[]").split(":", 1)[-1].strip() if low.startswith("label") else clean.strip("[]").strip()
            continue
        # anything else before the rows is narrative
        if not rows:
            body = clean.split(":", 1)[-1].strip() if low.startswith("narrative") else clean
            narrative_parts.append(body)
    narrative = " ".join(narrative_parts).strip()
    return label, narrative, rows


def _existing_ldjson(soup):
    return soup.find("script", attrs={"type": "application/ld+json"})


def apply_prefold(html, summary_fragment, context, schema_script=None):
    """Ensure a canonical pre-fold zone: summary block + TravelAction schema, with
    <!--more--> immediately after </script>.

    - If the post already has a canonical summary block, it is left to
      reapply_summary_block; otherwise we build one from the Step-3 fragment.
    - The schema is (re)built from context and inserted so the order is
      ... intro paragraphs, summary block, <script ld+json>, <!--more--> ...
    """
    from bs4 import Comment
    from . import schema_builder

    soup = BeautifulSoup(html, "html.parser")

    # Locate <!--more--> (canonical anchor for the pre-fold/body boundary).
    more = _find_more_comment(soup)
    if more is None:
        # No fold marker: append one at the end of the pre-fold content we build.
        more = Comment("more")
        soup.append(more)

    # 1. Summary block -- insert a new one only if the post has none.
    _lbl, existing_block = _find_summary_block(soup)
    if existing_block is None and summary_fragment:
        label, narrative, rows = parse_summary_fragment(summary_fragment)
        if not label:
            label = (context.get("post_title", "") or
                     (context.get("origin", "") + " to " + context.get("destination", ""))) + " - Post Summary"
        block_html = canonical_summary_block(label, narrative, rows)
        more.insert_before(BeautifulSoup(block_html, "html.parser"))

    # 2. Schema -- drop any stale ld+json, then insert the freshly built one right
    #    before <!--more--> so the fold sits immediately after </script>.
    for stale in soup.find_all("script", attrs={"type": "application/ld+json"}):
        stale.decompose()
    script_html = schema_script or schema_builder.build_schema_script(context, str(soup))
    more.insert_before(BeautifulSoup(script_html, "html.parser"))

    return str(soup)


# ---------------------------------------------------------------------------
# Fragment splicing (certified generated fragments -> canonical positions)
# ---------------------------------------------------------------------------
def _insert_after_more(soup, fragment_html):
    """Insert a fragment immediately after <!--more--> in document order."""
    more = _find_more_comment(soup)
    node = BeautifulSoup(fragment_html, "html.parser")
    if more is not None:
        more.insert_after(node)
    else:
        soup.append(node)
    return node


def insert_separators(html, separators):
    """Insert each separator <p> between consecutive tr-caption-container tables."""
    if not separators:
        return html, 0
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_=lambda c: c and CAPTION_TABLE_CLASS in c)
    inserted = 0
    si = 0
    for idx in range(len(tables) - 1):
        if si >= len(separators):
            break
        a, b = tables[idx], tables[idx + 1]
        # only if no prose <p> already sits between them
        between_prose = False
        for el in a.next_elements:
            if el is b:
                break
            if getattr(el, "name", None) == "p" and el.get_text(strip=True):
                between_prose = True
                break
        if not between_prose:
            a.insert_after(BeautifulSoup(separators[si], "html.parser"))
            inserted += 1
            si += 1
    return str(soup), inserted


def insert_factoids(html, factoids):
    """Place each section-closing factoid at the END of its H2 section -- just before
    the next <h2> (or the end of the body). factoids = list of {section, html}
    (TICKET-0053)."""
    if not factoids:
        return html, 0
    soup = BeautifulSoup(html, "html.parser")
    h2s = soup.find_all("h2")
    inserted = 0
    for fac in factoids:
        section, frag = fac.get("section", ""), fac.get("html", "")
        if not frag:
            continue
        target = None
        for idx, h in enumerate(h2s):
            if h.get_text(strip=True) == section:
                target = h
                nxt = h2s[idx + 1] if idx + 1 < len(h2s) else None
                break
        node = BeautifulSoup(frag, "html.parser")
        if target is None:
            soup.append(node)                 # no matching heading -> end of body
        elif nxt is not None:
            nxt.insert_before(node)           # end of this section
        else:
            (target.parent or soup).append(node)
        inserted += 1
    return str(soup), inserted


def splice_fragments(html, fragments):
    """
    Insert certified fragments. fragments keys (all optional):
      summary_block, first_paragraph, route_box, route_at_a_glance,
      journey_significance, separators (list).
    Pre-fold (summary block) is replaced in place; body fragments are inserted
    in canonical order right after <!--more-->.
    """
    soup = BeautifulSoup(html, "html.parser")

    # NOTE: the summary block (pre-fold) is handled by apply_prefold(), which parses
    # the Step-3 fragment into the canonical block and inserts it with the schema --
    # it is not spliced as raw text here.

    # body fragments, in reverse canonical order so each insert_after lands correctly
    ordered = [k for k in ("route_at_a_glance", "route_box", "first_paragraph")
               if fragments.get(k)]
    for key in ordered:
        _insert_after_more(soup, fragments[key])

    html = str(soup)
    if fragments.get("factoids"):
        html, _ = insert_factoids(html, fragments["factoids"])
    if fragments.get("separators"):
        html, _ = insert_separators(html, fragments["separators"])
    if fragments.get("journey_significance"):
        soup2 = BeautifulSoup(html, "html.parser")
        soup2.append(BeautifulSoup(fragments["journey_significance"], "html.parser"))
        html = str(soup2)
    return html


# ---------------------------------------------------------------------------
# Top-level assembly
# ---------------------------------------------------------------------------
def assemble(html, fragments=None, context=None):
    """Run the deterministic transforms (and splice fragments if provided).

    context (the extracted route/section context) enables pre-fold generation:
    build the canonical summary block from the Step-3 fragment (when the source has
    none) plus the TravelAction schema, with <!--more--> immediately after </script>.
    """
    html, _ = remove_m1_internal(html)
    html, _ = reemit_youtube(html)
    html, _ = strip_body_inline_styles(html)
    html, _ = remediate_forbidden_prose(html)   # Step 12 (safe subset)
    html, _ = reapply_summary_block(html)
    if fragments:
        html = splice_fragments(html, fragments)
    if context:
        summary_frag = (fragments or {}).get("summary_block")
        html = apply_prefold(html, summary_frag, context)
    return html
