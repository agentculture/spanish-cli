"""Markdown catalog for ``spanish explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple
and ``("spanish",)`` both resolve to the root entry; ``("spanish-cli",)`` is
kept as an alias for the distribution name.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# spanish

A clonable template for AgentCulture mesh agents. It carries an agent-first CLI
(cited from the teken `python-cli` reference), a mesh identity (`culture.yaml` +
`CLAUDE.md`), the canonical guildmaster skill kit under `.claude/skills/`, and a
buildable/deployable package baseline. Clone it, rename the package, edit
`culture.yaml`, and you have a new agent.

## Verbs

- `spanish whoami` — identity probe from `culture.yaml`.
- `spanish learn` — structured self-teaching prompt.
- `spanish explain <path>` — markdown docs for any noun/verb.
- `spanish overview` — descriptive snapshot of the agent.
- `spanish doctor` — check the agent-identity invariants.
- `spanish cli overview` — describe the CLI surface.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `spanish explain whoami`
- `spanish explain doctor`
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

Prints a structured self-teaching prompt covering purpose, command map,
exit-code policy, `--json` support, and the `explain` pointer.

## Usage

    spanish learn
    spanish learn --json
"""

_EXPLAIN = """\
# spanish explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

## Usage

    spanish explain spanish
    spanish explain whoami
    spanish explain --json <path>
"""

_OVERVIEW = """\
# spanish overview

Read-only descriptive snapshot of the agent: identity (from `culture.yaml`), the
verb surface, and the sibling-pattern artifacts the template carries. Accepts an
ignored `target` so a stray path never hard-fails.

## Usage

    spanish overview
    spanish overview --json
"""

_DOCTOR = """\
# spanish doctor

Checks the agent-identity invariants `steward doctor` verifies:
prompt-file-present and backend-consistency (`colleague` → `AGENTS.colleague.md`), plus a
skills-present check. Exits 1 when unhealthy.

## Usage

    spanish doctor
    spanish doctor --json
"""

_CLI = """\
# spanish cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the agent).

## Usage

    spanish cli overview
    spanish cli overview --json
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    # The console script name is the canonical self-name: the agent-first
    # rubric's `explain_self` check probes `explain <console-script-name>`.
    ("spanish",): _ROOT,
    # Alias for the distribution/repo name, so `explain spanish-cli` resolves.
    ("spanish-cli",): _ROOT,
    ("whoami",): _WHOAMI,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("overview",): _OVERVIEW,
    ("doctor",): _DOCTOR,
    ("cli",): _CLI,
    ("cli", "overview"): _CLI,
}
