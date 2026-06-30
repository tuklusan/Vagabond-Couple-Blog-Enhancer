#!/usr/bin/env python3
"""
HARD code+doc review gate (OpenRouter-powered).

Usage:
    python .claude/or_review_gate.py --staged     # git pre-commit mode (default)

Reviews the staged diff of code (.py) and doc (.md/.txt/.rst) files in a SINGLE
OpenRouter call. If the reviewer reports any Critical issue (and does not end with
APPROVED), the gate exits non-zero -> the commit is blocked.

Full review is written to Output/reviews/ ; only a concise verdict hits the console,
so Claude-Code token usage stays minimal.

Model: pinned via OPENROUTER_GATE_MODEL (default qwen/qwen3-coder:free) for stable,
code-capable reviews instead of the openrouter/free router lottery. Falls back to the
shared client's provider chain (openrouter/free -> DeepSeek -> NVIDIA) on failure.
"""
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import or_client  # noqa: E402

GATE_MODEL = os.environ.get("OPENROUTER_GATE_MODEL", "qwen/qwen3-coder:free")
CODE_EXT = {".py"}
DOC_EXT = {".md", ".txt", ".rst"}
SKIP_SUBSTR = ("_SECRETS", ".review.txt", "Output/", "Input/", "Temp/", ".claude/")
MAX_DIFF_CHARS = 16000

SYSTEM_PROMPT = (
    "You are a strict code and documentation reviewer for a Python travel-blog "
    "automation project. Review the unified git diff below. Report findings grouped "
    "as Critical / Warning / Info. Critical = bugs, security holes, data loss, broken "
    "logic, or docs that are factually wrong/contradictory. "
    "If and ONLY if there are zero Critical issues, end your reply with the single "
    "token: APPROVED"
)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def staged_files():
    res = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"])
    files = []
    for f in res.stdout.splitlines():
        f = f.strip()
        if not f:
            continue
        if any(s in f for s in SKIP_SUBSTR):
            continue
        if Path(f).suffix.lower() in (CODE_EXT | DOC_EXT):
            files.append(f)
    return files


def review_text(prompt):
    """Pinned gate model first, then shared fallback chain."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    try:
        return or_client.call_openrouter(messages, max_tokens=2048, model=GATE_MODEL), GATE_MODEL
    except Exception as e:
        or_client.safe_print("[gate] pinned model failed (" + str(e) + "); using fallback chain...")
        return or_client.chat(messages, max_tokens=2048)


def main():
    files = staged_files()
    if not files:
        print("[gate] No staged code/doc files -- nothing to review.")
        sys.exit(0)

    diff = run(["git", "diff", "--cached", "--"] + files).stdout
    if not diff.strip():
        print("[gate] Empty diff -- skipping.")
        sys.exit(0)
    truncated = diff[:MAX_DIFF_CHARS]
    note = "" if len(diff) <= MAX_DIFF_CHARS else "\n\n[diff truncated for review]"

    prompt = "Files under review:\n" + "\n".join(files) + "\n\nUnified diff:\n" + truncated + note

    try:
        review, provider = review_text(prompt)
    except Exception as e:
        # Fail-open on infrastructure errors so you are never permanently blocked from
        # committing by an outage. Flip GATE_FAIL_CLOSED=1 to make outages block instead.
        msg = "[gate] All review providers failed: " + str(e)
        if os.environ.get("GATE_FAIL_CLOSED") == "1":
            print(msg + "  (fail-closed -> blocking)")
            sys.exit(1)
        print(msg + "  (fail-open -> allowing commit)")
        sys.exit(0)

    approved = bool(re.search(r"(?<!\bNOT\s)\bAPPROVED\b", review, re.IGNORECASE))
    has_critical = bool(re.search(r"\bcritical\b", review, re.IGNORECASE)) and not approved

    reviews_dir = Path("Output") / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out = reviews_dir / ("gate-" + stamp + ".md")
    verdict = "BLOCKED" if has_critical else "APPROVED"
    out.write_text(
        "# Review gate " + verdict + " (" + provider + ")\n\n"
        "Files:\n- " + "\n- ".join(files) + "\n\n" + review + "\n",
        encoding="utf-8",
    )

    or_client.safe_print("[gate] " + verdict + " via " + provider + " -> " + str(out))
    if has_critical:
        # Surface only the Critical section to keep console output tiny.
        crit = re.findall(r"(?is)critical.*?(?=\n\s*(?:warning|info)\b|\Z)", review)
        snippet = (crit[0] if crit else review)[:1200]
        or_client.safe_print("\n[gate] COMMIT BLOCKED -- Critical findings:\n" + snippet)
        or_client.safe_print("\n[gate] Full review: " + str(out))
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
