# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
TVC Blog-Fix Orchestrator.

Drives the rev-18 "Crawled But Not Indexed" fix workflow as a gated state machine:
a cheap/free WRITER model (OpenRouter + NVIDIA/DeepSeek fallback) generates content,
and a web-grounded REVIEWER model (Claude API) fact-checks and certifies every claim
in an iterative handshake until criteria (a)-(e) all pass. See plan + workflow doc.
"""

__version__ = "0.1.0"
