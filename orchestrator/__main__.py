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

from . import sequencer
from .operator import Operator
from .state import RunState


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


def main():
    ap = argparse.ArgumentParser(prog="orchestrator")
    ap.add_argument("--input", required=True, help="path to the source post HTML")
    ap.add_argument("--auto", action="store_true", help="auto-operator (headless; gates use safe defaults)")
    ap.add_argument("--full", action="store_true", help="run the full canonical pipeline (needs live providers unless --dry)")
    ap.add_argument("--dry", action="store_true", help="stub generative/analysis nodes (walk the machinery, no LLM)")
    ap.add_argument("--run-id", default=None, help="reuse/name a run id")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(_ascii("input not found: " + str(src)))
        sys.exit(1)

    html = src.read_text(encoding="utf-8", errors="ignore")
    state = RunState.create(html, run_id=args.run_id)
    op = Operator(auto=args.auto)
    sctx = sequencer.StepContext(state=state, context={}, operator=op,
                                 mode="auto" if args.auto else "step",
                                 dry_generative=args.dry)

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
