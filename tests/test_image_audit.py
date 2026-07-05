#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Tests for the 1J visual image audit (TICKET-0167). The VLM and network are
mocked -- these verify the deterministic halves: record collection, the
downscale URL rewrite, verdict gating (visible-contradiction only, writing
rules, linked captions), and the Phase 5 correction application.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator import assembler, image_audit, vision_client  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print((("[PASS] " if cond else "[FAIL] ") + name + " " + str(detail))
          .encode("ascii", "replace").decode("ascii"))
    if not cond:
        FAILS.append(name)


CAPTIONED = (
    '<table class="tr-caption-container"><tbody>'
    '<tr><td><a href="https://example.com/full.jpg">'
    '<img src="https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg" '
    'alt="Totem pole at Stanley Park" title="Stanley Park, Vancouver"/></a></td></tr>'
    '<tr><td class="tr-caption">Totem pole at Stanley Park, Vancouver</td></tr>'
    '</tbody></table>'
)
LINKED_CAPTION = (
    '<table class="tr-caption-container"><tbody>'
    '<tr><td><img src="https://blogger.googleusercontent.com/img/x/s1600/p2.jpg" '
    'alt="Ship dining room" title="MS Statendam dining"/></td></tr>'
    '<tr><td class="tr-caption">Watch: <a href="https://youtu.be/abc">dining room tour</a></td></tr>'
    '</tbody></table>'
)
HTML = "<html><body><!--more-->" + CAPTIONED + LINKED_CAPTION + "</body></html>"


def test_collect_records():
    recs = image_audit.collect_image_records(HTML)
    check("collect_two_records", len(recs) == 2, len(recs))
    check("collect_alt", recs[0]["alt"] == "Totem pole at Stanley Park")
    check("collect_caption", "Stanley Park" in recs[0]["caption"])
    check("collect_caption_no_links", recs[0]["caption_has_links"] is False)
    check("collect_caption_links_flagged", recs[1]["caption_has_links"] is True)


def test_collect_records_rejects_non_string_input():
    """TICKET-0193: a non-string html argument must not raise out of
    collect_image_records (previously a bare TypeError from BeautifulSoup)."""
    for bad in (None, 12345, [], {}):
        check("collect_non_string_safe " + repr(bad),
              image_audit.collect_image_records(bad) == [])


def test_downscaled_url():
    check("rewrite_w_h_token",
          vision_client.downscaled_url("https://x/img/w640-h480/p.jpg") == "https://x/img/s512-rj/p.jpg")
    check("rewrite_s_token",
          vision_client.downscaled_url("https://x/img/s1600/p.jpg") == "https://x/img/s512-rj/p.jpg")
    check("rewrite_token_with_options",
          vision_client.downscaled_url("https://x/img/s1600-rw/p.jpg") == "https://x/img/s512-rj/p.jpg")
    check("rewrite_retry_token",
          vision_client.downscaled_url("https://x/img/s1600/p.jpg", vision_client.RETRY_SIZE_TOKEN)
          == "https://x/img/s320-rj/p.jpg")
    check("no_token_unchanged",
          vision_client.downscaled_url("https://x/img/p.jpg") == "https://x/img/p.jpg")
    check("rewrite_wikimedia_thumb",
          vision_client.downscaled_url(
              "https://upload.wikimedia.org/wikipedia/commons/d/d5/MS_Statendam%28js%2902.jpg")
          == "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/"
             "MS_Statendam%28js%2902.jpg/500px-MS_Statendam%28js%2902.jpg")
    check("rewrite_wikimedia_retry_250px",
          "250px-" in vision_client.downscaled_url(
              "https://upload.wikimedia.org/wikipedia/commons/d/d5/x.jpg",
              vision_client.RETRY_SIZE_TOKEN))
    check("ua_header_present", "User-Agent" in vision_client.FETCH_HEADERS
          and "python-requests" not in vision_client.FETCH_HEADERS["User-Agent"])


def test_fetch_rejects_unsafe_url():
    data, reason = vision_client.fetch_image("http://169.254.169.254/latest/meta-data")
    check("fetch_ssrf_blocked", data is None and reason == "unsafe url", reason)
    data, reason = vision_client.fetch_image("file:///etc/passwd")
    check("fetch_scheme_blocked", data is None and reason == "unsafe url", reason)


