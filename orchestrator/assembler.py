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


def _attr(s):
    """Escape for an HTML double-quoted attribute value (also quotes)."""
    return _esc(s).replace('"', "&quot;").replace("'", "&#39;")


def _frag(html):
    """Parse an HTML fragment into a node to insert. When the fragment is a single
    top-level element (the case for every fragment we splice -- a <div>, <script>,
    <p>, <table>), return that Tag so insert_before/after/replace_with don't get the
    BeautifulSoup document wrapper as their target (TICKET-0121). Falls back to the
    soup object for multi-element fragments."""
    soup = BeautifulSoup(html, "html.parser")
    tags = [c for c in soup.contents if getattr(c, "name", None)]
    return tags[0] if len(tags) == 1 else soup


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
    new_node = _frag(canonical_summary_block(label_text, narrative_text, rows))
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
    # explore family -> wander (travel voice; matches the human workflow). NOT
    # 'explorer' (could be a Ford Explorer). TICKET-0114.
    "exploring": "wandering", "explore": "wander", "explored": "wandered",
    "exploration": "journey",
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


def _safe_caption_html(nodes):
    """Render a list of caption nodes (mixed NavigableString/Tag) to a caption
    HTML fragment that preserves a genuine <a href="http(s)://...">...</a> link
    (e.g. a 'Watch: <a href=...>Video credit</a>' legacy caption) but drops any
    OTHER tag/attribute and rejects any non-http(s) href -- so this can never
    reopen the XSS surface TICKET-0061 closed, while no longer silently
    dropping a real source href out of a video caption (TICKET-0152)."""
    from bs4 import NavigableString, Comment, Tag
    out = []

    def walk(n):
        if isinstance(n, Comment):
            return
        if isinstance(n, NavigableString):
            out.append(_esc(str(n)))
        elif isinstance(n, Tag):
            if n.name == "a":
                href = n.get("href", "") or ""
                if re.match(r"^https?://", href, re.IGNORECASE):
                    out.append('<a href="' + _attr(href) + '">' + _esc(n.get_text()) + "</a>")
                    return
            for child in n.children:
                walk(child)

    for node in nodes:
        walk(node)
    return "".join(out).strip()


def reemit_youtube(html):
    """Normalise every YouTube embed to the project template (preserve id+caption)."""
    template = _youtube_template()
    if not template:
        return html, 0
    from bs4 import NavigableString, Comment
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
        p1 = iframe.parent
        p2 = p1.parent if p1 is not None else None
        # Modern nested template: iframe sits 2 levels deep (an aspect-ratio box
        # div, inside an outer wrapper div that also holds the caption <p>) -- only
        # climb to that outer div when it stays scoped to just this embed (few
        # direct children), so we don't accidentally grab an unrelated ancestor.
        climb = (p1 is not None and p1.name == "div" and p2 is not None
                 and getattr(p2, "name", None) == "div"
                 and len(p2.find_all(True, recursive=False)) <= 2)
        wrapper = p2 if climb else p1
        # caption: nearest tr-caption <p> in the embed wrapper, else iframe title
        caption_html, caption_text = "", ""
        if wrapper is not None and hasattr(wrapper, "find"):
            cap = wrapper.find("p", class_=lambda c: c and "tr-caption" in c)
            if cap:
                caption_html = _safe_caption_html(list(cap.children))
                caption_text = cap.get_text(" ", strip=True)
        if not caption_html and not climb and wrapper is not None and hasattr(wrapper, "contents"):
            # Legacy Blogger embed: no tr-caption <p> at all -- the caption is
            # loose text/links sitting right after a <br/>, direct siblings of
            # the iframe in the same wrapper (e.g. '<iframe>...</iframe><br />
            # Watch: <a href="...">Video credit</a>'). Collect every direct
            # child of the wrapper EXCEPT the iframe itself (TICKET-0126/0152).
            caption_nodes = [c for c in wrapper.contents if c is not iframe]
            caption_html = _safe_caption_html(caption_nodes)
            caption_text = "".join(
                c.get_text(" ", strip=True) if hasattr(c, "get_text") else str(c)
                for c in caption_nodes
            ).strip()
        # Escape source-provided title/caption before templating (TICKET-0061):
        # title lands in a double-quoted attribute (plain text only -- a tag
        # can't go in an attribute), caption in element content (safe HTML,
        # TICKET-0152).
        block = (template.replace("[VIDEO_ID]", vid)
                 .replace("[VIDEO TITLE]", _attr(title or caption_text or "Video"))
                 .replace("[CAPTION TEXT]", caption_html or _esc(title or "")))
        new_node = _frag(block)
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
        # a standalone format marker line -> skip it (TICKET-0111)
        if low.rstrip(":") in ("rows", "narrative", "label"):
            continue
        # anything else before the rows is narrative
        if not rows:
            body = clean.split(":", 1)[-1].strip() if low.startswith("narrative") else clean
            # strip a trailing marker that leaked onto the narrative line
            # ('...Grand Canyon itself. ROWS:')  (TICKET-0111)
            body = re.sub(r"\s*\b(rows|narrative|label)\s*:?\s*$", "", body, flags=re.IGNORECASE).strip()
            if body:
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
        # No fold marker: place one at the END OF THE PRE-FOLD ZONE, not the end of
        # the whole post (TICKET-0090). Anchor = the first section <h2> (fold sits
        # just before the first section); else after the intro paragraphs (the first
        # 1-2 <p>); else append as a last resort.
        more = Comment("more")
        first_h2 = soup.find("h2")
        if first_h2 is not None:
            first_h2.insert_before(more)
        else:
            paras = soup.find_all("p")
            if paras:
                anchor = paras[1] if len(paras) > 1 else paras[0]
                anchor.insert_after(more)
            else:
                soup.append(more)

    # 1. Summary block -- insert a new one only if the post has none.
    _lbl, existing_block = _find_summary_block(soup)
    if existing_block is None and summary_fragment:
        _lbl2, narrative, rows = parse_summary_fragment(summary_fragment)
        # Prefer the series/part identity ('Trans-America Part 13') deterministically
        # over the writer's label (which tends to be the ALL-CAPS route) -- TICKET-0112.
        title = (context.get("series") or context.get("post_title") or _lbl2 or
                 (context.get("origin", "") + " to " + context.get("destination", ""))).strip()
        title = re.sub(r"\s*[-—]\s*post summary\s*$", "", title, flags=re.IGNORECASE)
        label = title + " — Post Summary"
        block_html = canonical_summary_block(label, narrative, rows)
        more.insert_before(_frag(block_html))

    # 2. Schema -- drop any stale ld+json, then insert the freshly built one right
    #    before <!--more--> so the fold sits immediately after </script>.
    for stale in soup.find_all("script", attrs={"type": "application/ld+json"}):
        stale.decompose()
    script_html = schema_script or schema_builder.build_schema_script(context, str(soup))
    more.insert_before(_frag(script_html))

    return str(soup)


