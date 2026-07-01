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
            if line.startswith(prefix + "="):
                return line[len(prefix) + 1:].strip()
        raw = text.strip()
        if raw and "=" not in raw:
            return raw
    return ""


def load_openrouter_key() -> str:
    return _load_key("OPENROUTER_AI_API_KEY", "openrouter-api-key.txt", "OPENROUTER_AI_API_KEY")


def load_deepseek_key() -> str:
    return _load_key("DEEPSEEK_API_KEY", "deepseek-api-key.txt", "DEEPSEEK_API_KEY")


def load_nvidia_key() -> str:
    return _load_key("NVIDIA_API_KEY_CODING", "nvidia-api-keys.txt", "NVIDIA_API_KEY_CODING")


def _extract_content(resp_json):
    """Pull text from a chat completion, tolerating reasoning-only messages."""
    try:
        msg = resp_json["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return ""
    content = msg.get("content")
    if content and content.strip():
        return content
    reasoning = msg.get("reasoning")
    if reasoning and reasoning.strip():
        return reasoning
    return ""


def _post_chat(url, api_key, model, messages, max_tokens, temperature, timeout,
               extra_headers=None, max_retries=2):
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
        "max_tokens": max_tokens,
    }
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
            text = _extract_content(resp.json())
            if not text.strip():
                last_err = RuntimeError("empty content from " + str(model))
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise last_err
            return text
        except requests.exceptions.RequestException as e:
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
    return _post_chat(
        OPENROUTER_BASE_URL + "/chat/completions", key, model or OPENROUTER_MODEL,
        messages, max_tokens, temperature, timeout, extra_headers=extra,
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


def chat(messages, max_tokens=2048, temperature=0.1, allow_fallback=True):
    """
    Send a chat completion. OpenRouter first; on failure fall back to DeepSeek
    then NVIDIA so the pipeline keeps moving.

    Returns: (content_str, provider_label)
    Raises RuntimeError only if every provider fails.
    """
    errors = []
    try:
        return call_openrouter(messages, max_tokens, temperature), "openrouter:" + OPENROUTER_MODEL
    except Exception as e:
        errors.append("openrouter=" + str(e))
        if not allow_fallback:
            raise
        safe_print("[writer] OpenRouter failed (" + str(e) + "); trying DeepSeek...")

    try:
        return call_deepseek(messages, max_tokens, temperature), "deepseek-v4-pro"
    except Exception as e:
        errors.append("deepseek=" + str(e))
        safe_print("[writer] DeepSeek failed (" + str(e) + "); trying NVIDIA...")

    try:
        return call_nvidia(messages, max_tokens, temperature), "nvidia-nemotron"
    except Exception as e:
        errors.append("nvidia=" + str(e))

    raise RuntimeError("All writer providers failed: " + " | ".join(errors))


if __name__ == "__main__":
    content, provider = chat(
        [{"role": "user", "content": "Reply with exactly: PIPELINE OK"}],
        max_tokens=256,
    )
    safe_print("[" + provider + "] " + content)