def test_fetch_rejects_redirect_to_private():
    """A public host 302-ing to a private/metadata address must be refused at the
    redirect hop, not followed (TICKET-0178)."""
    from orchestrator import context_extractor
    import requests as _requests

    class FakeResp:
        status_code = 302
        headers = {"Location": "http://169.254.169.254/latest/meta-data"}
        def raise_for_status(self): pass

    orig_get = _requests.get
    calls = []

    def fake_get(url, **kw):
        calls.append((url, kw.get("allow_redirects")))
        return FakeResp()

    _requests.get = fake_get
    try:
        data, reason = vision_client.fetch_image(
            "https://blogger.googleusercontent.com/img/x/s1600/p.jpg")
    finally:
        _requests.get = orig_get
    check("redirect_ssrf_blocked", data is None and reason == "unsafe url", (data, reason))
    check("redirects_disabled_on_wire", all(ar is False for _u, ar in calls), calls)
    check("metadata_endpoint_never_fetched",
          not any("169.254.169.254" in u for u, _ar in calls), calls)


def _mock_vision(verdicts_by_src, certify=lambda field, orig, prop: (True, "ok")):
    """Patch fetch_image + inspect_image + certify_correction (the second-VLM
    certifier approves everything unless overridden); returns originals."""
    orig_fetch = vision_client.fetch_image
    orig_inspect = vision_client.inspect_image
    orig_certify = vision_client.certify_correction
    current = {"src": None}

    def fake_fetch(src):
        current["src"] = src
        return b"\xff\xd8fakejpeg", "image/jpeg"

    def fake_inspect(image_bytes, mime, prompt, **kw):
        v = verdicts_by_src.get(current["src"], {})
        return v, "raw", "mock-model"

    def fake_certify(image_bytes, mime, field, original, proposed, **kw):
        return certify(field, original, proposed)

    image_audit.vision_client.fetch_image = fake_fetch
    image_audit.vision_client.inspect_image = fake_inspect
    image_audit.vision_client.certify_correction = fake_certify
    return orig_fetch, orig_inspect, orig_certify


def _restore_vision(orig):
    image_audit.vision_client.fetch_image = orig[0]
    image_audit.vision_client.inspect_image = orig[1]
    image_audit.vision_client.certify_correction = orig[2]


def test_audit_contradicted_produces_gated_corrections():
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    src2 = "https://blogger.googleusercontent.com/img/x/s1600/p2.jpg"
    verdicts = {
        src1: {"visible_description": "A cruise ship dining room with set tables",
               "alt": {"status": "CONTRADICTED", "reason": "no totem pole visible",
                       "corrected": "Cruise ship dining room with set tables"},
               "title": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
               "caption": {"status": "CONTRADICTED", "reason": "no totem pole",
                           "corrected": "Dining room aboard the ship, en route from Vancouver"}},
        # linked caption contradicted -> must be finding-only, never applied
        src2: {"visible_description": "A totem pole in a park",
               "alt": {"status": "MATCH", "reason": "", "corrected": ""},
               "title": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
               "caption": {"status": "CONTRADICTED", "reason": "shows a totem pole",
                           "corrected": "Totem pole in Stanley Park"}},
    }
    orig = _mock_vision(verdicts)
    try:
        result = image_audit.audit_images(HTML, state=None, limit=0)
    finally:
        _restore_vision(orig)
    check("audit_counts", result["images_audited"] == 2 and result["images_total"] == 2, result)
    check("audit_findings", result["contradicted_count"] == 3, result["contradicted_count"])
    corr = {c["src"]: c for c in result["corrections"]}
    check("audit_correction_alt", corr.get(src1, {}).get("alt", "").startswith("Cruise ship"))
    check("audit_correction_caption", "Vancouver" in corr.get(src1, {}).get("caption", ""))
    check("audit_linked_caption_not_corrected", src2 not in corr, list(corr))
    linked = [f for f in result["findings"] if f["src"] == src2]
    check("audit_linked_caption_finding_recorded",
          len(linked) == 1 and linked[0]["applied"] is False)


def test_audit_rejects_rule_breaking_correction():
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    verdicts = {src1: {
        "visible_description": "x",
        "alt": {"status": "CONTRADICTED", "reason": "r",
                "corrected": "I saw a nestled realm of tapestry"},  # forbidden + first person
        "title": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
        "caption": {"status": "PLAUSIBLE", "reason": "", "corrected": ""}}}
    orig = _mock_vision(verdicts)
    try:
        result = image_audit.audit_images(CAPTIONED, state=None, limit=0)
    finally:
        _restore_vision(orig)
    check("audit_rule_breaker_finding_kept", result["contradicted_count"] == 1)
    check("audit_rule_breaker_not_applied", result["corrections"] == [], result["corrections"])