_SIGNOFF_RE = re.compile(
    r"until next time|fellow wanderers|vagabond couple|safe travels|happy trails",
    re.IGNORECASE)
# A short, standalone closing line -- 'The End.', 'Fin.', 'The end of the road.'
# -- is a sign-off even without one of the phrases above (observed on the
# alaska-cruise post: trailing generated content landed AFTER the author's own
# "The End." because this exact style wasn't recognized, TICKET-0160). Matched
# as the ENTIRE paragraph text (not a substring search) so this never
# misfires on ordinary prose that happens to contain "the end" mid-sentence
# (e.g. "by the end of our trip").
_STANDALONE_SIGNOFF_RE = re.compile(r"^(the\s+end|fin|end)\.?$", re.IGNORECASE)


def _outro_anchor(soup):
    """The node BEFORE which trailing generated content (journey-significance,
    last-section factoid) must be inserted so the post's sign-off/outro stays last
    (TICKET-0060/0160). Prefer a 'Next Stop' H2; else the sign-off paragraph; else
    None (meaning: append to the end)."""
    for h in soup.find_all("h2"):
        if h.get_text(strip=True).lower().startswith("next stop"):
            return h
    # else: the earliest trailing <p> that reads like a sign-off
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if _SIGNOFF_RE.search(text) or _STANDALONE_SIGNOFF_RE.match(text):
            return p
    return None


def _append_before_outro(soup, node):
    """Insert `node` just before the outro anchor, or append if there is none."""
    anchor = _outro_anchor(soup)
    if anchor is not None:
        anchor.insert_before(node)
    else:
        soup.append(node)


# ---------------------------------------------------------------------------
# Fragment splicing (certified generated fragments -> canonical positions)
# ---------------------------------------------------------------------------
def _insert_after_more(soup, fragment_html):
    """Insert a fragment immediately after <!--more--> in document order."""
    more = _find_more_comment(soup)
    node = _frag(fragment_html)
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
            a.insert_after(_frag(separators[si]))
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
        node = _frag(frag)
        if target is not None and nxt is not None:
            nxt.insert_before(node)           # end of this section (before next H2)
        else:
            # last section (or no matching heading): keep the sign-off/outro last
            _append_before_outro(soup, node)
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
        # Journey-significance precedes the Next Stop outro (rev-18 body order) --
        # insert before the sign-off, not at the very end (TICKET-0060).
        _append_before_outro(soup2, _frag(fragments["journey_significance"]))
        html = str(soup2)
    return html


