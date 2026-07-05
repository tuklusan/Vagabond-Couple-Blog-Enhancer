# TICKET-0202: [sequencer.py] Turn the 1J visual image audit OFF by default
Status: Closed
Priority: Medium
Type: Enhancement
Created: 2026-07-05
Description: User directive: the vision-based image-metadata/caption detection+correction feature (Phase 1/1J, TICKET-0167) must be OFF by default, activated only on the user's explicit instruction -- including explicit instruction in-chat when the orchestrator is run from a chat session. Previously `ORCH_IMAGE_AUDIT` defaulted to "1" (on): every `--full` run silently made a metered NIM vision-model call per image (hundreds on a large post) unless the operator remembered to set `ORCH_IMAGE_AUDIT=0`.
Steps to Reproduce: N/A -- direct user instruction, not a discovered defect.
Notes: Flipped the default: `image_audit_node()`'s handler now short-circuits to `status: "disabled"` unless `ORCH_IMAGE_AUDIT=1` is explicitly set (previously it ran unless `ORCH_IMAGE_AUDIT=0`). Docstring and README's config-reference row updated to describe it as opt-in. New test: test_image_audit_disabled_by_default (verifies both directions -- default-off short-circuits before any audit call, and explicit ORCH_IMAGE_AUDIT=1 actually reaches audit_images). Behavioral note (not code, but binding on this project going forward): when running the orchestrator from within a chat session, the vision audit must only be enabled when the user explicitly asks for it in that conversation -- setting ORCH_IMAGE_AUDIT=1 "by default" or "because it seems useful" is exactly the behavior this ticket exists to prevent.
