#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Phase 1 / 1J -- visual image audit (TICKET-0167).

For every photograph in the post, actually LOOK at the image (NIM vision model,
vision_client) and judge whether its alt text, title attribute, and visible
caption agree with what is in the frame. The failure mode this catches: a
caption/alt/title that describes a DIFFERENT photograph (wrong subject entirely
-- e.g. text says totem pole, frame shows a ship's dining room), which no
text-only pass can ever detect.

Anti-hallucination policy (the heart of this pass):
  * A vision model CANNOT verify proper nouns from pixels -- any glacier looks
    like "a glacier"; a dock in Vancouver looks like a dock anywhere. So the
    verdict scale is MATCH / PLAUSIBLE / CONTRADICTED, and only CONTRADICTED
    (the visible subject category makes the text impossible) triggers any
    correction. Unverifiable-but-consistent specifics stay untouched.
  * Corrections must be grounded ONLY in what is visible plus the parts of the
    original text the image does NOT contradict (keep location words unless the
    location itself is what's contradicted).
  * Corrections are gated deterministically before application: writing-rules
    clean (forbidden words / narrator), and caption text is only replaced when
    the caption cell contains no <a> links (G3 href preservation -- a linked
    caption is recorded as a finding for the operator instead of auto-edited).

Resumability (G4): verdicts are cached per-image in the run's
`1J_image_audit_progress` artifact as they land, so a 400-photo audit that
dies at image 250 resumes from 251, and a re-run never re-pays for images
already audited. Each cached verdict carries a digest of the alt/title/caption
it was judged against; if that text has changed since (operator edit, applied
correction), the entry is stale and the image is re-audited (TICKET-0169).
"""
import hashlib
import json
import os
import re

from bs4 import BeautifulSoup

from . import vision_client
from .nodes import writing_rules_findings

# 0 = audit every image. A positive value caps the number of images audited
# (useful for smoke tests and metered runs).
try:
    AUDIT_LIMIT = int(os.environ.get("ORCH_IMAGE_AUDIT_LIMIT", "0"))
except ValueError:
    AUDIT_LIMIT = 0

# Consecutive per-image failures before concluding the provider/key/network is
# down for this run and stopping early instead of burning full retry chains on
# every remaining image (TICKET-0168). Scattered failures reset the streak.
MAX_CONSECUTIVE_FAILURES = 5

# Whether gated corrections are APPLIED at Phase 5 (1) or recorded as
# findings-only for the operator (0, default). Human review of the first full
# 318-correction run graded ~50% genuine improvements but ~30% information-
# degrading and ~2% grammatical nonsense (TICKET-0175) -- until the visual
# certification loop lands, detection is trustworthy but auto-application is
# opt-in for supervised runs only.
APPLY_CORRECTIONS = os.environ.get("ORCH_IMAGE_AUDIT_APPLY", "0") == "1"

_VERDICT_STATUSES = ("MATCH", "PLAUSIBLE", "CONTRADICTED")

_PROMPT = (
    "You are auditing a travel-blog photograph against the text that describes it. "
    "First, describe what is actually VISIBLE in the frame (subject, setting, any "
    "readable signage) in UNDER 35 words. Then judge each provided text against the "
    "image:\n"
    "  MATCH -- the visible content clearly agrees with the text.\n"
    "  PLAUSIBLE -- nothing visible makes the text impossible. This is the default. "
    "You CANNOT verify proper nouns from pixels alone -- a glacier photo cannot "
    "confirm WHICH glacier -- so place names, ship names, dates, coordinates, and "
    "history default to PLAUSIBLE. Text mentioning things OUTSIDE or BEYOND the "
    "frame (a bridge not shown, a wake still forming, what happened next), artistic "
    "or figurative phrasing, and partial views are all PLAUSIBLE, not contradicted.\n"
    "  CONTRADICTED -- reserve for a WRONG PRIMARY SUBJECT only: the main thing the "
    "text claims to show is absent and something categorically different fills the "
    "frame (text says totem pole, frame shows a dining room; text says aircraft "
    "cabin, frame shows an airport terminal). If the text's primary subject is "
    "visible at all, it is NOT contradicted. You also CANNOT verify the VANTAGE "
    "POINT -- whether a skyline was shot from a ship, the shore, or a window is "
    "invisible in the frame; never flag a vantage claim and never assert a "
    "different vantage in a correction.\n"
    "For each CONTRADICTED text, write a corrected version: describe the visible "
    "primary subject, and KEEP the original's place names, coordinates, and journey "
    "context words VERBATIM unless the location itself is the contradiction -- a "
    "correction that drops 'Vancouver, BC' from a photo taken in Vancouver is wrong. "
    "Narrator voice we/us, no first person singular. Keep each reason under 20 "
    "words and each corrected text under 60 words.\n"
    "Reply with ONLY this JSON (no prose, no markdown outside it):\n"
    '{"visible_description": "...",'
    ' "alt": {"status": "MATCH|PLAUSIBLE|CONTRADICTED", "reason": "...", "corrected": ""},'
    ' "title": {"status": "...", "reason": "...", "corrected": ""},'
    ' "caption": {"status": "...", "reason": "...", "corrected": ""}}\n'
)


def collect_image_records(html):
    """Deterministic: every <img> in the document paired with its alt, title,
    and (when the image sits in a Blogger tr-caption-container table) the
    caption cell's text and whether that cell contains <a> links."""
    soup = BeautifulSoup(html, "html.parser")
    records = []
    for idx, img in enumerate(soup.find_all("img")):
        rec = {"index": idx, "src": img.get("src") or "",
               "alt": img.get("alt") or "", "title": img.get("title") or "",
               "caption": "", "caption_has_links": False}
        table = img.find_parent("table", class_=lambda c: c and "tr-caption-container" in c)
        if table:
            cap = table.find("td", class_=lambda c: c and "tr-caption" in c)
            if cap:
                rec["caption"] = cap.get_text(" ", strip=True)
                rec["caption_has_links"] = bool(cap.find("a"))
        records.append(rec)
    return records


def _build_prompt(rec):
    return (_PROMPT
            + "\nALT TEXT: " + (rec["alt"] or "(none)")
            + "\nTITLE ATTRIBUTE: " + (rec["title"] or "(none)")
            + "\nVISIBLE CAPTION: " + (rec["caption"] or "(none)"))


def _transcript(state, model, content):
    """Best-effort append to the run's AI-communications transcript (0140).
    The transcript is an audit trail, not a load-bearing artifact -- a disk/IO
    hiccup writing it must never abort the image audit itself."""
    if not state:
        return
    try:
        state.log_ai_call("1J_image_audit", "orchestrator",
                          "vlm:" + (model or "none"), model or "none", content)
    except Exception:
        pass


def _text_key(rec):
    """Digest of the text a verdict was judged against. A cached verdict is
    only valid for the alt/title/caption it actually saw -- if any of them has
    changed since (operator edit, prior applied correction), the cache entry is
    stale and the image must be re-audited (TICKET-0169)."""
    blob = "\x1f".join((rec["alt"], rec["title"], rec["caption"]))
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()[:16]


def _clean_field(verdict, field):
    """Normalize one field's sub-verdict; unknown/missing statuses degrade to
    PLAUSIBLE (never invent a contradiction the model didn't assert)."""
    sub = verdict.get(field) if isinstance(verdict, dict) else None
    if not isinstance(sub, dict):
        return {"status": "PLAUSIBLE", "reason": "no verdict", "corrected": ""}
    status = str(sub.get("status", "")).upper()
    if status not in _VERDICT_STATUSES:
        status = "PLAUSIBLE"
    return {"status": status, "reason": str(sub.get("reason", ""))[:300],
            "corrected": str(sub.get("corrected", "")).strip()}


_GEO_STOPWORDS = {"The", "This", "That", "These", "Those", "Our", "Note", "Watch",
                  "One", "Two", "Three", "There", "Here", "What", "When", "Where"}


def _proper_tokens(text):
    """Capitalized/proper-noun-ish tokens (place names, ship names, 'BC')."""
    return {w for w in re.findall(r"\b(?:[A-Z][a-z]{2,}|[A-Z]{2,})\b", text or "")
            if w not in _GEO_STOPWORDS}


def _acceptable_correction(original, corrected, require_context=False):
    """Deterministic gate on a proposed correction: non-empty, actually
    different, sane length, writing-rules clean (forbidden words/narrator),
    and -- for captions -- context-retaining. The VLM's output is generated
    prose, so it gets the same mechanical rules every other generative output
    gets.

    Context retention (require_context=True, used for CAPTIONS): if the
    original names places/entities (proper tokens) the correction must keep at
    least one of them. Observed live: the model occasionally 'corrects' a
    caption down to a bare visual description ('City skyline across water...'),
    silently deleting 'Vancouver' -- an SEO and information REGRESSION even
    when the flag itself was right. A caption correction sharing no proper noun
    with the original is either that regression or a location-swap the model
    cannot actually see in pixels; both are rejected (the finding is still
    recorded for the operator). Alt/title corrections are exempt: for a
    wrong-primary-subject photo the honest fix often HAS no legitimate claim to
    the original's place words (a dining-room frame must not keep 'Stanley
    Park'), and the prompt already instructs retention where it applies."""
    if not corrected or corrected == original:
        return False
    # No-op suppression (TICKET-0175): a "correction" differing only in case or
    # punctuation is churn, not a fix (observed live: punctuation-only rewrites).
    _norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", s.lower())).strip()
    if _norm(corrected) == _norm(original):
        return False
    if len(corrected) < 8 or len(corrected) > 400:
        return False
    if writing_rules_findings(corrected):
        return False
    if require_context:
        orig_proper = _proper_tokens(original)
        if orig_proper and not (orig_proper & _proper_tokens(corrected)):
            return False
    return True


def audit_images(html, state=None, limit=None, log=None):
    """Run the 1J audit over every image record. Returns the artifact dict:
    counts, per-image findings for anything CONTRADICTED, and the corrections
    list (only gated, applicable corrections) for Phase 5 application."""
    limit = AUDIT_LIMIT if limit is None else limit
    _log = log or (lambda m: None)
    records = collect_image_records(html)
    progress = {}
    if state:
        progress = state.read_artifact("1J_image_audit_progress") or {}
    audited = fetch_failures = review_failures = consecutive_failures = 0
    findings, corrections = [], []
    for rec in records:
        if limit and audited >= limit:
            break
        src = rec["src"]
        if not src:
            continue
        cached = progress.get(src)
        if cached and cached.get("text_key") == _text_key(rec):
            verdict = cached
            consecutive_failures = 0
        else:
            # Per-image resilience (TICKET-0168, same precedent as TICKET-0143's
            # per-item enhancers): one bad image/response must never abandon the
            # rest of the audit -- catch, count, continue. A run of consecutive
            # hard failures, though, means the provider/key/network is down for
            # good; stop burning retries on the remaining images (the progress
            # cache lets the next run resume right here).
            try:
                img_bytes, mime = vision_client.fetch_image(src)
                if img_bytes is None:
                    fetch_failures += 1
                    consecutive_failures += 1
                    _log("1J image " + str(rec["index"]) + ": fetch failed (" + str(mime) + ")")
                    _transcript(state, None, "IMAGE: " + src
                                + "\nFETCH FAILED (no VLM call made): " + str(mime))
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        _log("1J: " + str(consecutive_failures)
                             + " consecutive failures -- provider/network down; stopping audit early")
                        break
                    continue
                raw_verdict, raw_text, model = vision_client.inspect_image(
                    img_bytes, mime, _build_prompt(rec))
            except Exception as e:
                review_failures += 1
                consecutive_failures += 1
                _log("1J image " + str(rec["index"]) + ": error (" + str(e)[:120] + ")")
                _transcript(state, None, "IMAGE: " + src
                            + "\nERROR (call aborted): " + str(e)[:300])
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    _log("1J: " + str(consecutive_failures)
                         + " consecutive failures -- provider/network down; stopping audit early")
                    break
                continue
            _transcript(state, model, "IMAGE: " + src + "\nPROMPT:\n" + _build_prompt(rec)
                        + "\n\nRESPONSE:\n" + (raw_text or "")[:4000])
            if raw_verdict is None:
                review_failures += 1
                consecutive_failures += 1
                _log("1J image " + str(rec["index"]) + ": no verdict (" + (raw_text or "")[:80] + ")")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    _log("1J: " + str(consecutive_failures)
                         + " consecutive failures -- provider/network down; stopping audit early")
                    break
                continue
            consecutive_failures = 0
            verdict = {"visible_description": str(raw_verdict.get("visible_description", ""))[:400],
                       "model": model, "text_key": _text_key(rec)}
            for field in ("alt", "title", "caption"):
                verdict[field] = _clean_field(raw_verdict, field)
                sub = verdict[field]
                # Visual certification (TICKET-0175): every proposal that could
                # ever be applied gets a SECOND VLM opinion (rotated model chain)
                # while the image bytes are in hand -- accuracy, natural prose,
                # and no unjustified proper-noun/vantage deletion. Fails closed:
                # an uncertified proposal stays findings-only. The result is
                # cached in the verdict, so resumed runs never re-pay for it.
                if (sub["status"] == "CONTRADICTED"
                        and _acceptable_correction(rec[field], sub["corrected"],
                                                   require_context=(field == "caption"))):
                    try:
                        approved, why = vision_client.certify_correction(
                            img_bytes, mime, field, rec[field], sub["corrected"])
                    except Exception as e:
                        approved, why = False, "certifier error: " + str(e)[:120]
                    sub["certified"] = approved
                    sub["certify_reason"] = why
                    _transcript(state, "certifier",
                                "IMAGE: " + src + "\nCERTIFY " + field.upper()
                                + "\nPROPOSED: " + sub["corrected"][:300]
                                + "\nVERDICT: " + ("APPROVE" if approved else "REJECT")
                                + " -- " + why)
            progress[src] = verdict
            if state:
                state.save_artifact("1J_image_audit_progress", progress)
        audited += 1
        correction = {"src": src}
        for field in ("alt", "title", "caption"):
            sub = verdict[field]
            if sub["status"] != "CONTRADICTED":
                continue
            original = rec[field]
            finding = {"index": rec["index"], "src": src, "field": field,
                       "original": original[:200], "reason": sub["reason"],
                       "visible": verdict.get("visible_description", "")[:200],
                       "corrected": sub["corrected"][:300], "applied": False,
                       "certified": bool(sub.get("certified")),
                       "certify_reason": sub.get("certify_reason", "")}
            ok = (_acceptable_correction(original, sub["corrected"],
                                         require_context=(field == "caption"))
                  and bool(sub.get("certified")))   # uncertified -> findings-only (0175)
            if field == "caption" and rec["caption_has_links"]:
                ok = False           # linked caption: never auto-edit (G3); operator finding
                finding["reason"] += " [caption contains links -- not auto-edited]"
            if ok:
                correction[field] = sub["corrected"]
                finding["applied"] = True
            findings.append(finding)
        if len(correction) > 1:
            corrections.append(correction)
    return {
        "images_total": len(records),
        "images_audited": audited,
        "fetch_failures": fetch_failures,
        "review_failures": review_failures,
        "contradicted_count": len(findings),
        "findings": findings,
        # Findings-only by default (TICKET-0175): the corrections list is still
        # computed and recorded (so the operator sees exactly what WOULD change)
        # but Phase 5 only applies it when ORCH_IMAGE_AUDIT_APPLY=1.
        "corrections": corrections,
        "apply_enabled": APPLY_CORRECTIONS,
    }