def test_unknown_status_degrades_to_plausible():
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    verdicts = {src1: {"alt": {"status": "BANANAS", "corrected": "whatever"},
                       "title": "not-a-dict", "caption": None}}
    orig = _mock_vision(verdicts)
    try:
        result = image_audit.audit_images(CAPTIONED, state=None, limit=0)
    finally:
        _restore_vision(orig)
    check("audit_unknown_status_safe",
          result["contradicted_count"] == 0 and result["corrections"] == [], result)


def test_audit_survives_per_image_exception():
    """One raising image must not abandon the rest of the audit (TICKET-0168)."""
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    src2 = "https://blogger.googleusercontent.com/img/x/s1600/p2.jpg"
    orig_fetch, orig_inspect = vision_client.fetch_image, vision_client.inspect_image
    current = {"src": None}

    def fake_fetch(src):
        current["src"] = src
        return b"\xff\xd8fakejpeg", "image/jpeg"

    def fake_inspect(image_bytes, mime, prompt, **kw):
        if current["src"] == src1:
            raise RuntimeError("simulated malformed provider response")
        return {"visible_description": "x",
                "alt": {"status": "MATCH", "reason": "", "corrected": ""},
                "title": {"status": "MATCH", "reason": "", "corrected": ""},
                "caption": {"status": "MATCH", "reason": "", "corrected": ""}}, "raw", "mock"

    image_audit.vision_client.fetch_image = fake_fetch
    image_audit.vision_client.inspect_image = fake_inspect
    try:
        result = image_audit.audit_images(HTML, state=None, limit=0)
    finally:
        image_audit.vision_client.fetch_image = orig_fetch
        image_audit.vision_client.inspect_image = orig_inspect
    check("exception_counted_as_review_failure", result["review_failures"] == 1, result)
    check("exception_did_not_abort_audit", result["images_audited"] == 1, result)


def test_audit_stops_after_consecutive_failures():
    """A dead provider must stop the audit early, not retry every image."""
    many = "<html><body><!--more-->" + "".join(
        '<img src="https://blogger.googleusercontent.com/img/x/s1600/img%d.jpg"/>' % i
        for i in range(10)) + "</body></html>"
    orig_fetch = vision_client.fetch_image
    calls = {"n": 0}

    def dead_fetch(src):
        calls["n"] += 1
        return None, "fetch failed: simulated outage"

    image_audit.vision_client.fetch_image = dead_fetch
    try:
        result = image_audit.audit_images(many, state=None, limit=0)
    finally:
        image_audit.vision_client.fetch_image = orig_fetch
    check("dead_provider_stops_early",
          calls["n"] == image_audit.MAX_CONSECUTIVE_FAILURES, calls["n"])
    check("dead_provider_failures_recorded",
          result["fetch_failures"] == image_audit.MAX_CONSECUTIVE_FAILURES, result)


class _FakeState:
    """Just enough of RunState for the progress-cache/transcript tests."""
    def __init__(self, artifacts=None, transcript_raises=False):
        self.artifacts = dict(artifacts or {})
        self.transcript = []
        self.transcript_raises = transcript_raises

    def read_artifact(self, name):
        return self.artifacts.get(name)

    def save_artifact(self, name, obj):
        self.artifacts[name] = obj

    def log_ai_call(self, node_id, source, target, provider, content):
        if self.transcript_raises:
            raise IOError("simulated transcript disk failure")
        self.transcript.append(content)


