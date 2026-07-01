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
# Fragment splicing (certified generated fragments -> canonical positions)
# ---------------------------------------------------------------------------
def _insert_after_more(soup, fragment_html):
    """Insert a fragment immediately after <!--more--> in document order."""
    from bs4 import Comment
    more = None
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if "more" in c:
            more = c
            break
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


def splice_fragments(html, fragments):
    """
    Insert certified fragments. fragments keys (all optional):
      summary_block, first_paragraph, route_box, route_at_a_glance,
      journey_significance, separators (list).
    Pre-fold (summary block) is replaced in place; body fragments are inserted
    in canonical order right after <!--more-->.
    """
    soup = BeautifulSoup(html, "html.parser")

    if fragments.get("summary_block"):
        _label_p, block = _find_summary_block(soup)
        if block:
            block.replace_with(BeautifulSoup(fragments["summary_block"], "html.parser"))

    # body fragments, in reverse canonical order so each insert_after lands correctly
    ordered = [k for k in ("route_at_a_glance", "route_box", "first_paragraph")
               if fragments.get(k)]
    for key in ordered:
        _insert_after_more(soup, fragments[key])

    html = str(soup)
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
def assemble(html, fragments=None):
    """Run the deterministic transforms (and splice fragments if provided)."""
    html, _ = remove_m1_internal(html)
    html, _ = reemit_youtube(html)
    html, _ = strip_body_inline_styles(html)
    html, _ = reapply_summary_block(html)
    if fragments:
        html = splice_fragments(html, fragments)
    return html
