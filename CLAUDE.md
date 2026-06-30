# Project rules for Claude Code

## Commit + push policy (STRICT)

All commit+push goes through ONE command:

    python .claude/checkpoint.py --reason "<a|b|c>: <context>"

`checkpoint.py` stages everything, commits **through the hard review gate**
(`.git/hooks/pre-commit`, no `--no-verify`), and pushes. If the gate finds Critical
issues the commit is blocked and nothing is pushed.

**Commit + push at exactly these three points -- and not on every edit:**

- **(a) Before sending anything (code + docs) out for review.**
  Run a checkpoint *before* invoking any reviewer: `step7_review.py`,
  `step8_quality_gate.py`, `code_agent.py`, the `/code-review` skill, or handing work
  to a human. Reason: `before-review: <what>`.
- **(b) After completing a defect ticket.**
  Immediately after `ticket.py update TICKET-XXXX --status Closed`.
  Reason: `ticket-closed: TICKET-XXXX`.
- **(c) After implementing review comments, before sending for review again.**
  Reason: `post-review-fixes: <what>`.

### What is automated vs manual
- Hooks (`.claude/commit_push_rule.py`) auto-checkpoint for:
  - (a/c) before any review **script** runs (PreToolUse),
  - (b) after a ticket is closed via `ticket.py` (PostToolUse).
- Hooks CANNOT see the `/code-review` skill or "send to a human" -- for those,
  **run `checkpoint.py` yourself first.**
- There is NO per-edit autocommit anymore. Do not add one.

## LLM offload
All review / doc / test / codegen work runs on OpenRouter (free) with DeepSeek/NVIDIA
fallback via `.claude/or_client.py`. See `.claude/OPENROUTER_OFFLOAD.md`.
Goal: minimum Claude-Code cloud token usage.

## Coder workflow
Claude does not write app `.py` directly -- they go through `.claude/code_agent.py`
(enforced by `.claude/check_no_direct_python_write.py`). `.claude` tooling scripts are
the exception (write them via shell).
