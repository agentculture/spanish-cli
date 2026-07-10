# spanish-cli

Agent + CLI that turns Claude into a private Spanish tutor: track progress, get an overview, get advice, read stories, and learn & practice Spanish (written and spoken) online from your phone.

## What you get

- **An agent-first CLI** cited from [teken](https://github.com/agentculture/teken)
  (`afi-cli`) — the runtime package has no third-party dependencies.
- **A mesh identity** — `culture.yaml` (`suffix` + `backend`) and the matching
  resident prompt file (`AGENTS.colleague.md`, since this template runs
  `backend: colleague`).
- **The canonical guildmaster skill kit** (11 skills) under `.claude/skills/`,
  vendored cite-don't-import. See [`docs/skill-sources.md`](docs/skill-sources.md).
- **A build + deploy baseline** — pytest, lint, the agent-first rubric gate, and
  PyPI Trusted Publishing wired into GitHub Actions.

## Quickstart

```bash
uv sync
uv run pytest -n auto                 # run the test suite
uv run spanish whoami                 # identity from culture.yaml
uv run spanish learn                  # self-teaching prompt (add --json)
uv run teken cli doctor . --strict    # the agent-first rubric gate CI runs
```

The command is `spanish`; `spanish-cli` is the distribution name on PyPI and the
name of this repo.

## CLI

| Verb | What it does |
|------|--------------|
| `whoami` | Report this agent's nick, version, backend, and model from `culture.yaml`. |
| `learn` | Print a structured self-teaching prompt. |
| `explain <path>` | Markdown docs for any noun/verb path. |
| `overview` | Read-only descriptive snapshot of the agent. |
| `doctor` | Check the agent-identity invariants (prompt-file-present, backend-consistency). |
| `cli overview` | Describe the CLI surface itself. |

Every command supports `--json`. Results go to stdout, errors/diagnostics to
stderr (never mixed). Exit codes: `0` success, `1` user error, `2` environment
error, `3+` reserved.

## Status

Scaffolded from `culture-agent-template`; the Spanish-tutor domain is not built
yet. What ships today is the template's agent-first CLI skeleton — the six
introspection verbs above — so the self-describing output (`learn`, `explain`)
still calls itself a template. That prose gets rewritten alongside the first
tutor feature.

See [`CLAUDE.md`](CLAUDE.md) for the conventions (version-bump-every-PR, the
`cicd` PR lane, the agent-first rubric gate, deploy setup).

## License

Apache 2.0 — see [`LICENSE`](LICENSE).
