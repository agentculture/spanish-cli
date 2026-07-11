"""``spanish story`` — the shared content surface (list + read).

* ``story list [--level <l>]`` — level-tagged summaries for the catalog
  (learner-independent, so the static site can build from it).
* ``story read <id>`` — the full committed story wrapped in a teaching directive
  (present paragraph-at-a-time, use the glossary on demand, run the comprehension
  exercises, record each result). Learner-scoped: reading updates the learner's
  current position. An unknown id exits 1 with the error shape.

Bare ``spanish story`` defaults to ``story list``.
"""

from __future__ import annotations

import argparse

from spanish.cli._commands import _tutor
from spanish.cli._errors import EXIT_USER_ERROR, CliError
from spanish.tutor import curriculum, engine, state, stories, subject


def cmd_story_list(args: argparse.Namespace) -> int:
    level = getattr(args, "level", None)
    payload = engine.story_list_payload(level)
    return _tutor.emit(payload, args, text=_render_list(payload))


def _render_list(payload: dict) -> str:
    lines = [f"# Stories ({payload['subject']})", ""]
    if not payload["stories"]:
        lines.append("(no stories found)")
        return "\n".join(lines)
    for s in payload["stories"]:
        detail = f" [{s['level_detail']}]" if s.get("level_detail") else ""
        lines.append(f"- {s['id']} — {s['title']} ({s['level']}{detail}, {s['exercises']} ex)")
    return "\n".join(lines)


def cmd_story_read(args: argparse.Namespace) -> int:
    story = stories.read_story(args.story_id)
    if story is None:
        raise CliError(
            code=EXIT_USER_ERROR,
            message=f"no story matches '{args.story_id}'",
            remediation=f"run '{subject.COMMAND} story list --json' to see valid story ids",
        )
    learner = _tutor.resolve_learner(args)
    st = _tutor.load_state(learner)
    _set_position(st, story)
    state.save(st)
    payload = engine.story_read_payload(learner, story)
    return _tutor.emit(payload, args, text=_render_read(payload))


def _set_position(st: dict, story: dict) -> None:
    """Mark the story's first exercise item as the learner's current position."""
    exercises = story.get("exercises", []) or []
    if not exercises:
        return
    item_id = exercises[0].get("item_id")
    if not item_id:
        return
    hit = curriculum.find_item(item_id)
    if hit is not None:
        state.set_current(st, hit[0].id, item_id)
    else:
        st["current"] = {"item_id": item_id}


def _render_read(payload: dict) -> str:
    story = payload["story"]
    lines = [
        f"# {story['title']}  [{story.get('level_detail', story['level'])}]",
        "",
        story["body"],
    ]
    if story.get("glossary"):
        lines += ["", "## Glossary"]
        lines += [f"- {g['term']}: {g['definition']}" for g in story["glossary"]]
    lines += ["", "## Directive"]
    lines += [f"- {step}" for step in payload["directive"]["instructions"]]
    return "\n".join(lines)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "story",
        help="Read graded stories (see 'spanish story list').",
    )
    _tutor.add_json(p)
    _tutor.add_learner(p)
    # Bare `spanish story` lists.
    p.set_defaults(func=cmd_story_list, json=False, level=None)
    noun = p.add_subparsers(dest="story_command", parser_class=type(p))

    ls = noun.add_parser("list", help="List story summaries (contract: story_list).")
    ls.add_argument("--level", choices=("beginner", "intermediate", "advanced"), default=None)
    _tutor.add_json(ls)
    ls.set_defaults(func=cmd_story_list)

    rd = noun.add_parser("read", help="Read one story with a teaching directive (story_read).")
    rd.add_argument("story_id", help="The story id (filename stem under content/stories/).")
    _tutor.add_json(rd)
    _tutor.add_learner(rd)
    rd.set_defaults(func=cmd_story_read)
