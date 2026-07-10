# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is right now

`spanish-cli` is intended to be an agent + CLI that turns Claude into a private Spanish tutor (track progress, overview, advice, stories, written and spoken practice from a phone).

**None of that exists yet.** The repo was scaffolded from `culture-agent-template` (commit `ae97e2c`) and the tutor domain has not been built. What is here is the template's *agent-first CLI skeleton*: six introspection verbs (`whoami`, `learn`, `explain`, `overview`, `doctor`, `cli overview`), a mesh identity, a vendored skill kit, and a CI/publish baseline. The runtime package has **zero third-party dependencies** — keep it that way unless there's a reason not to.

Consequence: the CLI still describes itself as "a clonable template for AgentCulture mesh agents" in `spanish/cli/__init__.py`, `spanish/cli/_commands/learn.py`, `spanish/cli/_commands/overview.py`, and `spanish/explain/catalog.py`. When you implement tutor features, rewrite that prose in the same pass — `learn` and `explain` are the agent-facing docs, not decoration.

## Commands

```bash
uv sync                                   # create .venv, install dev group

uv run pytest -n auto                     # full suite (~1s)
uv run pytest tests/test_cli.py::test_whoami_json -v     # a single test
bash .claude/skills/run-tests/scripts/test.sh --ci       # exactly what CI runs

uv run black --check spanish tests        # the four lint gates, in CI order
uv run isort --check-only spanish tests
uv run flake8 spanish tests
uv run bandit -c pyproject.toml -r spanish

uv run teken cli doctor . --strict        # the agent-first rubric gate (see below)
markdownlint-cli2 "**/*.md" "#node_modules" "#.local" "#.claude/skills"
```

Line length is 100 everywhere (black, isort, flake8). Coverage `fail_under = 60`.

### Three names, one tool

