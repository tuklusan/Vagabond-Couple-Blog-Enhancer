"""
Central configuration for the orchestrator.

Everything overridable via environment variables so the orchestrator can run
headless in CI or be re-pointed without code edits.
"""
import os
from pathlib import Path

# Repo root = parent of the orchestrator package directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = PROJECT_ROOT / "Config" / "_SECRETS"

# Per-run state lives here (gitignored: Output/ is already in .gitignore).
RUN_ROOT = Path(os.environ.get("ORCH_RUN_ROOT", str(PROJECT_ROOT / "Output" / "runs")))

# ---------------------------------------------------------------------------
# Required Project Documents (rev-18 hard stop). They live OUTSIDE this repo.
# Point ORCH_DOCS_DIR elsewhere if the canonical folder moves.
# ---------------------------------------------------------------------------
DOCS_DIR = Path(os.environ.get(
    "ORCH_DOCS_DIR",
    r"H:\My Documents\BLOG_STUFF\BLOG-FIX-OLD-BLOGS\OLD-BLOG-FIXER\REQUIRED-PROJECT-DOCUMENTS-FOR-WORKFLOW",
))

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
    """Return the Path to a required document, or None if absent."""
    pattern = REQUIRED_DOCS[logical_name]
    if "*" in pattern:
        matches = sorted(DOCS_DIR.glob(pattern))
        return matches[-1] if matches else None
    path = DOCS_DIR / pattern
    return path if path.exists() else None


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
MAX_NODE_ROUNDS = int(os.environ.get("ORCH_MAX_NODE_ROUNDS", "6"))

# If every review provider is unreachable: fail-open (allow, flag) by default so
# an outage never permanently blocks a run; set 1 to fail-closed (block).
GATE_FAIL_CLOSED = os.environ.get("ORCH_GATE_FAIL_CLOSED", "0") == "1"
