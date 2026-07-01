#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
WRITER client for the orchestrator (lifted from the prior or_client.py).

Primary provider:  OpenRouter (free model)
Fallbacks:         DeepSeek, then NVIDIA NIM

The writer does bulk content generation. It NEVER finalises a factual claim --
the reviewer (reviewer_client) must certify claims before they persist.

Config (all overridable via environment):
    OPENROUTER_AI_API_KEY   - required for primary; else read from secrets file
    OPENROUTER_BASE_URL     - default https://openrouter.ai/api/v1
    OPENROUTER_MODEL        - default openrouter/free
    DEEPSEEK_API_KEY        - optional fallback
    NVIDIA_API_KEY_CODING   - optional fallback
"""
import os
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = PROJECT_ROOT / "Config" / "_SECRETS"

OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# OpenRouter reasoning control (OPT-IN, default off). NOTE: the `openrouter/free`
# ROUTER rejects `reasoning.effort:"none"` with HTTP 400 ("Reasoning is mandatory
# for this endpoint") and routes to a different (sometimes reasoning) model each
# call. So "none" only works when OPENROUTER_MODEL is pinned to a specific
# non-reasoning instruct model that accepts it. Leave empty for the free router.
OPENROUTER_REASONING_EFFORT = os.environ.get("OPENROUTER_REASONING_EFFORT", "").strip()
# Ask OpenRouter to include token/cost accounting in the response (opt-in).
OPENROUTER_INCLUDE_USAGE = os.environ.get("OPENROUTER_INCLUDE_USAGE", "0") == "1"

# Both configured writer models (openrouter/free and deepseek-v4-pro) are
# reasoning models: they spend output tokens on internal reasoning BEFORE
# emitting the visible answer. A small max_tokens can be fully consumed by
# reasoning, leaving empty content and a spurious escalation. Measured: a tight
# node (<=150-char description) needs ~1500 tokens for deepseek-v4-pro to finish
# reasoning AND emit content; 800 was too low. This floor guarantees reasoning
# headroom regardless of a node's short-output budget -- the prompt, not
# max_tokens, controls how long the answer actually is.
REASONING_TOKEN_FLOOR = int(os.environ.get("WRITER_TOKEN_FLOOR", "1600"))


def safe_print(msg):
    """Print ASCII-safe (Windows console can choke on unicode model output)."""
    print(str(msg).encode("ascii", "replace").decode("ascii"))


def _load_key(env_var: str, secret_file: str, prefix: str) -> str:
    val = os.environ.get(env_var)
    if val:
        return val.strip()
    path = SECRETS_DIR / secret_file
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Tolerate 'NAME = value' with spaces around '=' (TICKET-0023).
            if "=" in line:
                name, val = line.split("=", 1)
                if name.strip() == prefix:
                    return val.strip()
        # Bare-key file: return the first non-empty, non-'NAME=value' line.
        for line in text.splitlines():
            line = line.strip()
            if line and "=" not in line and not line.startswith("#"):
                return line
    return ""


def load_openrouter_key() -> str:
    return _load_key("OPENROUTER_AI_API_KEY", "openrouter-api-key.txt", "OPENROUTER_AI_API_KEY")


def load_deepseek_key() -> str:
    return _load_key("DEEPSEEK_API_KEY", "deepseek-api-key.txt", "DEEPSEEK_API_KEY")


def load_nvidia_key() -> str:
    # Env var is NVIDIA_API_KEY_CODING (a dedicated NVIDIA NIM key for code/text
    # generation). Accept the singular filename (preferred, consistent with the
    # other key files) and the legacy plural for back-compat (TICKET-0043).
    for fname in ("nvidia-api-key.txt", "nvidia-api-keys.txt"):
        key = _load_key("NVIDIA_API_KEY_CODING", fname, "NVIDIA_API_KEY_CODING")
        if key:
            return key
    return ""


def _extract_content(resp_json):
    """Pull the ANSWER text from a chat completion.

    Only message.content is the answer. A reasoning model may leave content empty
    and put its chain-of-thought in message.reasoning -- that internal monologue is
    NOT the answer (returning it produces 4000-char "The user wants..." blobs as
    blog copy). Treat empty content as failure so _post_chat retries and, on a
    persistent empty, chat() fails over to a provider that emits real content.
    """
    try:
        msg = resp_json["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return ""
    content = msg.get("content")
    if content and content.strip():
        return content
    return ""


def _post_chat(url, api_key, model, messages, max_tokens, temperature, timeout,
               extra_headers=None, max_retries=2, extra_payload=None):
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        # Give reasoning models thinking headroom (see REASONING_TOKEN_FLOOR).
        "max_tokens": max(max_tokens, REASONING_TOKEN_FLOOR),
    }
    if extra_payload:
        payload.update(extra_payload)
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code in (429, 503):
                last_err = RuntimeError("HTTP " + str(resp.status_code) + ": " + resp.text[:300])
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError as e:
                # Malformed body (e.g. an HTML error page) is not a
                # requests.RequestException; treat it as a retryable error so the
                # retry/fallback chain still runs (TICKET-0022).
                last_err = RuntimeError("non-JSON response from " + str(model) + ": " + str(e)[:120])
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise last_err
            text = _extract_content(data)
            if not text.strip():
                last_err = RuntimeError("empty content from " + str(model))
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise last_err
            return text
        except requests.exceptions.HTTPError as e:
            # Non-transient client/server errors (400/401/403/404 etc.) are not
            # worth retrying -- 429/503 were already handled above. Fail fast so a
            # bad request (e.g. an unsupported param) surfaces immediately instead
            # of burning the backoff budget (TICKET-0080).
            raise
        except requests.exceptions.RequestException as e:
            # Connectivity/timeout errors ARE transient -> retry with backoff.
            last_err = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise
    if last_err:
        raise last_err
    raise RuntimeError("chat failed")


def call_openrouter(messages, max_tokens=2048, temperature=0.1, model=None, timeout=120):
    key = load_openrouter_key()
    if not key:
        raise RuntimeError("OPENROUTER_AI_API_KEY not found (env or secrets file)")
    extra = {
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "https://localhost/vagabond-blog"),
        "X-Title": "Vagabond-Couple-Blog-Enhancer",
    }
    body = {}
    if OPENROUTER_REASONING_EFFORT:
        # "none" -> no reasoning, answer directly in message.content (writer wants
        # finished text, not chain-of-thought). Ignored by non-reasoning models.
        body["reasoning"] = {"effort": OPENROUTER_REASONING_EFFORT}
    if OPENROUTER_INCLUDE_USAGE:
        body["usage"] = {"include": True}
    return _post_chat(
        OPENROUTER_BASE_URL + "/chat/completions", key, model or OPENROUTER_MODEL,
        messages, max_tokens, temperature, timeout, extra_headers=extra,
        extra_payload=body or None,
    )


def call_deepseek(messages, max_tokens=2048, temperature=0.1, model="deepseek-v4-pro", timeout=120):
    key = load_deepseek_key()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not found")
    return _post_chat(
        DEEPSEEK_BASE_URL + "/chat/completions", key, model,
        messages, max_tokens, temperature, timeout,
    )


def call_nvidia(messages, max_tokens=2048, temperature=0.1,
                model="nvidia/nemotron-3-super-120b-a12b", timeout=120):
    key = load_nvidia_key()
    if not key:
        raise RuntimeError("NVIDIA_API_KEY_CODING not found")
    return _post_chat(
        NVIDIA_BASE_URL + "/chat/completions", key, model,
        messages, max_tokens, temperature, timeout,
    )


def chat(messages, max_tokens=2048, temperature=0.1, allow_fallback=True,
         prefer_deepseek=False):
    """
    Send a chat completion across the writer provider chain, moving on when a
    provider errors so the pipeline keeps going.

    Default order: OpenRouter (free) -> DeepSeek -> NVIDIA.
    prefer_deepseek=True reorders to DeepSeek -> OpenRouter -> NVIDIA. The review
    loop sets this after openrouter/free repeatedly fails a node's OBJECTIVE
    (deterministic) checks: the free model is a weak instruction-follower on
    tight-constraint nodes, so we escalate the writer to the reliable provider
    rather than burning rounds -- mirroring the reviewer's universal fallback.

    Returns: (content_str, provider_label). Raises only if every provider fails.
    """
    providers = [
        ("openrouter:" + OPENROUTER_MODEL, lambda: call_openrouter(messages, max_tokens, temperature)),
        ("deepseek-v4-pro", lambda: call_deepseek(messages, max_tokens, temperature)),
        ("nvidia-nemotron", lambda: call_nvidia(messages, max_tokens, temperature)),
    ]
    if prefer_deepseek:
        providers[0], providers[1] = providers[1], providers[0]

    errors = []
    for i, (label, call) in enumerate(providers):
        try:
            return call(), label
        except Exception as e:
            errors.append(label + "=" + str(e))
            if not allow_fallback:
                raise
            nxt = providers[i + 1][0] if i + 1 < len(providers) else "none"
            safe_print("[writer] " + label + " failed (" + str(e) + "); trying " + nxt + "...")

    raise RuntimeError("All writer providers failed: " + " | ".join(errors))


if __name__ == "__main__":
    content, provider = chat(
        [{"role": "user", "content": "Reply with exactly: PIPELINE OK"}],
        max_tokens=256,
    )
    safe_print("[" + provider + "] " + content)