_BLOCK_TAGS = r"(?:div|script|table|ol|ul|h2|h3|h4|p|blockquote)"


def reflow_blocks(html):
    """Insert a newline between DIRECTLY-ADJACENT block elements (and after
    <!--more-->) so the assembled source is readable/diffable. Only touches
    block-to-block boundaries -- never inline tags (a/b/i/span) -- so the rendered
    output is unchanged (TICKET-0119)."""
    prev = None
    # a couple of passes to catch chains like </div><script>...</script><!--more--><p>
    while prev != html:
        prev = html
        html = re.sub(r"(</" + _BLOCK_TAGS + r">|<!--more-->)(<(?:" + _BLOCK_TAGS + r")\b)",
                      r"\1\n\2", html)
    return html


def normalize_characters(html):
    """Normalize odd whitespace/hyphen code points that leak from LLM output:
    non-breaking / figure hyphens -> plain '-', non-breaking spaces -> ' '
    (TICKET-0115). En/em dashes are left intact (they are legitimate)."""
    for ch in ("‑", "‐", "⁃"):   # non-breaking / hyphen / hyphen bullet
        html = html.replace(ch, "-")
    html = html.replace(" ", " ").replace(" ", " ")   # nbsp / narrow nbsp
    return html


def wrap_orphan_text(html):
    """Wrap loose top-level text that sits directly after <!--more--> (a legacy
    Blogger habit -- '<!--more-->Arsenalna station is named after...' with no
    wrapping <p>) into a <p>. Harmless in the original, but reads as broken/
    orphan HTML once real structure (Route at a Glance <ol>, route box, schema)
    is spliced in right next to it (TICKET-0130). Scoped to ONLY top-level
    content after <!--more--> -- pre-fold content (and, in the test reference
    fixture, a large top-level doc-comment preamble) must stay untouched."""
    from bs4 import NavigableString, Comment
    soup = BeautifulSoup(html, "html.parser")
    changed = 0
    more = next((c for c in soup.contents if isinstance(c, Comment) and c.strip() == "more"), None)
    if more is None:
        return str(soup), 0
    after_more = False
    for child in list(soup.contents):
        if child is more:
            after_more = True
            continue
        if not after_more:
            continue
        if isinstance(child, NavigableString) and not isinstance(child, Comment) and child.strip():
            p = soup.new_tag("p")
            child.replace_with(p)
            p.append(child)
            changed += 1
    return str(soup), changed


_FORWARD_REF_RE = re.compile(
    r"\b(continues?|read more|next stop|see more|check out|more (at|on|here))\b", re.IGNORECASE)


def drop_redundant_forward_reference(html, context):
    """When the new lead-in feature (0132) has already referenced the prior post
    up top, the ORIGINAL source's own ad-hoc forward-reference sentence to that
    SAME post (a common old-Blogger habit -- 'Our photo-story continues at
    [link]') becomes a second, disjointed pointer to a post already covered. Drop
    that specific paragraph -- but ONLY when it's short, its one link matches
    the real prior_post URL, and it reads like a bare continuation sentence --
    never touch a paragraph with substantial content just because it happens to
    share that link (TICKET-0134). Safe re: G3 href preservation: the prior
    post's URL is still linked elsewhere (the new lead-in itself, and often the
    original's own intro), so removing this one redundant mention never drops
    the href from the document entirely."""
    prior = context.get("prior_post") if context else None
    if not isinstance(prior, dict) or not prior.get("url"):
        return html, 0
    soup = BeautifulSoup(html, "html.parser")
    removed = 0
    for p in soup.find_all("p"):
        links = p.find_all("a")
        if len(links) != 1 or links[0].get("href") != prior["url"]:
            continue
        text = p.get_text(" ", strip=True)
        if len(text) > 250 or not _FORWARD_REF_RE.search(text):
            continue
        p.decompose()
        removed += 1
    return str(soup), removed


def strip_empty_paragraphs(html):
    """Remove truly-empty <p></p> (no text, no children) -- but keep <p><br/></p>,
    which the author uses for intentional spacing (TICKET-0117)."""
    soup = BeautifulSoup(html, "html.parser")
    removed = 0
    for p in soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find(True):
            p.decompose()
            removed += 1
    return str(soup), removed


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
        html, _ = drop_redundant_forward_reference(html, context)  # TICKET-0134
    html = normalize_characters(html)           # TICKET-0115
    html, _ = strip_empty_paragraphs(html)       # TICKET-0117
    html, _ = wrap_orphan_text(html)             # TICKET-0130
    html = reflow_blocks(html)                   # TICKET-0119 (readable source)
    return html
