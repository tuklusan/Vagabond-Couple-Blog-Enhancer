#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""Deterministic source-context extraction tests (no LLM)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import config, context_extractor  # noqa: E402


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


FAILS = []


def check(name, cond, detail=""):
    print(_ascii(("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail)))
    if not cond:
        FAILS.append(name)


def main():
    # Fail cleanly if the fixture is missing rather than raising a raw traceback
    # (TICKET-0027).
    path = config.resolve_doc("reference_prefold")
    if not path or not Path(path).exists():
        check("reference_fixture_present", False, "reference_prefold not found")
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    try:
        html = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        check("reference_fixture_readable", False, str(e))
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    ctx = context_extractor.extract_context(html)

    print(_ascii("origin: " + ctx["origin"]))
    print(_ascii("destination: " + ctx["destination"]))
    print(_ascii("title: " + ctx["post_title"][:80]))
    print(_ascii("stops: " + str(len(ctx["stops"])) + "  waypoints: " + str(len(ctx["waypoints"]))
                 + "  sections: " + str(len(ctx["sections"]))))
    print(_ascii("landmarks: " + ctx["landmarks"][:120]))

    check("origin_from_schema", ctx["origin"] == "Ashgabat, Turkmenistan", ctx["origin"])
    check("destination_from_schema", ctx["destination"] == "Turkmenbashi, Turkmenistan", ctx["destination"])
    check("title_extracted", "Ashgabat to Turkmenbashi" in ctx["post_title"])
    check("stops_extracted", len(ctx["stops"]) >= 5, len(ctx["stops"]))
    check("landmarks_extracted", len(ctx["landmarks"]) > 0)
    check("waypoints_extracted", len(ctx["waypoints"]) >= 1, len(ctx["waypoints"]))
    check("sections_extracted", len(ctx["sections"]) >= 10, len(ctx["sections"]))
    check("etr_extracted", ctx["etr_minutes"] >= 1, ctx["etr_minutes"])
    check("existing_facts", len(ctx["existing_facts"]) > 50)
    # content correctness, not just counts (TICKET-0082): every stop/waypoint/section
    # is a real non-empty string, and known fixture entities are present.
    check("stops_are_nonempty_strings",
          all(isinstance(s, str) and s.strip() for s in ctx["stops"]))
    check("sections_are_nonempty_strings",
          all(isinstance(s, str) and s.strip() for s in ctx["sections"]))
    check("waypoints_are_nonempty_strings",
          all(isinstance(s, str) and s.strip() for s in ctx["waypoints"]))
    joined = " ".join(ctx["stops"] + ctx["waypoints"]) + " " + ctx["landmarks"]
    check("known_entities_present", "Ashgabat" in joined and "Turkmenbashi" in joined, joined[:80])

    print()
    if FAILS:
        print(_ascii("FAILED: " + str(FAILS)))
        sys.exit(1)
    print("CONTEXT-EXTRACTION TESTS PASSED")


if __name__ == "__main__":
    main()
