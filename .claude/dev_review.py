#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Development-time review harness (DeepSeek).

Claude Code authors the project's code / scripts / docs / tests; DeepSeek reviews
them and the findings become tickets in the local tracker (ticket.py) for the
developer to address later.

ROLE SEPARATION (important):
  * This harness uses the DEEPSEEK_API_KEY *environment variable* ONLY. That key
    is the dev-review role.
  * It is NOT the orchestrator app's DeepSeek usage. The app reads
    Config/_SECRETS/deepseek-api-key.txt for its writer fallback / app-reviewer,
    and that wiring is unchanged. This harness never reads that file.

Grounded in the DeepSeek API docs:
  * base https://api.deepseek.com ; model deepseek-v4-pro (1M ctx) — or the
    cheaper deepseek-v4-flash via DEV_REVIEW_DEEPSEEK_MODEL. (Legacy names
    deepseek-chat / deepseek-reasoner deprecate 2026-07-24.)
  * JSON output: response_format={"type":"json_object"} with the word "json" and a
    schema example in the prompt; the API may return empty content -> we retry.
  * temperature 0.0 (DeepSeek's recommendation for code/analysis).

Usage:
    python .claude/dev_review.py <file> [<file> ...] [--tickets] [--json out.json]
    git diff --name-only HEAD | python .claude/dev_review.py - --tickets
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
API_URL = os.environ.get("DEV_REVIEW_BASE_URL", "https://api.deepseek.com") + "/chat/completions"
MODEL = os.environ.get("DEV_REVIEW_DEEPSEEK_MODEL", "deepseek-v4-pro")
TEMPERATURE = 0.0  # DeepSeek recommends 0.0 for coding/analysis

CODE_EXT = {".py", ".sh", ".ps1", ".js", ".ts"}
DOC_EXT = {".md", ".txt", ".rst"}

SCHEMA_EXAMPLE = (
    '{"findings": [{"severity": "Critical", "title": "short title", '
    '"detail": "what is wrong and why it matters", '
    '"suggestion": "the concrete fix"}]}'
)


def _ascii(s):
    return str(s).encode("ascii", "replace").decode("ascii")


def _env_key():
    k = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not k:
        sys.exit("DEEPSEEK_API_KEY not set in the environment (dev-review role).")
    return k


def classify(path):
    p = Path(path)
    name = p.name.lower()
    if p.suffix.lower() in CODE_EXT:
        parts = [part.lower() for part in p.parts]
        if name.startswith("test_") or "tests" in parts or "test" in parts:  # TICKET-0038
            return "test"
        return "code"
    if p.suffix.lower() in DOC_EXT:
        return "doc"
    return None


def _system_prompt(kind):
    if kind == "code":
        focus = ("You are a senior code reviewer. Review for correctness bugs, security "
                 "issues, resource/concurrency problems, error handling, and edge cases. "
                 "Prefer fewer, high-confidence findings over nitpicks.")
    elif kind == "test":
        focus = ("You are a test-suite reviewer. Review for: assertions that actually test "
                 "the intended behavior, missing edge cases / coverage gaps, test isolation "
                 "and determinism (flakiness), and incorrect or tautological assertions.")
    else:  # doc
        focus = ("You are a documentation reviewer for a software project. Review for "
                 "accuracy vs the code, completeness, clarity, broken instructions, and "
                 "internal inconsistency.")
    return (
        focus + " Respond with a single valid json object ONLY, no prose outside it, "
        "matching this schema:\n" + SCHEMA_EXAMPLE + "\n"
        'severity is one of "Critical", "Warning", "Info". If the file is clean, '
        'return {"findings": []}.'
    )


def _extract(resp_json):
    try:
        msg = resp_json["choices"][0]["message"]
    except Exception:
        return ""
    content = msg.get("content")
    if content and content.strip():
        return content
    reasoning = msg.get("reasoning")
    return reasoning if (reasoning and reasoning.strip()) else ""


def _post(payload, headers, retries=3):
    last = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
            if resp.status_code in (429, 503):
                last = "HTTP " + str(resp.status_code)
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
            resp.raise_for_status()
            text = _extract(resp.json())
            if not text.strip():
                last = "empty content"
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                return ""
            return text
        except requests.exceptions.RequestException as e:
            last = str(e)
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise
    return ""


def _parse_findings(text):
    """Tolerant parse: prefer strict json, else find a balanced object with findings."""
    if not text.strip():
        return None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "findings" in obj:
            return obj["findings"]
    except Exception:
        pass
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    obj = json.loads(text[start:i + 1])
                    if isinstance(obj, dict) and "findings" in obj:
                        return obj["findings"]
                except Exception:
                    pass
    return None


def review_file(path):
    kind = classify(path)
    p = Path(path)
    if kind is None or not p.is_file():
        return {"file": str(path), "type": kind, "findings": [], "skipped": True}
    text = p.read_text(encoding="utf-8", errors="ignore")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _system_prompt(kind)},
            {"role": "user", "content": "Review this file (json output).\n\nFILE: "
             + p.name + "\n\n" + text[:200000]},   # generous cap; repo files are well under it (TICKET-0039/0062)
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": "Bearer " + _env_key(), "Content-Type": "application/json"}
    raw = _post(payload, headers)
    findings = _parse_findings(raw)
    if findings is None:
        return {"file": str(path), "type": kind,
                "findings": [{"severity": "Info", "title": "review unparseable/empty",
                              "detail": (raw[:300] if raw else "empty response after retries"),
                              "suggestion": "re-run the review for this file"}],
                "parse_error": True}
    return {"file": str(path), "type": kind, "findings": findings}


