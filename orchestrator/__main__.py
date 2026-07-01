#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Orchestrator entrypoint.

    python -m orchestrator --input path/to/post.html [--auto] [--run-id NAME]

Runs the pre-check + deterministic Phase-1 analysis + the Phase 4 approval gate
over a source post. (Generative Phase-3 nodes and document-level certification
plug into the same sequencer once the LLM providers are live.)
"""
import argparse
import sys
from pathlib import Path

from . import config, sequencer
from .operator import Operator
from .state import RunState


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


def check_required_support_files():
    """Hard-stop at startup if any Required Project Document is missing, telling the
    user exactly which files to drop into the docs folder. These ship bundled in
    Config/workflow-docs/, so this only trips if they were removed or ORCH_DOCS_DIR
    points at an incomplete folder."""
    missing = config.missing_docs()
    if not missing:
        return
    print(_ascii("=" * 72))
    print(_ascii("STARTUP HALT -- required support files are missing"))
    print(_ascii("=" * 72))
    print(_ascii("The orchestrator needs these files. Drop the missing ones into:"))
    print(_ascii("    " + str(config.DOCS_DIR)))
    print(_ascii("(or set ORCH_DOCS_DIR to a folder that contains them.)"))
    print(_ascii("-" * 72))
    for name in missing:
        print(_ascii("  MISSING  " + name + "  ->  expected filename: "
                     + config.REQUIRED_DOCS[name]))
    print(_ascii("=" * 72))
    sys.exit(3)


def main():
    ap = argparse.ArgumentParser(prog="orchestrator")
    ap.add_argument("--input", required=True, help="path to the source post HTML")
    ap.add_argument("--auto", action="store_true", help="auto-operator (headless; gates use safe defaults)")
    ap.add_argument("--full", action="store_true", help="run the full canonical pipeline (needs live providers unless --dry)")
    ap.add_argument("--dry", action="store_true", help="stub generative/analysis nodes (walk the machinery, no LLM)")
    ap.add_argument("--approve-phase4", action="store_true",
                    help="auto-operator: grant the Phase 4 approval gate (test/CI opt-in; real runs approve interactively)")
    ap.add_argument("--run-id", default=None, help="reuse/name a run id")
    args = ap.parse_args()

    # Hard-stop before doing anything if required support files are missing.
    check_required_support_files()

    src = Path(args.input)
    if not src.exists():
        print(_ascii("input not found: " + str(src)))
        sys.exit(1)
    if not src.is_file():                                   # TICKET-0004
        print(_ascii("input is not a file: " + str(src)))
        sys.exit(1)

    # Read strict UTF-8; on a decode error, warn and fall back to replacement rather
    # than silently dropping bytes (TICKET-0005).
    try:
        html = src.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        print(_ascii("warning: input is not valid UTF-8 (" + str(e)[:80]
                     + "); reading with replacement characters"))
        html = src.read_text(encoding="utf-8", errors="replace")
    state = RunState.create(html, run_id=args.run_id)
    op = Operator(auto=args.auto)
    sctx = sequencer.StepContext(state=state, context={}, operator=op,
                                 mode="auto" if args.auto else "step",
                                 dry_generative=args.dry,
                                 approve_gates=args.approve_phase4)

    seq = sequencer.build_full_sequence() if args.full else sequencer.build_phase1_deterministic_sequence()
    print(_ascii("run dir: " + str(state.dir)))
    result = sequencer.run_sequence(seq, sctx)
    print(_ascii("RESULT: " + str(result)))
    out = state.working_html_path
    if result.get("status") == "DONE":
        print(_ascii("enhanced HTML: " + str(out)))
    sys.exit(0 if result.get("status") in ("DONE", "STOPPED") else 2)


if __name__ == "__main__":
    main()
