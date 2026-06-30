#!/usr/bin/env python3
"""
Operator interaction (the human-in-the-loop gates).

The rev-18 workflow pauses for the operator at: the pre-check, every unverifiable
fact / voice-exception decision, the Phase 4 approval gate (no HTML generated
before approval), the 9-F opener-style choice, and the Phase 6/7 hand-off.

Operator(auto=True) auto-answers with the safe default so the pipeline can run
headless in tests/CI; interactive mode prompts on the CLI.
"""


def _ascii(x):
    return str(x).encode("ascii", "replace").decode("ascii")


class Operator:
    def __init__(self, auto=False, input_fn=input):
        self.auto = auto
        self._input = input_fn

    def info(self, msg):
        print(_ascii(msg))

    def confirm(self, message, default=True):
        if self.auto:
            print(_ascii("[operator:auto] " + message + " -> " + ("yes" if default else "no")))
            return default
        ans = self._input(_ascii(message) + (" [Y/n]: " if default else " [y/N]: ")).strip().lower()
        if not ans:
            return default
        return ans in ("y", "yes")

    def choose(self, message, options, default_index=0):
        if self.auto:
            print(_ascii("[operator:auto] " + message + " -> " + str(options[default_index])))
            return options[default_index]
        print(_ascii(message))
        for i, o in enumerate(options):
            print(_ascii("  " + str(i + 1) + ". " + str(o)))
        ans = self._input("choose [" + str(default_index + 1) + "]: ").strip()
        try:
            return options[int(ans) - 1]
        except Exception:
            return options[default_index]

    def decide(self, item_desc, options=("fix", "keep")):
        """A flagged item needing an operator call (e.g. a voice-exception)."""
        return self.choose("Decision needed: " + item_desc, list(options), default_index=0)

    def approve(self, title, summary_text, default=False):
        """The Phase 4 approval gate. Returns True only on explicit approval."""
        print(_ascii("=" * 70))
        print(_ascii(title))
        print(_ascii("=" * 70))
        print(_ascii(summary_text))
        print(_ascii("=" * 70))
        if self.auto:
            print(_ascii("[operator:auto] approval -> " + ("APPROVED" if default else "WITHHELD")))
            return default
        return self.confirm("Approve and proceed to HTML generation?", default=False)
