"""``spanish practice [<scope>]`` — a batch of exercises to run.

``scope`` may be an item id, a module id, or a lesson id; with no scope (or
``review``) the subject picks the learner's weakest touched items — its
within-subject review mode. Read-only (grading and write-back happen via
``record``). Emits the contract ``practice_directive`` payload.
"""

from __future__ import annotations

import argparse

from spanish.cli._commands import _tutor
from spanish.cli._errors import EXIT_USER_ERROR, CliError
from spanish.tutor import curriculum, engine

_REVIEW_LIMIT = 6


def cmd_practice(args: argparse.Namespace) -> int:
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    scope_arg = args.scope
    if scope_arg is None or scope_arg == "review":
        resolved_scope, exercises = _review_exercises(st)
    else:
        hit = curriculum.exercises_for_scope(scope_arg)
        if hit is None:
            raise CliError(
                code=EXIT_USER_ERROR,
                message=f"no practice scope matches '{scope_arg}'",
                remediation="pass an item id, a module id, a lesson id, or 'review'; "
                "see 'spanish overview --json' for the module/item map",
            )
        resolved_scope, exercise_tuple = hit
        exercises = [engine._exercise_dict(ex) for ex in exercise_tuple]
    payload = engine.practice_payload(learner, scope=resolved_scope, exercises=exercises)
    return _tutor.emit(payload, args, text=_render(payload))


def _review_exercises(st: dict) -> tuple[str, list[dict]]:
    """Weakest touched items' exercises; fall back to the first item when new."""
    exercises: list[dict] = []
    for weak in engine.weak_items(st):
        hit = curriculum.find_item(weak["item_id"])
        if hit is not None:
            exercises.extend(engine._exercise_dict(ex) for ex in hit[2].exercises)
        if len(exercises) >= _REVIEW_LIMIT:
            break
    if not exercises:
        first = curriculum.all_items()[0][2]
        exercises = [engine._exercise_dict(ex) for ex in first.exercises]
    return "review", exercises[:_REVIEW_LIMIT]


def _render(payload: dict) -> str:
    lines = [f"# Practice — {payload['scope']} ({payload['learner']})", ""]
    for ex in payload["exercises"]:
        lines.append(f"- [{ex['type']}] {ex['prompt']}")
    lines += ["", "## Directive"]
    lines += [f"- {step}" for step in payload["directive"]["instructions"]]
    return "\n".join(lines)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "practice",
        help="Get a batch of exercises to run (contract: practice_directive).",
    )
    p.add_argument(
        "scope",
        nargs="?",
        default=None,
        help="An item id, module id, lesson id, or 'review' (default: weakest touched items).",
    )
    _tutor.add_json(p)
    _tutor.add_learner(p)
    p.set_defaults(func=cmd_practice, json=False)
