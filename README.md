<!--
Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
Limited Source-Code Viewing License -- view-only. No execution, modification,
redistribution, production use, or AI/ML training. Full terms: see LICENSE
(repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
-->

# Vagabond Couple — Blog Enhancer Orchestrator

A Python orchestrator that drives **The Vagabond Couple "Crawled — Currently Not
Indexed" Fix Workflow (rev-18)**: it takes a raw Blogger post's HTML and produces
an SEO-remediated post — an enhanced HTML body plus a new SEO title and a new
≤150-character search description — under tight, verifiable quality control.

> **License:** proprietary, **view-only**. See [`LICENSE`](LICENSE). You may read
> and evaluate the source; you may **not** execute, modify, redistribute, use it
> in production, or use it to train/fine-tune/validate any AI model.
>
> **Note on the sections below.** The Install, Usage, and related instructions in
> this README are provided **for reference — to explain how the software is
> structured and how it operates**. They are **not** a grant of permission to
> execute, build, deploy, or otherwise use the software. Any actual use is
> governed solely by the [`LICENSE`](LICENSE), which is view-only.

---

## Architecture at a glance

```
        ┌──────────────────────────────────────────────────────────────────────┐
        │  INPUT:  raw Blogger post HTML                                         │
        └──────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
   ┌────────────────────────────────────────────────────────────────────────────────┐
   │  ORCHESTRATOR  —  G4 state machine (durable · resumable · step-entry gate)        │
   │                                                                                  │
   │  Pre-check ─▶ Context extraction ─▶ Phase 1 (scan) ─▶ Phase 2 (URL lock)          │
   │      ─▶ Phase 3: Steps 1..13 ─▶ Phase 4 ─▶ Phase 5 ─▶ Phase 6                      │
   │             (generative nodes)   APPROVAL   GEN+CERT   deliver                     │
   └────────────────────────────────────────────────────────────────────────────────┘
        │                          │                              │
        ▼                          ▼                              ▼
  DETERMINISTIC             WRITER ⇄ REVIEWER                OPERATOR GATES
  VALIDATORS (code)         (per generative node)            (human-in-the-loop)
  · href byte-diff          1. writer drafts ───────────┐    · pre-check
  · ?/U+FFFD scan              (OpenRouter→DeepSeek       │    · escalations (⚠ / ❌ / 🟠)
  · ld+json validity           →NVIDIA)                   │    · Phase 4 approval
  · ETR · ≤150 chars         2. deterministic pre-screen  │      (blocks HTML gen)
  · forbidden terms          3. reviewer certifies ◀──────┘    · Phase 6 deliverables
  · <!--more--> · images        (Claude web-grounded
  · RaaG ↔ H2                    →DeepSeek fallback)
                              facts · rules · repetition
                              loop ⟳ until CERTIFIED
                                          │
                                          ▼
        ┌──────────────────────────────────────────────────────────────────────┐
        │  OUTPUT:  enhanced post body HTML  +  SEO title  +  ≤150-char description │
        └──────────────────────────────────────────────────────────────────────┘
```

Key idea: the **writer never finalizes a claim** — the **reviewer must certify it
(with source URLs)** before it persists. Deterministic checks own the mechanical
rules; the reviewer spends its tokens only on facts and the holistic read.

---

## Table of contents

1. [What it does](#what-it-does)
2. [How it works (architecture)](#how-it-works-architecture)
3. [Requirements](#requirements)
4. [API keys — where to get them and how to provide them](#api-keys)
5. [Required Project Documents](#required-project-documents)
6. [Install](#install)
7. [Usage](#usage)
8. [Output layout](#output-layout)
9. [Configuration reference](#configuration-reference)
10. [Tests](#tests)
11. [Issue tracking](#issue-tracking)
12. [Troubleshooting](#troubleshooting)
13. [Project status](#project-status)

---

## What it does

Google often crawls a travel-blog post but declines to index it ("Crawled —
currently not indexed"), usually because of focus dilution, a weak first screen,
duplicate `?m=1` URL signals, missing structured route data, and a missing author
entity signal. The rev-18 workflow fixes all of that deterministically and with
fact-checked rewrites. This orchestrator runs that workflow as a gated state
machine so the result is consistent and trustworthy.

It will, for a given post:

- Audit media/links, character encoding, the summary block, schema, and
  `<!--more-->` placement.
- **Visually audit every photograph** (Phase 1/1J, TICKET-0167): an NVIDIA NIM
  vision model looks at each image and flags alt/title/caption text the visible
  content contradicts (wrong primary subject only — proper nouns, vantage
  points, and details beyond the frame are unverifiable from pixels and never
  flagged). Gated corrections are applied at Phase 5 assembly; risky ones
  (linked captions, place-name-dropping caption rewrites) are recorded as
  operator findings instead of auto-applied.
- Generate (and **fact-check, with temporal validity**: every inserted fact must
  have been true as of the trip's own dates, derived from the post — a
  currently-true fact that postdates the trip is rejected as an anachronism)
  a route-first first paragraph, a route summary
  box, a "Route at a Glance" list, section-closing factoids, a journey-
  significance paragraph, image separators, an SEO title, and a search
  description.
- Reapply the canonical summary-block CSS, strip noisy inline styles, re-emit
  YouTube embeds to the project template, and remove `?m=1` from internal links —
  while preserving all **other** original `href`s byte-for-byte (the `?m=1`
  stripping is the one intentional, audited href change).
- Stop for **operator approval** before generating final HTML, then certify the
  assembled output with a two-pass check before delivery.

---

## How it works (architecture)

Two cooperating models plus a deterministic core:

- **Writer (cheap / free)** — drafts content. Provider chain:
  **OpenRouter (free) → DeepSeek → NVIDIA**.
- **Reviewer (judgment)** — fact-checks and certifies. Provider chain:
  **Claude API (web-grounded) → DeepSeek (universal fallback)**. The writer never
  finalizes a factual claim; the reviewer must certify it (with source URLs)
  before it persists. Unverifiable claims are revised or escalated — **never
  silently kept**.
- **Deterministic validators (code, not LLM)** — own every mechanical rule
  (href byte-diff, `?`/U+FFFD scan, ld+json validity, ETR word count, ≤150-char,
  consecutive-image detection, forbidden-term scan loaded from the rules file,
  `<!--more-->` placement, image↔table counts, Route-at-a-Glance ↔ H2). This is
  what lets the reviewer spend its tokens only on facts and holistic reading, and
  it powers the second verification pass.

Control:

- **G4 state machine** — canonical-order dispatch with a step-entry gate (no step
  starts until the prior one is confirmed complete in durable, resumable state).
- **Phase 4 approval gate** — blocks HTML generation until the operator approves.
- **G2 two-pass certification** — Pass 1 (reviewer reads the whole post for HTML
  sanity, repetition, and a smooth chronological/geographical read); Pass 2
  (deterministic re-derivation of every mechanical fact). Both must pass.
- **Graceful degradation** — any provider outage **escalates to the operator**;
  nothing crashes and nothing auto-certifies.

---

## Requirements

- **Python 3.10+**
- Python packages (see [`requirements.txt`](requirements.txt)):
  `anthropic`, `requests`, `beautifulsoup4`
- At least **one writer provider** and **one reviewer provider** key (see below).
  The cheapest working setup is **OpenRouter (free) + DeepSeek**.
- The six [Required Project Documents](#required-project-documents).

---

## API keys

You need keys for the providers you intend to use. You can supply **any subset** —
the orchestrator falls back across providers automatically — but you need at least
one writer and one reviewer.

| Provider | Role | Get a key at | Notes |
|---|---|---|---|
| **OpenRouter** | Writer (primary) | <https://openrouter.ai/keys> | Free models available (`openrouter/free`). Key looks like `sk-or-v1-…`. |
| **DeepSeek** | Writer fallback **+ Reviewer fallback** | <https://platform.deepseek.com/api_keys> | Paid but inexpensive. Used as the **universal reviewer fallback** when Claude is unusable. |
| **Anthropic (Claude)** | Reviewer (primary, **web-grounded**) | <https://console.anthropic.com/settings/keys> | Key looks like `sk-ant-…`. **Requires a positive credit balance** (Plans & Billing) or every call returns `400: credit balance too low`. Web-grounded fact-checking only works here. |
| **NVIDIA NIM** | Writer fallback + reviewer fallback + vision | <https://build.nvidia.com/> | Optional for writing (writer fallback chain); **hosts the same `deepseek-v4-pro` as a reviewer/writer fallback pool** (TICKET-0214) so a DeepSeek-account outage doesn't silence the pipeline's only reviewer; **required for all vision features** (1J image audit, Step-13 vision nudge — without this key they record `unavailable`/skip and the run continues). |

> **Minimum viable setup:** OpenRouter (free) for the writer + DeepSeek for the
> reviewer. Fact-checking then runs on DeepSeek's own knowledge (no live web). Add
> **Anthropic credits** to enable web-grounded fact verification — that is the
> strongest anti-hallucination guarantee.

### How to provide the keys

Two mechanisms; **environment variables take priority over files**.

**Option A — Environment variables**

| Variable | Provider |
|---|---|
| `OPENROUTER_AI_API_KEY` | OpenRouter |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `ANTHROPIC_API_KEY` | Anthropic |
| `NVIDIA_API_KEY_CODING` | NVIDIA NIM |

PowerShell (current session):
```powershell
$env:OPENROUTER_AI_API_KEY = "sk-or-v1-..."
$env:DEEPSEEK_API_KEY      = "sk-..."
$env:ANTHROPIC_API_KEY     = "sk-ant-..."
```
Persist for your user (new shells):
```powershell
setx OPENROUTER_AI_API_KEY "sk-or-v1-..."
```
bash:
```bash
export OPENROUTER_AI_API_KEY="sk-or-v1-..."
export DEEPSEEK_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Option B — Secret files in `Config/_SECRETS/`** (this folder is git-ignored and
never committed)

| File | Provider |
|---|---|
| `Config/_SECRETS/openrouter-api-key.txt` | OpenRouter |
| `Config/_SECRETS/deepseek-api-key.txt` | DeepSeek |
| `Config/_SECRETS/anthropic-api-key.txt` | Anthropic |
| `Config/_SECRETS/nvidia-api-key.txt` (or legacy `-keys.txt`) | NVIDIA NIM |

Each file may be either a **bare key**:
```
sk-or-v1-................................................
```
or a **`NAME=value`** line (the variable name from the table above):
```
OPENROUTER_AI_API_KEY=sk-or-v1-................................................
```

> **Never commit keys.** `Config/_SECRETS/` is already in `.gitignore`. Keep it
> that way.

---

## Required Project Documents

These six ship **bundled inside the repo** at `Config/workflow-docs/`, so the
orchestrator is self-contained and runs out of the box. Set `ORCH_DOCS_DIR` to
override with your own canonical copies; resolution tries that folder first and
falls back to the bundled copies. The run **hard-stops at startup** if any are
missing (only possible if you removed them or pointed `ORCH_DOCS_DIR` at an
incomplete folder), printing each missing logical name, its expected filename,
and the exact folder to drop it into.

| Logical name | Filename (pattern) |
|---|---|
| Blogger theme XML | `vg-blog-theme-live-*.xml` |
| Schema example | `TRAVELACTION-ld_json-SCHEMA-EXAMPLE.txt` |
| YouTube embed template | `YOUTUBE-VIDEO-EMBED-FOR-BLOGGER.txt` |
| Writing rules | `english-writing-rules_v2.txt` |
| Canonical pre-fold reference | `TVC-reference-prefold-turkmenistan-part1_1.html` |
| Workflow spec | `TVC-google-indexing-fix-workflow-rev-18.md` |

The pre-check halts with the exact missing filenames if any are absent.

---

## Install

```bash
git clone https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer.git
cd Vagabond-Couple-Blog-Enhancer
pip install -r requirements.txt
```

Verify the providers and documents are wired up:

```bash
# writer smoke test (OpenRouter -> fallback)
python -m orchestrator.writer_client          # prints: [openrouter:openrouter/free] PIPELINE OK

# reviewer smoke test (Claude -> DeepSeek fallback)
python -c "from orchestrator import reviewer_client as r; print(r.ping())"

# confirm the six required documents resolve
python -c "from orchestrator import config; print('missing:', config.missing_docs())"
```

---

## Usage

> **Descriptive only.** The commands below document how the software operates.
> Running it is governed by the view-only [`LICENSE`](LICENSE) — this is not a
> grant to execute or deploy.

```bash
python -m orchestrator --input PATH_TO_POST.html [--full] [--dry] [--auto] [--approve-phase4] [--run-id NAME] \
    [--current-url URL] [--prior-url URL] [--next-url URL]
```

| Flag | Meaning |
|---|---|
| `--input` | **(required)** path to the source post HTML (post body, not a full page). |
| `--full` | Run the **entire** canonical pipeline (context extraction → Phase 1 → Phase 2 → Steps 1–13 → Phase 4 approval → Phase 5 generate + certify → Phase 6 deliverables). Without it, runs only the pre-check + deterministic Phase-1 analysis + the Phase 4 gate. |
| `--dry` | Stub the generative/analysis (LLM) nodes — walk the whole machine **without any model calls**. Great for verifying setup and the document/structure checks. |
| `--auto` | Headless operator: gates use safe defaults. **The Phase 4 gate withholds approval by default**, so an `--auto` run halts at Phase 4 (by design). Omit `--auto` to approve interactively. |
| `--approve-phase4` | Test/CI opt-in: auto-grants the Phase 4 approval gate under `--auto` so a headless run can reach `DONE` without an interactive `y`. Real runs should approve interactively (omit both `--auto` and this flag) rather than rely on it. |
| `--run-id` | Name/reuse a run directory under `Output/runs/`. |
| `--current-url` | This post's own live URL, if already published. Optional; used only as a fallback subject when the source has no schema/title and route extraction finds nothing. |
| `--prior-url` | The series' prior post's live URL. If given, the orchestrator fetches it (best-effort; a network failure or 404 just means no lead-in is attempted) and writes a genuine lead-in referencing and linking it in the first body paragraph. |
| `--next-url` | The series' next post's live URL. Same mechanism as `--prior-url`, but for a lead-out in the closing paragraph. |

### Common invocations

Walk the full machine with no LLM cost (sanity-check your setup on any post):
```bash
python -m orchestrator --input mypost.html --full --dry --auto
```

Deterministic analysis + Phase-4 summary, interactive approval:
```bash
python -m orchestrator --input mypost.html
```

Real run (needs working writer + reviewer keys), approving interactively:
```bash
python -m orchestrator --input mypost.html --full
# ... review the Phase 4 summary, type 'y' to approve HTML generation ...
```

Real run that's part of a series, with a genuine lead-in/lead-out to the prior/next posts:
```bash
python -m orchestrator --input mypost.html --full --auto --approve-phase4 \
    --current-url https://example.blogspot.com/2021/07/this-post.html \
    --prior-url https://example.blogspot.com/2021/07/prior-post.html \
    --next-url https://example.blogspot.com/2021/07/next-post.html
```

When a run reaches `DONE`, the enhanced HTML is the `working.html` in the run
directory (printed as `enhanced HTML: ...`).

### Operator gates

During a non-`--auto` run you will be prompted at:
- **Pre-check** — halts if any required document is missing.
- **Per-node escalations** — if the reviewer cannot certify a node, you choose to
  accept the output or abort.
- **Phase 4 approval** — a full modification summary is shown; you must type `y`
  to unlock HTML generation. Nothing is generated before this.
- **Phase 6** — the three deliverables are presented.

---

## Output layout

Each run writes to `Output/runs/<run_id>/` (git-ignored):

```
Output/runs/20260630T162908/
├── working.html        # the post HTML, mutated step-by-step (the deliverable when DONE)
├── status.json         # current node + per-node completion / gate state (G4)
├── log.jsonl           # append-only event log
├── ai_transcript.txt   # every writer/reviewer prompt + response, in order, labeled
│                       # ">>> SOURCE -> TARGET [node_id] (provider) timestamp" -- a
│                       # full audit trail of every AI communication in the run
└── artifacts/          # structured outputs
    ├── context.json                # extracted route/sections/stops
    ├── 1C_media_inventory.json
    ├── 1G_encoding.json
    ├── schema_check.json
    ├── gen_step6_first_body_paragraph.json   # certified fragment + verdict + source URLs
    ├── ...
    └── phase5_certification.json   # G2 two-pass result
```

Generative artifacts include the reviewer's verdict **and the source URLs it
consulted** — your anti-hallucination audit trail.

---

## Configuration reference

All optional; sensible defaults shown.

| Env var | Default | Purpose |
|---|---|---|
| `ORCH_DOCS_DIR` | `Config/workflow-docs/` (bundled) | Override folder for the six required documents; falls back to the bundled copies. |
| `ORCH_RUN_ROOT` | `Output/runs` | Where run state is written. |
| `ORCH_MAX_NODE_ROUNDS` | `6` | Writer↔reviewer rounds per node before escalating to the operator. |
| `ORCH_GATE_FAIL_CLOSED` | `0` | `1` = block on a total review outage instead of failing open. |
| `ORCH_IMAGE_AUDIT` | `0` (off) | `1` enables the Phase 1/1J visual image audit. **Off by default** (TICKET-0202) -- it makes a metered NIM vision-model call per image (hundreds on a large post), so it is opt-in per run rather than something every run silently pays for. |
| `ORCH_IMAGE_AUDIT_LIMIT` | `0` (all images) | Cap the number of images audited per run (smoke tests / metered runs). |
| `ORCH_IMAGE_AUDIT_APPLY` | `0` (findings-only) | `1` = apply 1J corrections at Phase 5. Every applied correction must now also pass **second-VLM visual certification** (TICKET-0175: accuracy, natural prose, no unjustified proper-noun/vantage deletion; fails closed). Default stays off pending one supervised validation run with certification active. |
| `ORCH_VLM_MODEL` | `meta/llama-3.2-90b-vision-instruct` | Primary NIM vision model for 1J; fixed fallbacks `nvidia/nemotron-nano-12b-v2-vl` then `microsoft/phi-4-multimodal-instruct`. |
| `ORCH_STEP13_VISION` | `0` (off) | `1` = vision-nudged separator research (TICKET-0208): a VLM identifies what each adjacent photo pair shows before the library/academic retrieval. Opt-in per run, same explicit-instruction rule as the 1J audit. The retrieval itself (Wikipedia + OpenAlex, keyless) is always on for Step 13; the writer is confined to retrieved snippets and the reviewer checks evidence entailment. |
| `ORCH_MAX_PASS1_BOUNCES` | `3` | Phase 5 Pass-1 REVISE bounces (factoid drop / passage rewrite) before halting for the operator. |
| `OPENROUTER_MODEL` | `openrouter/free` | Writer model. `openrouter/free` is a non-deterministic router (a different model per call). Set to **`auto`** to have the code query OpenRouter's `/models` and pick the best available **free instruct** model (stable + clean content), or pin a specific `…:free` id yourself. |
| `OPENROUTER_REASONING_EFFORT` | `` (off; `none` auto-applied on a pinned/`auto` instruct model) | OpenRouter reasoning effort. `none` returns the answer directly (no chain-of-thought) — valid only on a specific instruct model, **not** the `openrouter/free` router (which rejects it with 400). |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint. |
| `REVIEWER_MODEL` | `claude-opus-4-8` | Claude reviewer model (`claude-sonnet-4-6` to trade quality for cost). |
| `REVIEWER_DEEPSEEK_MODEL` | `deepseek-v4-pro` | DeepSeek reviewer-fallback model. |
| `WEB_SEARCH_TOOL_TYPE` | `web_search_20260209` | Claude web-search tool variant; auto-falls back to `web_search_20250305`. |

---

## Tests

The deterministic suite needs **no API keys** (only the required documents):

```bash
python tests/test_validators.py        # deterministic validators vs the reference HTML
python tests/test_context.py           # source-context extraction
python tests/test_assembler.py         # HTML transforms + fragment splicing
python tests/test_sequencer.py         # G4 gate, Phase 4 block/pass
python tests/test_document_cert.py     # G2 Pass 2 (deterministic re-derivation)
python tests/test_full_sequence.py     # full 29-node canonical dry walk
python tests/test_image_audit.py       # 1J visual image audit (VLM mocked)
```

Live tests (consume tokens; need writer + reviewer keys):

```bash
python tests/test_node_loop.py         # one writer<->reviewer node loop
python tests/test_more_nodes.py        # title + description nodes
```

---

## Issue tracking

The repo ships a small offline issue tracker, `ticket.py`. Each ticket is a plain
markdown file under `Tickets/` (`TICKET-NNNN.md`), so tickets live with the code
and need no external service.

```bash
python ticket.py new --title "Short title" [--type Bug|Task|Enhancement] \
                     [--priority High|Medium|Low] [--desc "Details"]
python ticket.py list [--status Open|Closed]
python ticket.py show 0001
python ticket.py update 0001 --status Closed [--notes "What was done"]
```

Closing a ticket (`update … --status Closed`) is one of the project's three
commit+push points (before review · after a defect ticket · after applying review
fixes).

### DeepSeek dev-review push gate

A second-opinion reviewer (DeepSeek, via `.claude/dev_review.py`) is enforced at
**push time** by a tracked git hook, so code/doc/test changes can't reach the
remote without review. Enable it once per clone:

```bash
git config core.hooksPath .githooks   # or: sh .githooks/install
```

On `git push`, `.githooks/pre-push` reviews the changed `.py`/`.md` files (excluding
`Tickets/` and the bundled `Config/workflow-docs/`). Policy:

- **Blocks** the push on any unaddressed **Critical** finding — and files a ticket
  for each so it's actionable.
- **Remembers triaged false positives** (TICKET-0183): a Critical finding matching
  a `Tickets/` ticket already closed as *FALSE POSITIVE / DUPLICATE / NO ACTION*
  (same file, strongly overlapping title) is reported as suppressed instead of
  re-blocking every subsequent push. Genuinely-fixed findings are *not*
  suppressed — a regression of fixed code still blocks.
- **Fails open** (allows, with a warning) if DeepSeek is unreachable for every file,
  so an API outage or missing key never permanently blocks pushes.
- Warning/Info findings are advisory (don't block).

Needs `DEEPSEEK_API_KEY` in the environment. Bypass for an emergency push with
`git push --no-verify` or `SKIP_DEEPSEEK_REVIEW=1 git push`.

> A GitHub Issues tracker is also available on the origin remote if you prefer a
> hosted option.

---

## Troubleshooting

| Symptom | Cause & fix |
|---|---|
| `400 … Your credit balance is too low` (Anthropic) | The Anthropic account is unfunded. Reviews automatically fall back to DeepSeek. To enable **web-grounded** review, add credits at console.anthropic.com → Plans & Billing. |
| `[reviewer] Claude unusable … falling back to DeepSeek` | Informational — the universal fallback is working. Review proceeds on DeepSeek (no live web search). |
| `429 Too Many Requests` (OpenRouter) | Free-tier rate limit. The writer falls back to DeepSeek/NVIDIA. Wait a few minutes, or pin a specific `:free` model / add OpenRouter credit for higher limits. |
| `empty content from deepseek-…` | Transient DeepSeek hiccup; it is retried, then the provider chain continues. Re-run if it persists. |
| `All writer providers failed` / a node returns `ESCALATE: writer_unavailable` | No writer provider is reachable. Check that at least one of `OPENROUTER_AI_API_KEY` / `DEEPSEEK_API_KEY` / `NVIDIA_API_KEY_CODING` is set, and check connectivity. |
| `HALT — Required project document(s) missing` | One of the six docs isn't found. Set `ORCH_DOCS_DIR`, or place the missing files there. The halt names them exactly. |
| `--auto` run halts at `Phase 4 approval withheld` | **Expected.** `--auto` withholds approval as a safe default. Run without `--auto` and type `y` to approve. |
| A node `ESCALATE`s repeatedly | The reviewer couldn't certify within `ORCH_MAX_NODE_ROUNDS`, or both reviewer providers were down. Decide at the operator prompt (accept / abort), raise `ORCH_MAX_NODE_ROUNDS`, or fix the underlying claim/provider. |
| `1G encoding: suspect=True` on a clean post | Not an error. The `?`-scanner flags any `?` glued to a word or inside a URL query (e.g. `?usp=sharing`) **for classification** — review and confirm it's legitimate. |
| `BadRequestError … web_search` (Anthropic) | The web-search tool variant isn't available for that model/account. The client auto-retries with the basic variant; if needed set `WEB_SEARCH_TOOL_TYPE=web_search_20250305`. |
| `404 … model` | An invalid model id. Set `REVIEWER_MODEL`, `OPENROUTER_MODEL`, or `REVIEWER_DEEPSEEK_MODEL` to a model your account can access. |
| Garbled non-ASCII in the console | The CLI prints ASCII-safe; the run artifacts (`working.html`, JSON) keep full UTF-8. Inspect the files for exact characters. |
| Resuming after a stop | State is durable in `Output/runs/<run_id>/`. The G4 gate re-confirms the last completed step before continuing. |

---

## Project status

The control plane and all deterministic machinery are complete and tested:
context extraction, validators, the writer↔reviewer loop, the G4 sequencer,
operator gates, the G2 two-pass certification, and the HTML assembler all run and
pass without any LLM.

The live, fully-generative end-to-end run is gated only on operational items: a
funded Anthropic account (for web-grounded review) and recovered free-tier
provider quota. The `1A/1B/1H/1I` source-prose analysis passes are currently
stubbed (the per-node loops and the Phase 5 pass already enforce facts, rules,
and repetition on produced text).
