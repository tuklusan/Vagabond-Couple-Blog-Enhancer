#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
NVIDIA NIM vision-model client for the 1E visual image audit (TICKET-0167).

The one place the pipeline actually LOOKS at a photograph: fetch the image
(downscaled), inline it base64 into an OpenAI-style chat request against NIM's
vision models, and get a structured JSON verdict back. Text-only providers
(OpenRouter/DeepSeek) cannot do this, so the writer/reviewer fallback chains do
not apply here -- this is a NIM-only capability, using the same
NVIDIA_API_KEY_CODING credential the writer fallback already loads.

Model chain (first success wins; primary/backups all verified available on this
account via /v1/models): a large vision-instruct model first for judgment
quality, then smaller multimodal fallbacks for availability.
"""
import base64
import json
import os
import re
import time

import requests

from . import writer_client
from .context_extractor import _is_safe_public_url, safe_get

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Overridable primary; the fallbacks stay fixed (all verified on this account).
VLM_MODELS = [
    os.environ.get("ORCH_VLM_MODEL", "meta/llama-3.2-90b-vision-instruct"),
    "nvidia/nemotron-nano-12b-v2-vl",
    "microsoft/phi-4-multimodal-instruct",
]

# Blogger/googleusercontent size token in the URL path: /s1600/ or /w640-h480/.
# Rewriting it re-requests the SAME image at a smaller size, and the -rj option
# suffix forces a server-side JPEG re-encode -- verified live: a 546KB PNG
# comes back as an 87KB JPEG at /s512-rj/. The audit only needs enough pixels
# to see WHAT is in the frame, and NIM's inline-base64 transport has a hard
# payload ceiling (~180KB), so fetch small + JPEG on purpose.
_SIZE_TOKEN_RE = re.compile(r"/(s\d+|w\d+-h\d+)(-[a-z0-9]+)*(?=/)")
FETCH_SIZE_TOKEN = "s512-rj"
RETRY_SIZE_TOKEN = "s320-rj"
MAX_IMAGE_BYTES = 160_000        # stay under NIM's inline-b64 request ceiling
FETCH_TIMEOUT = 20

# Some image hosts (observed live: upload.wikimedia.org, 403) reject requests
# bearing the default python-requests User-Agent. Identify honestly per
# Wikimedia's UA policy: tool name + contact URL (TICKET-0170).
FETCH_HEADERS = {"User-Agent": "VagabondCoupleBlogEnhancer/1.0 "
                               "(+https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer; "
                               "image caption audit)"}


# Wikimedia Commons original: .../wikipedia/commons/<x>/<xy>/<File.ext>
# Its thumbnail form:          .../wikipedia/commons/thumb/<x>/<xy>/<File.ext>/<N>px-<File.ext>
_WIKIMEDIA_RE = re.compile(
    r"^(https://upload\.wikimedia\.org/wikipedia/[^/]+)/([0-9a-f])/([0-9a-f]{2})/([^/]+)$")


def downscaled_url(src, token=FETCH_SIZE_TOKEN):
    """Rewrite an image URL to the audit fetch size: Blogger URLs via their
    size token; Wikimedia originals via the thumbnail path scheme (observed
    live: a post embedding a 5.6MB Commons original with no size token,
    TICKET-0170). Unrecognized URLs are returned unchanged (the size cap in
    fetch_image still protects the request payload)."""
    src = str(src or "")
    m = _WIKIMEDIA_RE.match(src)
    if m:
        # Wikimedia only serves the standard thumbnail widths to unauthenticated
        # clients (rejects arbitrary px with 400, verified live); 500/250 are on
        # the standard list.
        px = "250" if token == RETRY_SIZE_TOKEN else "500"
        return (m.group(1) + "/thumb/" + m.group(2) + "/" + m.group(3) + "/"
                + m.group(4) + "/" + px + "px-" + m.group(4))
    return _SIZE_TOKEN_RE.sub("/" + token, src, count=1)


def fetch_image(src):
    """Fetch an image for auditing: SSRF-guarded (TICKET-0159 helper), fetched
    at a downscaled size as a forced JPEG, hard-capped in bytes, with one
    smaller-size retry on either a transient error or an oversized response.
    Returns (bytes, mime) or (None, reason) on any failure -- never raises."""
    last_reason = "no size variant succeeded"
    for token in (FETCH_SIZE_TOKEN, RETRY_SIZE_TOKEN):
        url = downscaled_url(src, token)
        if not _is_safe_public_url(url):
            return None, "unsafe url"
        try:
            # safe_get re-validates every redirect hop -- a public image host
            # 302-ing to a private/metadata address is refused (TICKET-0178).
            resp = safe_get(url, timeout=FETCH_TIMEOUT, headers=FETCH_HEADERS)
            resp.raise_for_status()
        except ValueError:
            return None, "unsafe url"
        except requests.exceptions.RequestException as e:
            last_reason = "fetch failed: " + str(e)[:120]
            continue
        mime = (resp.headers.get("content-type") or "").split(";")[0].strip()
        if not mime.startswith("image/"):
            last_reason = "not an image: " + (mime or "no content-type")
            continue
        if len(resp.content) > MAX_IMAGE_BYTES:
            last_reason = "too large (" + str(len(resp.content)) + " bytes at " + token + ")"
            continue
        return resp.content, mime
    return None, last_reason


def _parse_json_verdict(text):
    """Tolerant JSON extraction (same approach as the dev-review harness): try a
    strict parse, else scan for the first balanced object."""
    if not (text or "").strip():
        return None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    depth, start = 0, None
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
                    if isinstance(obj, dict):
                        return obj
                except Exception:
                    pass
    return None


def inspect_image(image_bytes, mime, prompt, max_tokens=1100, temperature=0.0,
                  timeout=90, retries=2):
    """Send one image + one instruction to the NIM vision chain; return
    (verdict_dict_or_None, raw_text, model_used). Retries 429/5xx per model with
    backoff; an empty reply OR a reply that fails JSON parsing (markdown prose,
    truncated object) falls through to the next model in the chain -- observed
    live: models occasionally answer in markdown despite the JSON-only
    instruction, and a different model then answers correctly."""
    key = writer_client.load_nvidia_key()
    if not key:
        return None, "NVIDIA_API_KEY_CODING not found", ""
    b64 = base64.b64encode(image_bytes).decode()
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:" + mime + ";base64," + b64}},
    ]}]
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    last_err = ""
    for model in VLM_MODELS:
        payload = {"model": model, "messages": messages,
                   "max_tokens": max_tokens, "temperature": temperature}
        for attempt in range(retries + 1):
            try:
                resp = requests.post(NVIDIA_BASE_URL + "/chat/completions",
                                     headers=headers, json=payload, timeout=timeout)
                if resp.status_code in (429, 500, 502, 503):
                    last_err = model + ": HTTP " + str(resp.status_code)
                    if attempt < retries:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    break                     # next model
                resp.raise_for_status()
                try:
                    text = resp.json()["choices"][0]["message"].get("content") or ""
                except (ValueError, KeyError, IndexError, TypeError) as e:
                    # A 200 with a malformed/non-JSON body must fail over to the
                    # next model, not raise out of the audit loop (TICKET-0168).
                    last_err = model + ": malformed response: " + str(e)[:80]
                    break                     # next model
                if not text.strip():
                    last_err = model + ": empty content"
                    break                     # next model
                verdict = _parse_json_verdict(text)
                if verdict is None:
                    last_err = model + ": unparseable verdict: " + text[:80]
                    break                     # next model may answer in clean JSON
                return verdict, text, model
            except requests.exceptions.RequestException as e:
                last_err = model + ": " + str(e)[:120]
                if attempt < retries:
                    time.sleep(2 ** (attempt + 1))
                    continue
                break                         # next model
    return None, last_err, ""
