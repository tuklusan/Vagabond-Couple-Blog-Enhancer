#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""Tier-2 deterministic certification (G2 Pass 2) -- no LLM."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import config, review_loop, validators  # noqa: E402
from orchestrator.state import RunState  # noqa: E402


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


FAILS = []


def check(name, cond, detail=""):
    print(_ascii(("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail)))
    if not cond:
        FAILS.append(name)


def main():
    html = Path(config.resolve_doc("reference_prefold")).read_text(encoding="utf-8", errors="ignore")

    cl = review_loop.document_deterministic_checklist(html, validators.href_inventory(html))
    print(_ascii("checklist: " + str(cl["checks"])))
    print(_ascii("failed: " + str(cl["failed"])))

    c = cl["checks"]
    check("schema_ok", c["schema_ok"])
    check("more_canonical", c["more_canonical"])
    check("image_table_match", c["image_table_match"])
    check("summary_present", c["summary_present"])
    check("no_ufffd", c["no_ufffd"])
    # assert the key EXISTS and is True, so an omitted check can't silently pass (TICKET-0028)
    check("hrefs_preserved", c.get("hrefs_preserved") is True)
    # no_forbidden is reported but not hard-asserted (reference prose may trip a term)
    print(_ascii("no_forbidden (informational): " + str(c["no_forbidden"])))

    # full certification, reviewer skipped -> certified mirrors Pass 2
    state = RunState.create(html, run_id="test_doccert")
    state.save_artifact("1C_media_inventory", validators.media_inventory(html))
    cert = review_loop.run_document_certification(state, run_reviewer=False)
    check("cert_has_keys", "certified" in cert and "pass2_deterministic" in cert)
    # value, not just presence: with the reviewer skipped, certified == pass2.ok (0083)
    check("cert_matches_pass2", cert["certified"] == cert["pass2_deterministic"]["ok"])
    check("cert_pass1_skipped", cert["pass1_reviewer"] is None)
    check("cert_artifact_saved", state.has_artifact("phase5_certification"))

    print()
    if FAILS:
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    print("DOCUMENT-CERT TESTS PASSED")


if __name__ == "__main__":
    main()
