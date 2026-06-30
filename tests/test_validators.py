#!/usr/bin/env python3
"""Deterministic-validator tests against the canonical reference pre-fold HTML."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import config, validators  # noqa: E402


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


def main():
    ref = config.resolve_doc("reference_prefold")
    assert ref is not None, "reference pre-fold doc not found"
    html = Path(ref).read_text(encoding="utf-8", errors="ignore")

    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(_ascii(f"[{status}] {name} {detail}"))
        if not cond:
            failures.append(name)

    # --- <!--more--> (reference is a DOC fixture: its comment mentions the token
    #     in prose, so raw count > 1; the canonical placement check is the
    #     meaningful structural invariant) ---
    more = validators.count_more_tags(html)
    check("more_canonical_after_script", more["canonical_after_script"], str(more))

    # --- ld+json ---
    schema = validators.validate_ld_json(html)
    check("schema_valid_json", schema.get("valid_json"), "")
    check("schema_is_travelaction", schema.get("type_is_travelaction"), "")
    check("schema_author_ok", schema.get("author_ok"), str(schema.get("missing_fields")))

    # --- media inventory ---
    media = validators.media_inventory(html)
    check("caption_tables>=1", media["caption_tables"] >= 1, f"tables={media['caption_tables']}")
    check("image_table_match", media["image_table_match"],
          f"imgs={media['photographs']} tables={media['caption_tables']}")

    # --- summary block ---
    sb = validators.summary_block(html)
    check("summary_present", sb["present"], "")
    check("summary_rows>=10", sb["data_rows"] >= 10, f"rows={sb['data_rows']}")

    # --- forbidden-term scanner loads rules + detects planted terms ---
    words, phrases = validators.load_writing_rules_terms()
    check("rules_words_loaded", len(words) > 10, f"words={len(words)}")
    check("rules_phrases_loaded", len(phrases) > 3, f"phrases={len(phrases)}")
    hits = validators.scan_forbidden("We must leverage this nestled realm. In conclusion, naturally.")
    terms_found = {h["term"].lower() for h in hits}
    check("forbidden_detects_words", {"leverage", "nestled", "realm"} <= terms_found, str(sorted(terms_found)))
    check("forbidden_detects_phrases",
          any("conclusion" in t for t in terms_found) or any("naturally" in t for t in terms_found),
          str(sorted(terms_found)))

    # --- question-mark scan runs (reference may have ? in doc comment) ---
    qm = validators.scan_question_marks(html)
    check("qmscan_runs", isinstance(qm, dict) and "ufffd_count" in qm, "")
    check("no_ufffd_in_reference", qm["ufffd_count"] == 0, f"ufffd={qm['ufffd_count']}")

    # --- href inventory + preservation diff is identity on itself ---
    inv = validators.href_inventory(html)
    diff = validators.diff_hrefs(inv, html)
    check("href_self_diff_ok", diff["ok"] and not diff["removed"], str(diff))

    # --- ETR runs (reference is pre-fold only; below-more is small) ---
    etr = validators.etr_minutes(html)
    check("etr_runs", "etr_minutes" in etr, str(etr))

    print()
    if failures:
        print(_ascii(f"FAILED: {failures}"))
        sys.exit(1)
    print("ALL VALIDATOR TESTS PASSED")


if __name__ == "__main__":
    main()
