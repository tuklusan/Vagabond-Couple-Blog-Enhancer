#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""Assembler tests -- deterministic transforms on the reference + splicing."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import assembler, config, validators  # noqa: E402


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


FAILS = []


def check(name, cond, detail=""):
    print(_ascii(("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail)))
    if not cond:
        FAILS.append(name)


def _load_reference():
    """Read the reference fixture, failing the test cleanly if it is missing
    (TICKET-0026/0027) rather than raising an opaque traceback."""
    path = config.resolve_doc("reference_prefold")
    if not path or not Path(path).exists():
        check("reference_fixture_present", False, "reference_prefold not found")
        return None
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        check("reference_fixture_readable", False, str(e))
        return None


def test_reference_transforms():
    html = _load_reference()
    if html is None:
        return
    before_hrefs = validators.href_inventory(html)
    before_media = validators.media_inventory(html)
    before_rows = validators.summary_block(html)["data_rows"]

    out = assembler.assemble(html)

    # summary block preserved + canonical CSS reapplied
    sb = validators.summary_block(out)
    check("summary_present_after", sb["present"], "")
    # dynamic: row count is preserved through assembly, not a hardcoded 14 (TICKET-0024)
    check("summary_rows_preserved", sb["data_rows"] == before_rows and before_rows > 0,
          "rows=" + str(sb["data_rows"]) + " before=" + str(before_rows))
    check("canonical_radius", "border-radius: 8px" in out)
    check("canonical_georgia", "font-family: Georgia, serif" in out)
    # structure intact
    check("schema_intact", validators.validate_ld_json(out)["ok"])
    check("more_canonical", validators.count_more_tags(out)["canonical_after_script"])
    after_media = validators.media_inventory(out)
    check("image_table_unchanged",
          after_media["caption_tables"] == before_media["caption_tables"]
          and after_media["photographs"] == before_media["photographs"])
    # hrefs preserved byte-for-byte (no ?m=1 in reference, so nothing removed)
    check("hrefs_preserved", validators.diff_hrefs(before_hrefs, out)["ok"],
          str(validators.diff_hrefs(before_hrefs, out)))


def test_strip_removes_body_style():
    snippet = '<p style="color: #0000ee; text-align: left;">hello</p>'
    out, removed = assembler.strip_body_inline_styles(snippet)
    check("strip_removed_style", removed == 1 and "style=" not in out, out)


def test_m1_removal():
    snippet = '<a href="https://thevagabondcouple.blogspot.com/x.html?m=1">x</a>'
    out, n = assembler.remove_m1_internal(snippet)
    check("m1_removed", n == 1 and "?m=1" not in out, out)


def test_splice_order():
    src = '<p>intro</p><!--more-->\n<p>original body</p>'
    fragments = {
        "first_paragraph": "<p>FIRSTPARA</p>",
        "route_box": '<div class="tvc-route-summary">ROUTEBOX</div>',
        "route_at_a_glance": "<h2>Route at a Glance</h2><ol><li>stop</li></ol>",
        "journey_significance": "<p>JOURNEYSIG</p>",
    }
    out = assembler.splice_fragments(src, fragments)
    check("splice_all_present",
          all(s in out for s in ("FIRSTPARA", "ROUTEBOX", "Route at a Glance", "JOURNEYSIG")), out[:200])
    # canonical order after <!--more-->: first paragraph -> route box -> RaaG
    check("splice_order",
          out.find("FIRSTPARA") < out.find("ROUTEBOX") < out.find("Route at a Glance"),
          f"{out.find('FIRSTPARA')},{out.find('ROUTEBOX')},{out.find('Route at a Glance')}")
    # body fragments must land AFTER <!--more-->, not in the intro (TICKET-0081)
    pmore = out.find("<!--more-->")
    check("fragments_after_more", pmore != -1 and out.find("FIRSTPARA") > pmore,
          f"more={pmore} first={out.find('FIRSTPARA')}")


def test_splice_separators():
    src = ('<table class="tr-caption-container"><tbody><tr><td>img A</td></tr></tbody></table>'
           '<table class="tr-caption-container"><tbody><tr><td>img B</td></tr></tbody></table>')
    out, inserted = assembler.insert_separators(src, ["<p>SEPARATOR</p>"])
    # position, not mere presence: img A -> SEPARATOR -> img B (TICKET-0025)
    pa, ps, pb = out.find("img A"), out.find("SEPARATOR"), out.find("img B")
    check("separator_inserted", inserted == 1 and "SEPARATOR" in out, str(inserted))
    check("separator_between_tables", -1 < pa < ps < pb, f"{pa},{ps},{pb}")


def test_trailing_content_before_outro():
    # journey-significance + last-section factoid must precede the sign-off (0060)
    body = ('<!--more--><h2>One</h2><p>a</p><h2>Last</h2><p>b</p>'
            '<p>Until next time, fellow wanderers. - The Vagabond Couple</p>')
    out = assembler.splice_fragments(body, {"journey_significance": "<p>JSIG</p>"})
    check("journey_before_outro", -1 < out.find("JSIG") < out.find("Until next time"),
          f"{out.find('JSIG')},{out.find('Until next time')}")
    out2, _ = assembler.insert_factoids(body, [{"section": "Last", "html": "<p>FLAST</p>"}])
    check("last_factoid_before_outro", -1 < out2.find("FLAST") < out2.find("Until next time"),
          f"{out2.find('FLAST')},{out2.find('Until next time')}")


def test_youtube_caption_escaped():
    # source-provided title/caption must be escaped, not injected (TICKET-0061)
    html = ('<div><div><iframe src="https://www.youtube.com/embed/ABC123XYZ" '
            'title="x&quot; onerror=alert(1)"></iframe>'
            '<p class="tr-caption">cap &quot;q &lt;script&gt;</p></div></div>')
    out, n = assembler.reemit_youtube(html)
    check("youtube_reemitted", n == 1, str(n))
    low = out.lower()
    # no raw script tag anywhere, and the title attribute is not broken out of
    # (raw onerror= / an unescaped closing quote+space) -- TICKET-0061/0101
    check("no_raw_script_injected", "<script" not in low, out[:120])
    check("no_attr_breakout", "onerror=" not in low and 'title="x" ' not in low, out[:160])


def test_prefold_without_more_marker():
    # no <!--more--> in source: pre-fold content must land BEFORE the first section
    # H2, not at the end of the post (TICKET-0090)
    ctx = {"origin": "X, CA", "destination": "Y, AZ", "post_title": "T", "sections": ["Sec One"]}
    html = ('<p>intro para one</p><h2>Sec One</h2><p>section body</p>')
    frag = "[T - Post Summary]\n\nWe went from X to Y.\n\nA | Sec One - the leg"
    out = assembler.apply_prefold(html, frag, ctx)
    h2 = out.find("<h2>Sec One")
    check("prefold_summary_before_section", -1 < out.find("Post Summary") < h2)
    check("prefold_schema_before_section", -1 < out.find("application/ld+json") < h2)
    check("prefold_more_before_section", -1 < out.find("<!--more-->") < h2)


def main():
    test_prefold_without_more_marker()
    test_youtube_caption_escaped()
    test_reference_transforms()
    test_strip_removes_body_style()
    test_m1_removal()
    test_splice_order()
    test_splice_separators()
    test_trailing_content_before_outro()
    print()
    if FAILS:
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    print("ASSEMBLER TESTS PASSED")


if __name__ == "__main__":
    main()
