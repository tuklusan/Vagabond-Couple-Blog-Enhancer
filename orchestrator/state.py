#!/usr/bin/env python3
# Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
# Limited Source-Code Viewing License -- view-only. No execution, modification,
# redistribution, production use, or AI/ML training. Full terms: see LICENSE
# (repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
"""
Durable per-run state.

Implements the G4 requirement that progress survives a session break: every
node's completion, its Output artifact, the mutating working HTML, and a
structured event log all live on disk so a run can be resumed and the
step-entry gate can verify what actually happened.

Layout (under Output/runs/<run_id>/):
    working.html          # the post HTML, mutated step-by-step
    status.json           # current node + per-node completion/gate state
    log.jsonl             # append-only event log
    artifacts/<name>.json # structured outputs (inventories, audits, verdicts)
"""
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

from . import config

_SAFE_RUN_ID = re.compile(r"[A-Za-z0-9_\-]+")


def _sanitize_run_id(run_id: str) -> str:
    """Reject run ids that could escape the run root (TICKET-0018). Only
    alphanumerics, underscore, and hyphen are allowed."""
    if not run_id or not _SAFE_RUN_ID.fullmatch(run_id):
        raise ValueError("invalid run_id " + repr(run_id)
                         + " -- allowed characters: letters, digits, '_' and '-'")
    return run_id


def _atomic_write_text(path: Path, text: str):
    """Write via a temp file + atomic replace so a crash mid-write never leaves a
    truncated/partial file for a concurrent reader (TICKET-0019/0020)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


class RunState:
    def __init__(self, run_id: str):
        self.run_id = _sanitize_run_id(run_id)
        self.dir = config.RUN_ROOT / self.run_id
        self.artifacts_dir = self.dir / "artifacts"
        self.working_html_path = self.dir / "working.html"
        self.status_path = self.dir / "status.json"
        self.log_path = self.dir / "log.jsonl"

    # ---- lifecycle -------------------------------------------------------
    @classmethod
    def create(cls, source_html: str, run_id: str = None):
        run_id = run_id or datetime.now().strftime("%Y%m%dT%H%M%S")
        self = cls(run_id)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.working_html_path.write_text(source_html, encoding="utf-8")
        self._write_status({"run_id": run_id, "current_node": None, "nodes": {}})
        self.log("run_created", {"source_chars": len(source_html)})
        return self

    @classmethod
    def load(cls, run_id: str):
        self = cls(run_id)
        if not self.status_path.exists():
            raise FileNotFoundError("no run state at " + str(self.dir))
        return self

    # ---- working HTML ----------------------------------------------------
    def get_working_html(self) -> str:
        return self.working_html_path.read_text(encoding="utf-8")

    def set_working_html(self, html: str):
        _atomic_write_text(self.working_html_path, html)

    # ---- artifacts -------------------------------------------------------
    def save_artifact(self, name: str, obj) -> str:
        path = self.artifacts_dir / (name + ".json")
        _atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))
        return str(path)

    def read_artifact(self, name: str):
        path = self.artifacts_dir / (name + ".json")
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            # A truncated/corrupt artifact is treated as absent rather than crashing
            # the run (TICKET-0021); the node that needs it will regenerate/re-check.
            return None

    def has_artifact(self, name: str) -> bool:
        return (self.artifacts_dir / (name + ".json")).exists()

    # ---- status / G4 gate ------------------------------------------------
    def _read_status(self):
        try:
            return json.loads(self.status_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            # Corrupt/missing status -> start from an empty skeleton (TICKET-0021)
            # rather than crashing; callers re-populate via mark_node/set_current_node.
            return {"run_id": self.run_id, "current_node": None, "nodes": {}}

    def _write_status(self, status):
        _atomic_write_text(self.status_path,
                           json.dumps(status, ensure_ascii=False, indent=2))

    def set_current_node(self, node_id: str):
        st = self._read_status()
        st["current_node"] = node_id
        self._write_status(st)

    def mark_node(self, node_id: str, *, complete: bool, output_ref=None, gates_ok=True, note=""):
        st = self._read_status()
        st.setdefault("nodes", {})[node_id] = {
            "complete": complete,
            "output_ref": output_ref,
            "gates_ok": gates_ok,
            "note": note,
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
        self._write_status(st)

    def node_complete(self, node_id: str) -> bool:
        st = self._read_status()
        rec = st.get("nodes", {}).get(node_id)
        return bool(rec and rec.get("complete") and rec.get("gates_ok", True))

    # ---- log -------------------------------------------------------------
    def log(self, event: str, data=None):
        rec = {"ts": time.time(), "iso": datetime.now().isoformat(timespec="seconds"),
               "event": event, "data": data or {}}
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
