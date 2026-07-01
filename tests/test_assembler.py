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


def test_reference_transforms():
    html = Path(config.resolve_doc("reference_prefold")).read_text(encoding="utf-8", errors="ignore")
    before_hrefs = validators.href_inventory(html)
    before_media = validators.media_inventory(html)

    out = assembler.assemble(html)

    # summary block preserved + canonical CSS reapplied
    sb = validators.summary_block(out)
    check("summary_present_after", sb["present"], "")
    check("summary_rows_preserved", sb["data_rows"] == 14, "rows=" + str(sb["data_rows"]))
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


def test_splice_separators():
    src = ('<table class="tr-caption-container"><tbody><tr><td>img A</td></tr></tbody></table>'
           '<table class="tr-caption-container"><tbody><tr><td>img B</td></tr></tbody></table>')
    out, inserted = assembler.insert_separators(src, ["<p>SEPARATOR</p>"])
    check("separator_inserted", inserted == 1 and "SEPARATOR" in out, str(inserted))


def main():
    test_reference_transforms()
    test_strip_removes_body_style()
    test_m1_removal()
    test_splice_order()
    test_splice_separators()
    print()
    if FAILS:
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    print("ASSEMBLER TESTS PASSED")


if __name__ == "__main__":
    main()
