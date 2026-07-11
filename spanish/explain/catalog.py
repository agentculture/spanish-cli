"""Markdown catalog for ``spanish explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple
and both spellings of the tool's name — ``("spanish",)`` (the installed console
script) and ``("spanish-cli",)`` (the distribution / repo / mesh nick) — resolve
to the root entry. Every registered command path has an entry here
(``test_every_registered_path_has_catalog_entry`` enforces it).

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# spanish

A private, LLM-free Spanish tutor implementing the learn subject-plugin contract.
It owns the committed Spanish content (stories, lessons, exercises) and each
learner's mastery state, resolves what to teach next, and emits structured
teaching directives. The driving agent (or human) does the conversational
tutoring and writes graded outcomes back with `record`.

Installed command: `spanish`. PyPI package and repo: `spanish-cli`. Mesh nick:
`spanish-cli`.

## Tutor verbs (the contract surface)

- `spanish overview` — subject self-description: modules + content counts.
- `spanish progress` — the learner's mastery, counters, and next step.
- `spanish advice` — deterministic study advice from stored state.
- `spanish story list|read <id>` — graded stories + a reading directive.
- `spanish lesson start|next|repeat` — teaching directives from the curriculum.
- `spanish practice [<scope>]` — a batch of exercises to run (no scope = review).
- `spanish record --item <id> --result pass|partial|fail` — write back one outcome.
- `spanish doctor` — self-check + the pinned contract version.

## Agent-first verbs

- `spanish whoami` — identity probe from `culture.yaml`.
- `spanish learn` — structured self-teaching prompt.
- `spanish explain <path>` — markdown docs for any noun/verb.
- `spanish cli overview` — describe the CLI surface.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `spanish explain lesson`
- `spanish explain record`
"""

_WHOAMI = """\
# spanish whoami

Reports the agent's identity from `culture.yaml`: nick (`suffix`), backend,
served model, and the package version. Read-only.

## Usage

    spanish whoami
    spanish whoami --json
"""

_LEARN = """\
# spanish learn

Prints a structured self-teaching prompt for an agent operating the CLI: the
tutor purpose, the eight subject-plugin verbs, the learner/state model, exit-code
policy, `--json` support, and the `explain` pointer.

## Usage

    spanish learn
    spanish learn --json
"""

_EXPLAIN = """\
# spanish explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

Both `spanish explain spanish` and `spanish explain spanish-cli` resolve to this
root entry — the command is `spanish`, the distribution is `spanish-cli`.

## Usage

    spanish explain spanish
    spanish explain lesson
    spanish explain --json <path>
"""

_OVERVIEW = """\
# spanish overview

The subject's self-description (contract `subject_overview`): identity, the
ordered course modules (the web face renders one sub-page per module), and
content counts. Learner-independent and side-effect free.

The `--json` payload carries the contract fields (`schema_version`, `kind`,
`subject`, `display_name`, `description`, `modules`, `content`) plus the
`sections` key the agent-first rubric checks. Accepts an ignored `target` so a
stray path never hard-fails.

## Usage

    spanish overview
    spanish overview --json
"""

_PROGRESS = """\
# spanish progress

Where the learner stands in this subject (contract `progress`): per-item mastery
on the ladder `unknown → introduced → practiced → mastered`, the counters
`items_total`/`items_touched`/`items_mastered`, weak items, and the subject's own
`next` recommendation. Read-only — a pure function of stored state.

## Usage

    spanish progress
    spanish progress --learner ori --json
"""

_ADVICE = """\
# spanish advice

Deterministic study advice derived from stored state (contract `advice`): what to
shore up and why, each entry with a runnable command. No LLM. May seed a single
"start here" entry for a brand-new learner.

## Usage

    spanish advice
    spanish advice --learner ori --json
"""

_STORY = """\
# spanish story

The shared content surface.

- `spanish story list [--level beginner|intermediate|advanced]` — level-tagged
  summaries for the catalog (contract `story_list`, learner-independent).
- `spanish story read <id>` — the full committed story wrapped in a teaching
  directive (contract `story_read`): present paragraph-at-a-time, use the
  glossary on demand, run the comprehension exercises, record each result.
  Learner-scoped; an unknown id exits 1.

Bare `spanish story` lists.

## Usage

    spanish story list --json
    spanish story read dev-cafe --learner ori --json
"""

_STORY_LIST = """\
# spanish story list

Level-tagged story summaries (id, title, level, exercise count) for the catalog
— contract `story_list`. Learner-independent, so the static web catalog builds
from it. Filter with `--level`.

## Usage

    spanish story list
    spanish story list --level beginner --json
"""

