"""``spanish lesson`` — start / next / repeat.

The subject resolves *what* to teach; the directive tells the driver *how*:

* ``lesson start [<target>]`` — a specific lesson (by lesson id, module id, or
  item id); first exposure lifts its items to ``introduced``.
* ``lesson next`` — continue from mastery state (the first not-yet-mastered
  item's lesson).
* ``lesson repeat [<id>] [--harder]`` — re-issue a lesson; ``--harder`` bumps its
  integer difficulty rung (the never-ending-progression hook).

Learner-scoped; ``start``/``next`` set the current position and lift items.
Bare ``spanish lesson`` defaults to ``lesson next``.
"""

from __future__ import annotations

import argparse

from spanish.cli._commands import _tutor
from spanish.cli._errors import EXIT_USER_ERROR, CliError
from spanish.tutor import curriculum, engine, state


def _resolve_target(token: str) -> curriculum.LessonTarget:
    try:
        return curriculum.resolve_lesson_target(token)
    except KeyError as exc:
        raise CliError(
            code=EXIT_USER_ERROR,
            message=f"no lesson matches '{token}'",
            remediation="valid targets: " + ", ".join(curriculum.valid_lesson_targets()),
        ) from exc


def _lift_and_position(st: dict, target: curriculum.LessonTarget) -> None:
    for item in target.lesson.items:
        state.touch_item(st, item.id)
    first = target.lesson.items[0]
    state.set_current(st, target.module.id, first.id)


def cmd_lesson_start(args: argparse.Namespace) -> int:
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    if args.target:
        target = _resolve_target(args.target)
    else:
        target = _next_target(st)
    _lift_and_position(st, target)
    state.save(st)
    payload = engine.lesson_payload(
        learner, mode="start", module=target.module, lesson=target.lesson, difficulty=1
    )
    return _tutor.emit(payload, args, text=_render(payload))


def cmd_lesson_next(args: argparse.Namespace) -> int:
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    target = _next_target(st)
    _lift_and_position(st, target)
    state.save(st)
    payload = engine.lesson_payload(
        learner, mode="next", module=target.module, lesson=target.lesson, difficulty=1
    )
    return _tutor.emit(payload, args, text=_render(payload))


def cmd_lesson_repeat(args: argparse.Namespace) -> int:
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    if args.lesson_id:
        target = _resolve_target(args.lesson_id)
    else:
        # Repeat the learner's current lesson, or the next one if none set.
        target = _current_target(st) or _next_target(st)
    if args.harder:
        difficulty = state.bump_repeat(st, target.lesson.id)
    else:
        difficulty = state.repeat_difficulty(st, target.lesson.id)
    state.save(st)
    payload = engine.lesson_payload(
        learner, mode="repeat", module=target.module, lesson=target.lesson, difficulty=difficulty
    )
    return _tutor.emit(payload, args, text=_render(payload))


def _next_target(st: dict) -> curriculum.LessonTarget:
    nxt = engine.recommend_next(st)
    token = nxt.get("item_id") or nxt.get("module_id") or ""
    if token:
        try:
            return curriculum.resolve_lesson_target(token)
        except KeyError:
            pass
    # done / no token → fall back to the first lesson (maintenance repeat).
    module = curriculum.MODULES[0]
    return curriculum.LessonTarget(module=module, lesson=module.lessons[0])


def _current_target(st: dict) -> curriculum.LessonTarget | None:
    current = st.get("current") or {}
    item_id = current.get("item_id")
    if not item_id:
        return None
    hit = curriculum.find_item(item_id)
    if hit is None:
        return None
    return curriculum.LessonTarget(module=hit[0], lesson=hit[1])


def _render(payload: dict) -> str:
    lesson = payload["lesson"]
    lines = [
        f"# Lesson [{payload['mode']}] — {lesson['title']} (rung {lesson['difficulty']})",
        "",
    ]
    for item in lesson["items"]:
        lines.append(f"## {item['label']}  [{item['id']}]")
        lines += [f"- {pt}" for pt in item.get("points", [])]
        lines.append("")
    lines.append("## Directive")
    lines += [f"- {step}" for step in payload["directive"]["instructions"]]
    return "\n".join(lines).rstrip()


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "lesson",
        help="Start / continue / repeat a lesson (contract: lesson_directive).",
    )
    _tutor.add_json(p)
    _tutor.add_learner(p)
    # Bare `spanish lesson` continues from mastery state.
    p.set_defaults(func=cmd_lesson_next, json=False)
    noun = p.add_subparsers(dest="lesson_command", parser_class=type(p))

    st = noun.add_parser(
        "start", help="Start a lesson (by lesson/module/item id, or the next one)."
    )
    st.add_argument("target", nargs="?", help="A lesson id, module id, or item id.")
    _tutor.add_json(st)
    _tutor.add_learner(st)
    st.set_defaults(func=cmd_lesson_start)

    nx = noun.add_parser("next", help="Continue from mastery state.")
    _tutor.add_json(nx)
    _tutor.add_learner(nx)
    nx.set_defaults(func=cmd_lesson_next)

    rp = noun.add_parser("repeat", help="Re-issue a completed lesson; --harder raises the rung.")
    rp.add_argument("lesson_id", nargs="?", help="Lesson to repeat (default: current/next).")
    rp.add_argument("--harder", action="store_true", help="Increment the difficulty rung.")
    _tutor.add_json(rp)
    _tutor.add_learner(rp)
    rp.set_defaults(func=cmd_lesson_repeat)
