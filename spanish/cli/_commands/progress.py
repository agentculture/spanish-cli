"""``spanish progress`` — where the learner stands in this subject.

Read-only. Emits the contract ``progress`` payload: per-item mastery on the
shared ladder, counters, weak items, and the subject's own within-subject next
recommendation. No LLM, no network — a pure function of stored state.
"""

from __future__ import annotations

import argparse

from spanish.cli._commands import _tutor
from spanish.tutor import engine


def cmd_progress(args: argparse.Namespace) -> int:
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    payload = engine.progress_payload(st, learner)
    text = _render(payload)
    return _tutor.emit(payload, args, text=text)


def _render(payload: dict) -> str:
    nxt = payload["next"]
    lines = [
        f"# Progress — {payload['learner']} ({payload['subject']})",
        "",
        f"items: mastered {payload['items_mastered']}/{payload['items_total']} "
        f"(touched {payload['items_touched']})",
        f"next:  {nxt['text']}",
        f"       -> {nxt['command']}",
    ]
    if payload["weak"]:
        lines += ["", "weak items:"]
        lines += [f"  - {w['item_id']} ({w['mastery']})" for w in payload["weak"]]
    return "\n".join(lines)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "progress",
        help="Show the learner's mastery, counters, and next step (contract: progress).",
    )
    _tutor.add_json(p)
    _tutor.add_learner(p)
    p.set_defaults(func=cmd_progress, json=False)
