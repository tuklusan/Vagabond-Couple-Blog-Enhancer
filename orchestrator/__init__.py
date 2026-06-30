"""
TVC Blog-Fix Orchestrator.

Drives the rev-18 "Crawled But Not Indexed" fix workflow as a gated state machine:
a cheap/free WRITER model (OpenRouter + NVIDIA/DeepSeek fallback) generates content,
and a web-grounded REVIEWER model (Claude API) fact-checks and certifies every claim
in an iterative handshake until criteria (a)-(e) all pass. See plan + workflow doc.
"""

__version__ = "0.1.0"