def test_failure_paths_logged_to_transcript():
    """Fetch failures and per-image exceptions land in ai_transcript.txt too,
    and a transcript write failure never aborts the audit."""
    orig_fetch, orig_inspect = vision_client.fetch_image, vision_client.inspect_image
    current = {"src": None}

    def fake_fetch(src):
        current["src"] = src
        if "p1" in src:
            return None, "fetch failed: simulated 404"
        return b"\xff\xd8fakejpeg", "image/jpeg"

    def fake_inspect(image_bytes, mime, prompt, **kw):
        raise RuntimeError("simulated provider explosion")

    image_audit.vision_client.fetch_image = fake_fetch
    image_audit.vision_client.inspect_image = fake_inspect
    try:
        state = _FakeState()
        result = image_audit.audit_images(HTML, state=state, limit=0)
        check("transcript_has_fetch_failure",
              any("FETCH FAILED" in t and "simulated 404" in t for t in state.transcript),
              state.transcript)
        check("transcript_has_error_entry",
              any("ERROR (call aborted)" in t and "provider explosion" in t
                  for t in state.transcript), state.transcript)
        # transcript write failure must not abort the audit
        state2 = _FakeState(transcript_raises=True)
        result2 = image_audit.audit_images(HTML, state=state2, limit=0)
        check("transcript_failure_never_aborts_audit",
              result2["fetch_failures"] == 1 and result2["review_failures"] == 1, result2)
    finally:
        image_audit.vision_client.fetch_image = orig_fetch
        image_audit.vision_client.inspect_image = orig_inspect


def test_progress_cache_reuse_and_staleness():
    """A cached verdict is reused only for the exact alt/title/caption it was
    judged against; changed text forces a re-audit (TICKET-0169)."""
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    clean = {"status": "MATCH", "reason": "", "corrected": ""}
    verdict = {"visible_description": "x", "model": "mock",
               "alt": clean, "title": clean, "caption": clean}
    rec = image_audit.collect_image_records(CAPTIONED)[0]
    fresh_key = image_audit._text_key(rec)

    calls = {"n": 0}
    orig_fetch, orig_inspect = vision_client.fetch_image, vision_client.inspect_image

    def fake_fetch(src):
        return b"\xff\xd8fakejpeg", "image/jpeg"

    def fake_inspect(image_bytes, mime, prompt, **kw):
        calls["n"] += 1
        return {"visible_description": "x", "alt": clean, "title": clean,
                "caption": clean}, "raw", "mock"

    image_audit.vision_client.fetch_image = fake_fetch
    image_audit.vision_client.inspect_image = fake_inspect
    try:
        # 1) cache entry judged against the CURRENT text -> reused, no VLM call
        state = _FakeState({"1J_image_audit_progress":
                            {src1: dict(verdict, text_key=fresh_key)}})
        result = image_audit.audit_images(CAPTIONED, state=state, limit=0)
        check("cache_hit_no_vlm_call", calls["n"] == 0 and result["images_audited"] == 1,
              (calls["n"], result["images_audited"]))
        # 2) cache entry judged against STALE text -> re-audited
        state = _FakeState({"1J_image_audit_progress":
                            {src1: dict(verdict, text_key="0123456789abcdef")}})
        result = image_audit.audit_images(CAPTIONED, state=state, limit=0)
        check("cache_stale_reaudited", calls["n"] == 1 and result["images_audited"] == 1,
              (calls["n"], result["images_audited"]))
        # and the refreshed entry carries the current text_key
        refreshed = state.artifacts["1J_image_audit_progress"][src1]
        check("cache_refreshed_key", refreshed.get("text_key") == fresh_key)
    finally:
        image_audit.vision_client.fetch_image = orig_fetch
        image_audit.vision_client.inspect_image = orig_inspect


def test_certifier_rejection_demotes_to_finding_only():
    """A proposal the second-VLM certifier rejects must never be applied
    (TICKET-0175) -- and the rejection reason is recorded."""
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    verdicts = {src1: {
        "visible_description": "a dining room",
        "alt": {"status": "CONTRADICTED", "reason": "wrong subject",
                "corrected": "A body of water entered cruise service in 2011"},
        "title": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
        "caption": {"status": "PLAUSIBLE", "reason": "", "corrected": ""}}}
    orig = _mock_vision(verdicts,
                        certify=lambda f, o, p: (False, "generic-noun substitution nonsense"))
    try:
        result = image_audit.audit_images(CAPTIONED, state=None, limit=0)
    finally:
        _restore_vision(orig)
    check("certifier_reject_no_correction", result["corrections"] == [], result["corrections"])
    f = result["findings"][0]
    check("certifier_reject_finding_kept",
          f["applied"] is False and f["certified"] is False
          and "nonsense" in f["certify_reason"], f)