# ---------------------------------------------------------------------------
# Reporting + ticket creation
# ---------------------------------------------------------------------------
_PRIORITY = {"critical": "High", "warning": "Medium", "info": "Low"}
_TTYPE = {"code": "Bug", "test": "Task", "doc": "Task"}


def print_summary(results):
    print(_ascii("=" * 66))
    print(_ascii("DeepSeek review summary  (" + MODEL + ", temp " + str(TEMPERATURE) + ")"))
    print(_ascii("=" * 66))
    tot = {"Critical": 0, "Warning": 0, "Info": 0}
    for r in results:
        counts = {"Critical": 0, "Warning": 0, "Info": 0}
        for f in r["findings"]:
            sev = str(f.get("severity", "Info")).capitalize()
            counts[sev] = counts.get(sev, 0) + 1
            tot[sev] = tot.get(sev, 0) + 1
        flag = "" if not r.get("parse_error") else "  [parse error]"
        print(_ascii(f"{r['file']:<42} C:{counts['Critical']} W:{counts['Warning']} "
                     f"I:{counts['Info']}{flag}"))
    print(_ascii("-" * 66))
    print(_ascii(f"TOTAL  Critical:{tot['Critical']}  Warning:{tot['Warning']}  Info:{tot['Info']}"))


def create_tickets(results, min_severity="warning"):
    """Create a ticket per Critical/Warning finding. Returns created ids."""
    order = {"critical": 2, "warning": 1, "info": 0}
    threshold = order.get(min_severity, 1)
    created = []
    for r in results:
        for f in r["findings"]:
            sev = str(f.get("severity", "info")).lower()
            if order.get(sev, 0) < threshold:
                continue
            title = ("[" + Path(r["file"]).name + "] " + str(f.get("title", "finding")))[:80]
            desc = (str(f.get("detail", "")).strip()
                    + (" | Suggestion: " + str(f.get("suggestion", "")).strip()
                       if f.get("suggestion") else "")
                    + " | File: " + r["file"] + " | Severity: " + sev)
            ttype = _TTYPE.get(r["type"], "Task")
            prio = _PRIORITY.get(sev, "Medium")
            proc = subprocess.run(
                [sys.executable, "ticket.py", "new", "--title", title,
                 "--type", ttype, "--priority", prio, "--desc", desc],
                cwd=str(REPO_ROOT), capture_output=True, text=True)
            tid = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else "?"
            created.append((tid, title))
            print(_ascii("  created " + tid + ": " + title))
    return created


def main():
    ap = argparse.ArgumentParser(prog="dev_review")
    ap.add_argument("files", nargs="*", help="files to review (or '-' to read a list from stdin)")
    ap.add_argument("--tickets", action="store_true", help="create a ticket per Critical/Warning finding")
    ap.add_argument("--min-severity", default="warning", choices=["critical", "warning", "info"],
                    help="lowest severity that becomes a ticket (default warning)")
    ap.add_argument("--json", dest="json_out", default=None, help="write the consolidated findings to this JSON file")
    args = ap.parse_args()

    files = args.files
    if files == ["-"]:
        files = [ln.strip() for ln in sys.stdin if ln.strip()]
    if not files:
        sys.exit("usage: python .claude/dev_review.py <file> [...] [--tickets] [--json out.json]")

    results = []
    for f in files:
        try:
            r = review_file(f)
        except Exception as e:
            r = {"file": str(f), "type": classify(f), "findings": [],
                 "error": str(e)[:200]}
            print(_ascii("[error] " + str(f) + ": " + str(e)[:160]))
        if not r.get("skipped"):
            results.append(r)

    print_summary(results)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(_ascii("wrote findings -> " + args.json_out))

    if args.tickets:
        print(_ascii("\nCreating tickets (>= " + args.min_severity + ") ..."))
        created = create_tickets(results, min_severity=args.min_severity)
        print(_ascii("created " + str(len(created)) + " ticket(s)."))


if __name__ == "__main__":
    main()
