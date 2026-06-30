#!/usr/bin/env python3
"""
Test result artefact analysis (OpenRouter-powered).

Usage:
    python .claude/or_test_analyze.py --input Output/test-results.txt
    pytest -q 2>&1 | python .claude/or_test_analyze.py        # reads stdin

Sends the test output (pytest log, junit xml, etc.) to OpenRouter and writes a
triage report to Output/test-analysis/ : what failed, likely root cause, and the
smallest fix. Heavy analysis runs on the free model -> minimal Claude-Code tokens.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import or_client  # noqa: E402

SYSTEM = (
    "You are a test-triage engineer. Given raw test output, produce a concise report: "
    "(1) PASS/FAIL summary with counts, (2) each failing test with the likely root cause, "
    "(3) the smallest concrete fix for each, (4) any flakiness/environment red flags. "
    "Be specific and brief."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="")
    args = ap.parse_args()

    if args.input:
        p = Path(args.input)
        if not p.is_file():
            or_client.safe_print("[analyze] input not found: " + str(p))
            sys.exit(1)
        data = p.read_text(encoding="utf-8", errors="ignore")
    else:
        data = sys.stdin.read()

    data = data.strip()
    if not data:
        or_client.safe_print("[analyze] no test output provided.")
        sys.exit(1)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "Test output:\n" + data[:16000]},
    ]
    report, provider = or_client.chat(messages, max_tokens=2048)

    out_dir = Path("Output") / "test-analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out = out_dir / ("analysis-" + stamp + ".md")
    out.write_text("# Test analysis (" + provider + ")\n\n" + report + "\n", encoding="utf-8")
    or_client.safe_print("[analyze] " + provider + " -> " + str(out))
    print()
    print(report[:1500])


if __name__ == "__main__":
    main()
