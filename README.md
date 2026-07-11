# spanish-cli

Agent + CLI that turns Claude into a private Spanish tutor: track progress, get an overview, get advice, read stories, and learn & practice Spanish (written and spoken) online from your phone.

## What you get

- **An agent-first CLI** cited from [teken](https://github.com/agentculture/teken)
  (`afi-cli`) — the runtime package has no third-party dependencies.
- **A mesh identity** — `culture.yaml` (`suffix` + `backend`) and the matching
  resident prompt file (`AGENTS.colleague.md`, since this template runs
  `backend: colleague`).
- **The canonical guildmaster skill kit** (14 skills) under `.claude/skills/`,
  vendored cite-don't-import. See [`docs/skill-sources.md`](docs/skill-sources.md).
- **A build + deploy baseline** — pytest, lint, the agent-first rubric gate, and
  PyPI Trusted Publishing wired into GitHub Actions.

## Quickstart

```bash
uv sync
uv run pytest -n auto                 # run the test suite
uv run spanish whoami                  # identity from culture.yaml
uv run spanish learn                   # self-teaching prompt (add --json)
uv run teken cli doctor . --strict    # the agent-first rubric gate CI runs
```

The installed command is **`spanish`**; the PyPI package and repo are
**`spanish-cli`**. `spanish explain spanish` and `spanish explain spanish-cli` both
resolve to the root doc entry.

## CLI

spanish-cli is an **LLM-free tutor engine** that implements the
[learn subject-plugin contract](https://github.com/agentculture/learn-cli): it
owns the committed Spanish content (stories, lessons, exercises) and each
learner's mastery state, resolves what to teach next, and emits structured
teaching **directives**. The driving agent (or human) does the conversational
tutoring the directive describes, grades `pass|partial|fail`, and writes the
result back with `record`. spanish never converses, grades free text, or computes
scores — learn-cli's motivation layer does the scoring.

### Tutor verbs (the contract surface)

| Verb | What it does | Payload `kind` |
|------|--------------|----------------|
| `spanish overview` | Subject self-description: modules + content counts. | `subject_overview` |
| `spanish progress` | The learner's mastery, counters, and next step. | `progress` |
| `spanish advice` | Deterministic study advice from stored state. | `advice` |
| `spanish story list \| read <id>` | Graded stories + a reading directive. | `story_list` / `story_read` |
| `spanish lesson start \| next \| repeat` | Teaching directives from the curriculum. | `lesson_directive` |
| `spanish practice [<scope>]` | A batch of exercises to run (no scope = review). | `practice_directive` |
| `spanish record --item <id> --result …` | Write back one graded outcome; updates mastery. | `record_ack` |
| `spanish doctor` | Self-check + the pinned contract version. | `subject_doctor` |

### Agent-first verbs

| Verb | What it does |
|------|--------------|
| `spanish whoami` | Report this agent's nick, version, backend, and model from `culture.yaml`. |
| `spanish learn` | Print a structured self-teaching prompt. |
| `spanish explain <path>` | Markdown docs for any noun/verb path. |
| `spanish cli overview` | Describe the CLI surface itself. |

Every command supports `--json`. Results go to stdout, errors/diagnostics to
stderr (never mixed). Exit codes: `0` success, `1` user error, `2` environment
error, `3+` reserved.

### Learner state

Learner-scoped verbs take `--learner <id>` (default: `$SPANISH_CLI_LEARNER` or the
OS user; the resolved id is echoed back). State persists one JSON file per
learner under `$SPANISH_CLI_LEARN_HOME` (or `$XDG_DATA_HOME/spanish_cli/learn`, or
`~/.local/share/spanish_cli/learn`), written atomically and resumed across
sessions.

## Content

Stories are committed JSON files under `content/stories/*.json` (flat, one file
per story, `filename == id`), each validated against the shared `story` schema in
CI (`tests/test_story_content.py`). The starter set ships `dev-`prefixed dev
stories; the full graded ladder is authored separately. The curriculum (modules,
lessons, items, exercises) lives as structured data in
`spanish/tutor/curriculum.py`.

The contract schemas + validator are **cited (cite-don't-import)** into
`spanish/contract_cite/` — see [`docs/contract-provenance.md`](docs/contract-provenance.md).

See [`CLAUDE.md`](CLAUDE.md) for the architecture and the full conventions
(version-bump-every-PR, the `cicd` PR lane, deploy setup).

## License

Apache 2.0 — see [`LICENSE`](LICENSE).