The command is **`spanish`**, the distribution on PyPI is **`spanish-cli`**, and the mesh nick (`culture.yaml`'s `suffix`) is also **`spanish-cli`**. `spanish` is canonical for anything user- or agent-facing: argparse's `prog`, every string in `learn` and the explain catalog, every `hint:` remediation. Reserve `spanish-cli` for three things — `importlib.metadata.version("spanish-cli")` in `spanish/__init__.py`, the issues URL, and `_FALLBACK_NICK` in `whoami.py`. `explain spanish-cli` resolves to the root entry as an alias, nothing more.

## The agent-first rubric gate

CI's `lint` job runs `uv run teken cli doctor . --strict`, a 26-check rubric from [teken](https://github.com/agentculture/teken) that the CLI's whole shape exists to satisfy. It passes 26/26; keep it that way.

The check that constrains naming is `explain_self`: the rubric shells out to `explain <console-script-name>`, so `ENTRIES` in `spanish/explain/catalog.py` must contain a key matching whatever `[project.scripts]` declares. Rename the script and you must add the matching catalog key in the same commit.

The rubric is also why the CLI has verbs that look redundant: `learn` must be ≥200 chars and name purpose, commands, exit codes, `--json`, and `explain`; `overview` must not hard-fail on a bogus target path (hence the ignored `target` positional); the `cli` noun exists solely so `cli overview` satisfies `overview_cli_noun_exists`; `doctor` must emit `{healthy, checks: [{id, passed, severity, message, remediation}]}`. Don't "simplify" these away — run the gate first.

## Architecture

### Output and error contract (stable — agents parse this)

Three modules define a contract every command obeys:

- `spanish/cli/_errors.py` — `CliError(code, message, remediation)`. Exit policy: `0` success, `1` user error, `2` environment error, `3+` reserved. Every failure raises `CliError`; nothing else.
- `spanish/cli/_output.py` — **results to stdout, errors and diagnostics to stderr, never mixed.** `--json` routes structured payloads to the same streams.
- `spanish/cli/__init__.py` — `_dispatch()` catches `CliError`, and wraps any other exception into one, so **no Python traceback ever reaches stderr**. Text-mode errors render as `error: <msg>` + `hint: <remediation>`; the `hint:` prefix is what the rubric greps for.

Two subtleties live in `__init__.py`. `_CliArgumentParser` overrides `.error()` so argparse's own failures (unknown verb, bad flag) exit `1` through the structured format instead of argparse's default exit `2`. And because parse-time errors happen before `args.json` exists, `main()` scans raw argv for `--json` and stashes it on the class attribute `_json_hint` before `parse_args`. Any subparser you create must inherit `_CliArgumentParser` (pass `parser_class=type(p)`, as `_commands/cli.py` does) or its parse errors bypass the contract.

### Adding a noun or verb

Each module in `spanish/cli/_commands/` exposes `register(sub)`. To add one:

1. Write the module with `register(sub)` + a `cmd_*(args) -> int | None` handler taking `--json`.
2. Call its `register()` in `_build_parser()` (there's a marked comment).
3. Add a catalog entry in `spanish/explain/catalog.py` — `ENTRIES` is keyed by command-path tuples, e.g. `("cli", "overview")`. `test_every_catalog_path_resolves` iterates every key, and the docstring convention is that every registered path has an entry.
4. Update the `_TEXT` and `_as_json_payload()` command maps in `_commands/learn.py`, and `_VERBS` in `_commands/overview.py`. Nothing enforces this automatically — the rubric only checks `learn`'s markers, not that it's complete.

### Identity: `culture.yaml` and the backend/prompt-file coupling

`culture.yaml` declares `suffix: spanish-cli`, `backend: colleague`, `model: sakamakismile/Qwen3.6-27B-Text-NVFP4-MTP`. Two things follow:

- **`AGENTS.colleague.md` is this agent's resident prompt file, not `CLAUDE.md`.** `doctor` enforces the mapping `claude → CLAUDE.md`, `colleague → AGENTS.colleague.md`, `acp → AGENTS.md`, `gemini → GEMINI.md`. `test_doctor_recognizes_declared_backend` asserts `doctor` stays healthy against whatever `culture.yaml` declares, so changing `backend` without teaching `_PROMPT_FILE` the new mapping fails the suite. (The seed CLAUDE.md this file replaced claimed `backend: claude` — it was wrong.)
- **`whoami` parses `culture.yaml` by hand**, line by line, to preserve the zero-dependency runtime (`_commands/whoami.py`). It walks up from `__file__`, not from the CWD, so it always reports *this* agent's identity rather than whatever `culture.yaml` sits in the caller's directory. In a wheel install no `culture.yaml` ships, and both `whoami` and `doctor` degrade to defaults / a single info check.

## Conventions

**Every PR bumps the version — including docs-only, config-only, and CI-only PRs.** The `version-check` CI job compares `pyproject.toml` against `origin/main` and fails the PR (with a bot comment) if they match. Use the skill: `python3 .claude/skills/version-bump/scripts/bump.py patch|minor|major`, optionally piping `{"added":[...],"changed":[...],"fixed":[...]}` on stdin to fill `CHANGELOG.md`. `__version__` reads from package metadata, so there's no `__init__.py` literal to update.

**PRs go through the `cicd` skill** (`.claude/skills/cicd/scripts/workflow.sh`), which wraps `devex pr` — `lint | open | read | reply | delta`, plus its own `status` and `await` (SonarCloud quality gate + unresolved-thread tally, non-zero exit on a red gate). Requires `devex` >= 0.21, `gh`, and `jq` on PATH.

**`.claude/skills/` is vendored cite-don't-import from [guildmaster](https://github.com/agentculture/guildmaster)** (`ask-colleague` comes directly from `colleague`; `remember` and `recall` from `eidetic-cli`). Don't edit or reformat those scripts as part of unrelated work — markdownlint ignores the tree, Sonar excludes it, and `docs/skill-sources.md` is the provenance ledger with the re-sync procedure and its two tracked divergences (`agex` → `devex`, `outsource` → `ask-colleague`). If a change belongs upstream, lift it to guildmaster and re-vendor.

**Publishing** is PyPI Trusted Publishing via OIDC. `publish.yml` fires on changes to `pyproject.toml` or `spanish/**`: same-repo PRs publish a `.dev<run_number>` build to TestPyPI, pushes to `main` publish to PyPI. Fork PRs skip it.

## Sonar and CI notes

`sonar-project.properties` pins `sonar.sources=spanish` and reads `coverage.xml`; `relative_files = true` in `[tool.coverage.run]` is load-bearing, since absolute or `.venv` paths make SonarCloud report empty coverage. The scan step is guarded by `if: env.SONAR_TOKEN != ''`, so token-less and fork-PR runs stay green without it.