def test_certifier_approval_allows_correction():
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    verdicts = {src1: {
        "visible_description": "a dining room",
        "alt": {"status": "CONTRADICTED", "reason": "wrong subject",
                "corrected": "Cruise ship dining room with set tables"},
        "title": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
        "caption": {"status": "PLAUSIBLE", "reason": "", "corrected": ""}}}
    orig = _mock_vision(verdicts)   # default certifier approves
    try:
        result = image_audit.audit_images(CAPTIONED, state=None, limit=0)
    finally:
        _restore_vision(orig)
    check("certifier_approve_applied",
          len(result["corrections"]) == 1
          and result["corrections"][0]["alt"].startswith("Cruise ship"), result["corrections"])
    check("certifier_approve_recorded", result["findings"][0]["certified"] is True)


def test_noop_correction_suppressed():
    """Case/punctuation-only 'corrections' are churn, never applied (0175)."""
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    rec = image_audit.collect_image_records(CAPTIONED)[0]
    verdicts = {src1: {
        "visible_description": "x",
        "alt": {"status": "CONTRADICTED", "reason": "r",
                "corrected": rec["alt"].upper() + "."},   # same text, case/punct only
        "title": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
        "caption": {"status": "PLAUSIBLE", "reason": "", "corrected": ""}}}
    orig = _mock_vision(verdicts)
    try:
        result = image_audit.audit_images(CAPTIONED, state=None, limit=0)
    finally:
        _restore_vision(orig)
    check("noop_not_applied", result["corrections"] == [], result["corrections"])


def test_caption_correction_must_retain_context():
    src1 = "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg"
    verdicts = {src1: {
        "visible_description": "city skyline",
        "alt": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
        "title": {"status": "PLAUSIBLE", "reason": "", "corrected": ""},
        # a "correction" that deletes every place word -- must be finding-only
        "caption": {"status": "CONTRADICTED", "reason": "r",
                    "corrected": "City skyline across water with a clear sky"}}}
    orig = _mock_vision(verdicts)
    try:
        result = image_audit.audit_images(CAPTIONED, state=None, limit=0)
    finally:
        _restore_vision(orig)
    check("caption_context_drop_rejected", result["corrections"] == [], result["corrections"])
    check("caption_context_drop_finding_kept",
          result["contradicted_count"] == 1 and result["findings"][0]["applied"] is False)


def test_apply_image_corrections():
    corrections = [{"src": "https://blogger.googleusercontent.com/img/x/w640-h480/p1.jpg",
                    "alt": "Cruise ship dining room",
                    "title": "Dining room, departure night",
                    "caption": "Dining room aboard the ship"}]
    out, applied = assembler.apply_image_corrections(HTML, corrections)
    check("apply_count", applied == 3, applied)
    check("apply_alt", 'alt="Cruise ship dining room"' in out)
    check("apply_title", 'title="Dining room, departure night"' in out)
    check("apply_caption", "Dining room aboard the ship" in out)
    check("apply_original_caption_gone", "Totem pole at Stanley Park, Vancouver" not in out)
    check("apply_full_link_kept", 'href="https://example.com/full.jpg"' in out)
    # a caption correction against the LINKED caption must be refused at apply time too
    out2, applied2 = assembler.apply_image_corrections(
        HTML, [{"src": "https://blogger.googleusercontent.com/img/x/s1600/p2.jpg",
                "caption": "should not land"}])
    check("apply_linked_caption_refused", "should not land" not in out2 and applied2 == 0)
    check("apply_linked_caption_href_kept", 'href="https://youtu.be/abc"' in out2)


def main():
    test_collect_records()
    test_collect_records_rejects_non_string_input()
    test_downscaled_url()
    test_fetch_rejects_unsafe_url()
    test_fetch_rejects_redirect_to_private()
    test_audit_contradicted_produces_gated_corrections()
    test_audit_rejects_rule_breaking_correction()
    test_unknown_status_degrades_to_plausible()
    test_audit_survives_per_image_exception()
    test_audit_stops_after_consecutive_failures()
    test_progress_cache_reuse_and_staleness()
    test_failure_paths_logged_to_transcript()
    test_certifier_rejection_demotes_to_finding_only()
    test_certifier_approval_allows_correction()
    test_noop_correction_suppressed()
    test_caption_correction_must_retain_context()
    test_apply_image_corrections()
    print()
    if FAILS:
        print("FAILED: " + str(FAILS))
        sys.exit(1)
    print("IMAGE-AUDIT TESTS PASSED")


if __name__ == "__main__":
    main()
