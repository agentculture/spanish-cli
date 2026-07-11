"""``spanish record`` — the driver's write-back (the motivation layer's input).

The driver reports one graded outcome; the subject appends the raw result to its
history, updates the item's mastery on the ladder (inferred from ``--result``
unless ``--mastery`` is given; inference never regresses), and acks with the
contract ``record_ack`` payload. The ``recorded`` object is raw observations
only — it structurally forbids score/grade/points; learn-cli computes scores.

    spanish record --learner ori --item es.numeros.precios --activity practice \\
      --exercise precios-1 --result pass --correct 1 --total 1 --json
"""

from __future__ import annotations

import argparse

from spanish.cli._commands import _tutor
from spanish.cli._errors import EXIT_USER_ERROR, CliError
from spanish.contract_cite import MASTERY_LEVELS, RESULTS
from spanish.tutor import engine, state


def cmd_record(args: argparse.Namespace) -> int:
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    try:
        recorded = state.record_result(
            st,
            item_id=args.item,
            activity=args.activity,
            result=args.result,
            exercise_id=args.exercise,
            story_id=args.story,
            lesson_id=args.lesson_id,
            correct=args.correct,
            total=args.total,
            duration_seconds=args.duration_seconds,
            notes=args.notes,
            mastery=args.mastery,
        )
    except ValueError as exc:
        raise CliError(
            code=EXIT_USER_ERROR,
            message=str(exc),
            remediation=f"result in {{{','.join(RESULTS)}}}; "
            f"mastery in {{{','.join(MASTERY_LEVELS)}}}",
        ) from exc
    state.save(st)
    level = state.mastery_of(st, args.item)
    payload = engine.record_ack_payload(
        learner,
        recorded=recorded,
        item_id=args.item,
        level=level,
        next_step=engine.recommend_next(st),
    )
    text = (
        f"recorded {args.item} -> {args.result} (mastery {level})\n"
        f"next: {payload['next']['command']}"
    )
    return _tutor.emit(payload, args, text=text)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "record",
        help="Write back a graded outcome; updates mastery (contract: record_ack).",
    )
    p.add_argument("--item", required=True, help="The curriculum item id this result evidences.")
    p.add_argument(
        "--result",
        required=True,
        choices=RESULTS,
        help="The graded outcome: pass | partial | fail.",
    )
    p.add_argument(
        "--activity",
        default="practice",
        choices=state.ACTIVITIES,
        help="Which activity produced the result (default: practice).",
    )
    p.add_argument("--exercise", help="The exercise id, when the result is for one exercise.")
    p.add_argument("--story", help="The story id, when the result came from a story.")
    p.add_argument("--lesson-id", dest="lesson_id", help="The lesson id, for a lesson result.")
    p.add_argument("--correct", type=int, help="Raw count of correct responses (optional).")
    p.add_argument("--total", type=int, help="Raw count of graded responses (optional, >=1).")
    p.add_argument(
        "--duration-seconds",
        dest="duration_seconds",
        type=float,
        help="Time spent, in seconds (optional).",
    )
    p.add_argument("--notes", help="Free-text notes from the driver (optional).")
    p.add_argument(
        "--mastery",
        choices=MASTERY_LEVELS,
        help="Set mastery explicitly (else inferred from --result, never regressing).",
    )
    _tutor.add_json(p)
    _tutor.add_learner(p)
    p.set_defaults(func=cmd_record, json=False)