_STORY_READ = """\
# spanish story read <id>

Returns one full committed story (the shared `story` schema, verbatim) wrapped in
a teaching directive — contract `story_read`. Learner-scoped: reading updates the
learner's current position. An unknown story id exits 1 with the error shape.

## Usage

    spanish story read dev-cafe
    spanish story read dev-cafe --learner ori --json
"""

_LESSON = """\
# spanish lesson

Start / continue / repeat a lesson (contract `lesson_directive`). The subject
resolves *what* to teach; the directive tells the driver *how*.

- `spanish lesson start [<target>]` — a lesson by lesson id, module id, or item
  id (first exposure lifts its items to `introduced`).
- `spanish lesson next` — continue from mastery state.
- `spanish lesson repeat [<id>] [--harder]` — re-issue a lesson; `--harder`
  increments its integer difficulty rung (never-ending progression).

Bare `spanish lesson` continues from mastery state.

## Usage

    spanish lesson start l.saludos --json
    spanish lesson next --learner ori --json
    spanish lesson repeat l.numeros --harder --json
"""

_LESSON_START = """\
# spanish lesson start [<target>]

Emit a lesson directive for a specific lesson — resolved from a lesson id, a
module id (its first lesson), or an item id (the lesson containing it). With no
target, starts the next lesson from mastery state. First exposure lifts the
lesson's items to `introduced` and sets the current position.

## Usage

    spanish lesson start l.saludos --json
    spanish lesson start primeros-pasos --learner ori --json
"""

_LESSON_NEXT = """\
# spanish lesson next

Emit the lesson directive for the first not-yet-mastered item's lesson —
continuing from the learner's mastery state.

## Usage

    spanish lesson next
    spanish lesson next --learner ori --json
"""

_LESSON_REPEAT = """\
# spanish lesson repeat [<id>] [--harder]

Re-issue a lesson (default: the learner's current or next lesson). `--harder`
increments the lesson's integer difficulty rung and raises the directive's bar —
the repeatable-lessons half of never-ending progression.

## Usage

    spanish lesson repeat l.numeros --json
    spanish lesson repeat l.numeros --harder --learner ori --json
"""

_PRACTICE = """\
# spanish practice [<scope>]

A batch of exercises for the driver to run, grade `pass|partial|fail` against the
answer/rubric, and record — contract `practice_directive`. `scope` may be an item
id, a module id, or a lesson id; with no scope (or `review`) the subject picks the
learner's weakest touched items.

## Usage

    spanish practice es.numeros.precios --json
    spanish practice --learner ori --json      # review the weakest items
"""

_RECORD = """\
# spanish record --item <id> --result pass|partial|fail

The driver's write-back after grading (contract `record_ack`). The subject
appends the raw result to history, updates the item's mastery (inferred from
`--result` unless `--mastery` is given; inference never regresses), and acks with
the normalized `recorded` object — raw observations only, never a score.

Flags: `--activity lesson|practice|story` (default practice), `--exercise <id>`,
`--story <id>`, `--lesson-id <id>`, `--correct N`, `--total N`,
`--duration-seconds F`, `--notes ...`, `--mastery <level>`.

## Usage

    spanish record --item es.numeros.precios --result pass --json
    spanish record --learner ori --item es.numeros.precios --activity practice \\
      --exercise precios-1 --result partial --correct 1 --total 2 --json
"""

_DOCTOR = """\
# spanish doctor

Self-check + contract pin (contract `subject_doctor`). Keeps the mesh
agent-identity checks (`prompt-file-present`, `backend-consistency` →
`colleague` requires `AGENTS.colleague.md`, `skills-present`) and adds the
subject checks: `content-store-present` (stories validate), `learner-state-writable`
(the XDG state dir), and `contract-schemas-pinned`. Emits `contract_version`.
Exit 0 healthy, 2 unhealthy.

## Usage

    spanish doctor
    spanish doctor --json
"""

_CLI = """\
# spanish cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the subject).

## Usage

    spanish cli overview
    spanish cli overview --json
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    # Both the console script and the distribution name resolve to the root.
    ("spanish",): _ROOT,
    ("spanish-cli",): _ROOT,
    ("whoami",): _WHOAMI,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("overview",): _OVERVIEW,
    ("progress",): _PROGRESS,
    ("advice",): _ADVICE,
    ("story",): _STORY,
    ("story", "list"): _STORY_LIST,
    ("story", "read"): _STORY_READ,
    ("lesson",): _LESSON,
    ("lesson", "start"): _LESSON_START,
    ("lesson", "next"): _LESSON_NEXT,
    ("lesson", "repeat"): _LESSON_REPEAT,
    ("practice",): _PRACTICE,
    ("record",): _RECORD,
    ("doctor",): _DOCTOR,
    ("cli",): _CLI,
    ("cli", "overview"): _CLI,
}
