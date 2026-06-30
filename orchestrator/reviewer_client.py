#!/usr/bin/env python3
"""
REVIEWER client -- Claude API, web-grounded.

This is the trust anchor of the pipeline. The writer never finalises a factual
claim; the reviewer fact-checks against authoritative web sources and certifies
content against criteria (a)-(e) before it persists. Returns a structured JSON
verdict plus the source URLs it consulted (the anti-hallucination audit trail).

Notes / API specifics:
  * Model: claude-opus-4-8 by default (config.REVIEWER_MODEL).
  * Web search server tool: web_search_20260209 (falls back to web_search_20250305).
  * Server-tool loops can return stop_reason == "pause_turn" -> re-send to continue.
  * Verdict is emitted as JSON by PROMPT + defensive json parse -- NOT
    output_config.format, which 400s when web-search citations are present.
"""
import json
import os
import re
from pathlib import Path

import anthropic

from . import config
from . import writer_client

# Appended to the reviewer system prompt when falling back to DeepSeek, which has
# no live web access -- keeps the anti-hallucination guarantee intact.
DEEPSEEK_FALLBACK_NOTE = (
    "\n\nIMPORTANT: You are operating WITHOUT live web access. Do not mark any "
    "specific figure, date, record, distance, elevation, or named-entity claim "
    "CERTIFIED unless you are highly confident from reliable knowledge. If you "
    "cannot verify a claim, use REVISE (when you know the correct value) or "
    "ESCALATE (when you do not) rather than certifying it from memory."
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = PROJECT_ROOT / "Config" / "_SECRETS"


def load_anthropic_key() -> str:
    val = os.environ.get("ANTHROPIC_API_KEY")
    if val:
        return val.strip()
    path = SECRETS_DIR / "anthropic-api-key.txt"
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
        raw = text.strip()
        if raw and "=" not in raw:
            return raw
    return ""


def _client():
    key = load_anthropic_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not found (env or Config/_SECRETS/anthropic-api-key.txt)")
    return anthropic.Anthropic(api_key=key)


# ---------------------------------------------------------------------------
# Source-URL collection (audit trail)
# ---------------------------------------------------------------------------
def _collect_search_sources(block, sources):
    content = getattr(block, "content", None)
    if content is None:
        return
    # Error result: content is a single object with an error_code -> no urls.
    if not isinstance(content, list):
        return
    for result in content:
        url = getattr(result, "url", None)
        if url:
            sources.append(url)


def _dedup(seq):
    return list(dict.fromkeys(seq))


# ---------------------------------------------------------------------------
# JSON verdict extraction (defensive -- the model may wrap JSON in prose)
# ---------------------------------------------------------------------------
def _balanced_objects(text):
    """Yield every balanced {...} substring in text (ignores braces in strings)."""
    out = []
    depth = 0
    start = None
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    out.append(text[start:i + 1])
                    start = None
    return out


def extract_verdict(text):
    """Return the verdict dict from model text, or None if unparseable."""
    # Prefer a ```json fenced block.
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL):
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    parsed = []
    for cand in _balanced_objects(text):
        try:
            parsed.append(json.loads(cand))
        except Exception:
            pass
    for obj in parsed:
        if isinstance(obj, dict) and "decision" in obj:
            return obj
    return parsed[-1] if parsed else None


# ---------------------------------------------------------------------------
# Core review call
# ---------------------------------------------------------------------------
def _run_conversation(client, model, system, user, tools, max_tokens, max_continuations):
    messages = [{"role": "user", "content": user}]
    text_parts = []
    sources = []
    for _ in range(max_continuations + 1):
        resp = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            tools=tools, messages=messages,
        )
        for block in resp.content:
            bt = getattr(block, "type", None)
            if bt == "text":
                text_parts.append(getattr(block, "text", "") or "")
                for c in (getattr(block, "citations", None) or []):
                    u = getattr(c, "url", None)
                    if u:
                        sources.append(u)
            elif bt and bt.startswith("web_search_tool_result"):
                _collect_search_sources(block, sources)
        if getattr(resp, "stop_reason", None) == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        break
    return "".join(text_parts), _dedup(sources)


def _review_with_claude(system, user, web_search, model, max_tokens, max_continuations):
    """Claude path (web-grounded). Returns (text, sources). Raises on failure."""
    client = _client()
    model = model or config.REVIEWER_MODEL
    tool_types = [config.WEB_SEARCH_TOOL_TYPE, config.WEB_SEARCH_TOOL_TYPE_FALLBACK] if web_search else [None]
    last_err = None
    for tool_type in tool_types:
        tools = [{"type": tool_type, "name": "web_search"}] if tool_type else []
        try:
            return _run_conversation(client, model, system, user, tools, max_tokens, max_continuations)
        except anthropic.BadRequestError as e:
            msg = str(getattr(e, "message", "") or e)
            # Only retry the next tool variant when the error is about the
            # web_search tool. Billing/auth/other 400s must surface at once so
            # review_raw can fall back to DeepSeek.
            if web_search and tool_type and ("web_search" in msg or "tool" in msg.lower()):
                last_err = e
                continue
            raise
    raise last_err if last_err else RuntimeError("claude review failed")


