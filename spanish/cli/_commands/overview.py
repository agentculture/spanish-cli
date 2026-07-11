"""``spanish overview`` — the subject's self-description (contract: subject_overview).

Reconciled surface: this verb is both the agent-first descriptive snapshot *and*
the contract's ``overview`` payload. Because contract payloads are open, the
JSON output carries the contract-required fields (``schema_version``, ``kind:
subject_overview``, ``subject``, ``display_name``, ``description``, ``modules``,
``content``) **and** keeps the ``sections`` key the agent-first rubric checks —
one payload satisfying both.

Learner-independent and side-effect free, so the static web face can build one
sub-page per module straight from it. Descriptive verbs never hard-fail on a
missing target path: an optional ``target`` positional is accepted and ignored,
so ``overview <bogus-path>`` still exits 0.
"""

from __future__ import annotations

import argparse

from spanish.cli._commands.whoami import report
from spanish.cli._output import emit_result
from spanish.tutor import curriculum, engine, stories

_VERBS = [
    "overview — this subject self-description (contract: subject_overview)",
    "progress — the learner's mastery, counters, and next step",
    "advice — deterministic study advice from stored state",
    "story list|read — graded stories + reading directive",
    "lesson start|next|repeat — teaching directives from the curriculum",
    "practice [<scope>] — a batch of exercises to run",
    "record — write back a graded outcome; updates mastery",
    "doctor — self-check + contract pin",
    "whoami / learn / explain / cli overview — agent-first introspection",
]


def _module_items() -> list[str]:
    return [f"{m.id} — {m.title} ({m.level})" for m in curriculum.MODULES]


def agent_sections() -> list[dict[str, object]]:
    """Sections describing the subject + agent (rubric `sections` + text render)."""
    ident = report()
    counts = curriculum.counts()
    return [
        {
            "title": "Identity",
            "items": [
                f"subject: {engine.subject.SUBJECT_ID}",
                f"nick: {ident['nick']}",
                f"version: {ident['version']}",
                f"backend: {ident['backend']}",
                f"model: {ident['model']}",
            ],
        },
        {"title": "Modules", "items": _module_items()},
        {
            "title": "Content",
            "items": [
                f"stories: {stories.story_count()}",
                f"lessons: {counts['lessons']}",
                f"items: {counts['items']}",
                f"exercises: {counts['exercises']}",
            ],
        },
        {"title": "Verbs", "items": list(_VERBS)},
    ]


def cli_sections() -> list[dict[str, object]]:
    """Sections describing the CLI surface itself (used by `cli overview`)."""
    return [
        {
            "title": "Verbs",
            "items": list(_VERBS) + ["cli overview — describe the CLI surface (this command)"],
        },
        {
            "title": "Conventions",
            "items": [
                "every command supports --json",
                "results to stdout, errors/diagnostics to stderr (never mixed)",
                "exit codes: 0 success, 1 user error, 2 environment error, 3+ reserved",
            ],
        },
    ]


def render_text(subject: str, sections: list[dict[str, object]]) -> str:
    lines = [f"# {subject}", ""]
    for section in sections:
        lines.append(f"## {section['title']}")
        for item in section["items"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).rstrip()


def emit_overview(subject: str, sections: list[dict[str, object]], *, json_mode: bool) -> None:
    if json_mode:
        emit_result({"subject": subject, "sections": sections}, json_mode=True)
    else:
        emit_result(render_text(subject, sections), json_mode=False)


def cmd_overview(args: argparse.Namespace) -> int:
    # `target` is accepted for rubric compatibility (descriptive verbs must not
    # hard-fail on a missing path) but overview describes this subject itself.
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        # Contract subject_overview payload, extended (open payload) with the
        # `sections` key the agent-first rubric asserts — one payload, both
        # contracts satisfied.
        payload = engine.overview_payload()
        payload["sections"] = agent_sections()
        emit_result(payload, json_mode=True)
    else:
        emit_result(render_text("spanish-cli", agent_sections()), json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "overview",
        help="Subject self-description: modules, content counts, verbs (subject_overview).",
    )
    p.add_argument(
        "target",
        nargs="?",
        help="Ignored — overview always describes this subject itself. Accepted so a "
        "stray path argument never hard-fails.",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_overview)
