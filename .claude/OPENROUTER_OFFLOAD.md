# OpenRouter Offload Pipeline

All heavy LLM work (code review, doc review, test generation, test-result analysis,
and the hard review gate) runs on **OpenRouter** so Claude-Code cloud token usage stays
minimal. Claude only orchestrates; the reasoning happens on the free model.

## Config
- Key: env `OPENROUTER_AI_API_KEY` (User scope) **and** `Config/_SECRETS/openrouter-api-key.txt`
  (gitignored; the file is what subprocess hooks read, since they don't inherit the User env var).
- Base URL: `https://openrouter.ai/api/v1`
- Default model: `openrouter/free` (a router that auto-picks a free model).
- Gate model (pinned, more stable): `qwen/qwen3-coder:free` via `OPENROUTER_GATE_MODEL`.
- Fallback chain on any failure/rate-limit: OpenRouter -> DeepSeek -> NVIDIA NIM.

Override any of these with env vars: `OPENROUTER_MODEL`, `OPENROUTER_GATE_MODEL`,
`OPENROUTER_BASE_URL`.

## Components
| File | Role | Triggers |
|------|------|----------|
| `or_client.py` | Single shared client + provider fallback | imported by all below |
| `or_review_gate.py --staged` | **HARD gate**: reviews staged code+doc diff; Critical -> blocks commit | `.git/hooks/pre-commit` |
| `deepseek_review_hook.py` | RETIRED (unwired). Per-edit review removed; review now happens only at the commit gate | manual only |
| `check_and_update_docs.py` | Auto-updates `Doc/DESIGN.txt` / `Doc/WORKFLOW.md` | PostToolUse (Write/Edit) |
| `code_agent.py` | Generates + reviews Python (3-round loop) | invoked for all `.py` authoring |
| `or_testgen.py --target X` | Generates pytest tests -> `Output/tests/` | manual |
| `or_test_analyze.py [--input F]` | Triages test output -> `Output/test-analysis/` | manual / pipe |

## The hard gate
- Runs as `.git/hooks/pre-commit` on every **real** `git commit`.
- One OpenRouter call over the whole staged diff (`.py/.md/.txt/.rst`).
- Critical findings -> exit 1 -> commit blocked. Full review saved to `Output/reviews/`.
- Autocommit snapshots use `git commit --no-verify`, so safety snapshots are never blocked.
- **Fail-open** by default if every provider is down (so an outage can't trap you).
  Set `GATE_FAIL_CLOSED=1` to block commits when review is unavailable.

### Toggles
- Make autocommit snapshots ALSO gated: remove `--no-verify` in `autocommit_and_push.py`.
- Strict mode: `setx GATE_FAIL_CLOSED 1`.
- Manual gate run: `python .claude/or_review_gate.py --staged`

## Examples
```
python .claude/or_client.py                         # smoke test
python .claude/or_testgen.py --target Scripts/foo.py
pytest -q 2>&1 | python .claude/or_test_analyze.py
```