def _review_with_deepseek(system, user, max_tokens):
    """DeepSeek fallback path (no web tool). Returns (text, sources=[])."""
    messages = [
        {"role": "system", "content": system + DEEPSEEK_FALLBACK_NOTE},
        {"role": "user", "content": user},
    ]
    text = writer_client.call_deepseek(messages, max_tokens=max_tokens, model=config.REVIEWER_DEEPSEEK_MODEL)
    return text, []


def review_raw(system, user, web_search=True, model=None, max_tokens=4096, max_continuations=4):
    """
    Run a review. Reviewer role = Claude (web-grounded) first; if Claude is
    unusable for ANY reason (no credit balance, auth, outage), fall back
    UNIVERSALLY to DeepSeek. Returns: (text, sources, provider).
    """
    try:
        text, sources = _review_with_claude(system, user, web_search, model, max_tokens, max_continuations)
        return text, sources, "claude:" + (model or config.REVIEWER_MODEL)
    except Exception as e_claude:
        _safe_print("[reviewer] Claude unusable (" + str(e_claude)[:160] + "); falling back to DeepSeek...")
        try:
            text, sources = _review_with_deepseek(system, user, max_tokens)
            return text, sources, "deepseek:" + config.REVIEWER_DEEPSEEK_MODEL
        except Exception as e_ds:
            # Both reviewer providers are unusable. Never crash and never silently
            # certify -> emit a verdict that forces ESCALATE to the operator.
            _safe_print("[reviewer] DeepSeek also failed (" + str(e_ds)[:160] + "); ESCALATING.")
            note = ("both reviewer providers unavailable: claude=" + str(e_claude)[:120]
                    + " | deepseek=" + str(e_ds)[:120])
            synthetic = json.dumps({"decision": "ESCALATE", "note": note, "criteria": {}})
            return synthetic, [], "none"


def ping():
    """Confirm the reviewer is usable (via whichever provider answers)."""
    text, _sources, provider = review_raw("Reply with exactly: REVIEWER OK", "ping", web_search=False, max_tokens=64)
    return provider + " -> " + text.strip()


def certify(system, user, web_search=True, model=None, max_tokens=4096):
    """
    High-level: run a review expecting a JSON verdict. Returns:
        (verdict_dict, raw_text, sources)
    verdict_dict always has a 'decision'; if parsing fails it is forced to
    ESCALATE so a malformed reply never silently passes.
    """
    text, sources, provider = review_raw(system, user, web_search=web_search, model=model, max_tokens=max_tokens)
    verdict = extract_verdict(text)
    if not isinstance(verdict, dict) or "decision" not in verdict:
        verdict = {
            "decision": "ESCALATE",
            "note": "reviewer reply could not be parsed into a verdict",
            "raw_excerpt": text[:600],
        }
    # Record which provider actually adjudicated (audit trail).
    verdict["reviewer_provider"] = provider
    # Always surface the consulted sources alongside the verdict.
    verdict.setdefault("sources", [])
    merged = _dedup(list(verdict.get("sources") or []) + sources)
    verdict["sources"] = merged
    return verdict, text, merged


# ---------------------------------------------------------------------------
# Convenience: single-claim fact check (used in the Phase A smoke test)
# ---------------------------------------------------------------------------
_FACTCHECK_SYSTEM = (
    "You are a meticulous travel fact-checker. Verify the user's claim against "
    "authoritative web sources using the web_search tool before judging. Do not "
    "rely on memory for specific figures (elevations, dates, records, distances). "
    "After verifying, output ONLY a JSON object (no prose outside it) of the form:\n"
    '{"decision": "CERTIFIED" | "REVISE" | "ESCALATE", '
    '"criteria": {"facts": {"status": "pass" | "fail", '
    '"findings": ["..."], "sources": ["url", "..."]}}, '
    '"revision_instructions": "what to change if REVISE, else empty"}\n'
    "CERTIFIED only if the claim is verifiably true. REVISE if it is wrong and "
    "you found the correct value. ESCALATE if it cannot be verified."
)


def fact_check(claim, context=""):
    user = "Claim to verify:\n" + claim
    if context:
        user += "\n\nContext:\n" + context
    return certify(_FACTCHECK_SYSTEM, user, web_search=True)


def _safe_print(msg):
    print(str(msg).encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    # Smoke test: a deliberately wrong elevation must be caught + corrected.
    verdict, text, sources = fact_check(
        "Wuqia (Ulugqat), Xinjiang, China sits at an elevation of about 3000 meters.",
        context="It is in fact roughly 2,170-2,900 m depending on the point; verify.",
    )
    _safe_print("decision: " + str(verdict.get("decision")))
    _safe_print("facts: " + json.dumps(verdict.get("criteria", {}).get("facts", {}), ensure_ascii=True)[:500])
    _safe_print("sources: " + json.dumps(sources, ensure_ascii=True)[:400])
