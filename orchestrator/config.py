# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Central configuration for the orchestrator.

Everything overridable via environment variables so the orchestrator can run
headless in CI or be re-pointed without code edits.
"""
import os
from pathlib import Path


def _env_int(name, default):
    """Read an int from the environment, falling back to `default` on a missing or
    non-integer value instead of crashing the import (TICKET-0006)."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        print("[config] ignoring non-integer " + name + "=" + repr(raw)
              + "; using default " + str(default))
        return default


# Repo root = parent of the orchestrator package directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = PROJECT_ROOT / "Config" / "_SECRETS"

# Per-run state lives here (gitignored: Output/ is already in .gitignore).
RUN_ROOT = Path(os.environ.get("ORCH_RUN_ROOT", str(PROJECT_ROOT / "Output" / "runs")))

# ---------------------------------------------------------------------------
# Required Project Documents (rev-18 hard stop). They are now bundled INSIDE the
# repo under Config/workflow-docs/ so the orchestrator is self-contained. Set
# ORCH_DOCS_DIR to override (e.g. to a private canonical folder); resolution then
# tries the override first and falls back to the bundled copies.
# ---------------------------------------------------------------------------
BUNDLED_DOCS_DIR = PROJECT_ROOT / "Config" / "workflow-docs"
DOCS_DIR = Path(os.environ.get("ORCH_DOCS_DIR", str(BUNDLED_DOCS_DIR)))
# Ordered search path: the configured DOCS_DIR first, then the bundled copies.
DOCS_SEARCH_DIRS = [DOCS_DIR] + ([BUNDLED_DOCS_DIR] if DOCS_DIR != BUNDLED_DOCS_DIR else [])

# Logical name -> filename (or glob for the timestamped theme XML).
REQUIRED_DOCS = {
    "theme_xml": "vg-blog-theme-live-*.xml",
    "schema_example": "TRAVELACTION-ld_json-SCHEMA-EXAMPLE.txt",
    "youtube_embed": "YOUTUBE-VIDEO-EMBED-FOR-BLOGGER.txt",
    "writing_rules": "english-writing-rules_v2.txt",
    "reference_prefold": "TVC-reference-prefold-turkmenistan-part1_1.html",
    "workflow": "TVC-google-indexing-fix-workflow-rev-18.md",
}


def resolve_doc(logical_name: str):
    """Return the Path to a required document, or None if absent.

    Searches DOCS_SEARCH_DIRS in order (configured override first, bundled copies
    second) so a partial override still falls back to the shipped defaults."""
    pattern = REQUIRED_DOCS[logical_name]
    for base in DOCS_SEARCH_DIRS:
        if "*" in pattern:
            # newest by modification time, not lexical order (TICKET-0007)
            matches = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime)
            if matches:
                return matches[-1]
        else:
            path = base / pattern
            if path.exists():
                return path
    return None


def missing_docs():
    """List logical names of any Required Project Documents not found."""
    return [name for name in REQUIRED_DOCS if resolve_doc(name) is None]


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
# Writer: cheap/free bulk generation (handled by writer_client / or_client).
WRITER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")

# Reviewer: Claude API. Default to the strongest model for fact-checking;
# set REVIEWER_MODEL=claude-sonnet-4-6 to trade quality for cost.
REVIEWER_MODEL = os.environ.get("REVIEWER_MODEL", "claude-opus-4-8")

# UNIVERSAL reviewer fallback: whenever Claude is unusable (no credit balance,
# auth failure, outage), the reviewer role falls back to DeepSeek. DeepSeek has
# no web-search server tool, so on fallback the reviewer is told not to certify
# figures it cannot verify from reliable knowledge (mark REVISE/ESCALATE).
REVIEWER_DEEPSEEK_MODEL = os.environ.get("REVIEWER_DEEPSEEK_MODEL", "deepseek-v4-pro")

# Web-search tool variant (dynamic-filtering on Opus 4.8). Falls back to the
# basic variant automatically if the SDK/model rejects the new one.
WEB_SEARCH_TOOL_TYPE = os.environ.get("WEB_SEARCH_TOOL_TYPE", "web_search_20260209")
WEB_SEARCH_TOOL_TYPE_FALLBACK = "web_search_20250305"

# ---------------------------------------------------------------------------
# Loop / gate policy
# ---------------------------------------------------------------------------
# How many writer<->reviewer rounds on a single node before escalating to the
# operator rather than looping forever ("even if it takes a long time" - but not
# infinitely on an unverifiable claim).
MAX_NODE_ROUNDS = _env_int("ORCH_MAX_NODE_ROUNDS", 6)

# If every review provider is unreachable: fail-open (allow, flag) by default so
# an outage never permanently blocks a run; set 1 to fail-closed (block).
GATE_FAIL_CLOSED = os.environ.get("ORCH_GATE_FAIL_CLOSED", "0") == "1"
