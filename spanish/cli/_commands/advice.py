"""``spanish advice`` — deterministic study advice from stored state.

Read-only. Emits the contract ``advice`` payload: what to shore up and why, each
entry with a runnable command. A pure function of the learner's mastery/history
(the "tutor's opinion" a driver can relay verbatim); may be empty for a
brand-new learner — here we seed a single "start here" entry instead.
"""

from __future__ import annotations

import argparse

from spanish.cli._commands import _tutor
from spanish.tutor import engine


def cmd_advice(args: argparse.Namespace) -> int:
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    payload = engine.advice_payload(st, learner)
    return _tutor.emit(payload, args, text=_render(payload))


def _render(payload: dict) -> str:
    lines = [f"# Advice — {payload['learner']} ({payload['subject']})", ""]
    if not payload["advice"]:
        lines.append("(no advice yet — start a lesson)")
        return "\n".join(lines)
    for entry in payload["advice"]:
        focus = entry.get("focus") or "general"
        lines.append(f"- [{focus}] {entry['suggestion']}")
        if entry.get("reason"):
            lines.append(f"    why: {entry['reason']}")
        if entry.get("command"):
            lines.append(f"    -> {entry['command']}")
    return "\n".join(lines)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "advice",
        help="Deterministic study advice from stored state (contract: advice).",
    )
    _tutor.add_json(p)
    _tutor.add_learner(p)
    p.set_defaults(func=cmd_advice, json=False)
