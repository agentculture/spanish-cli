# Cited contract provenance

spanish-cli implements the **learn subject-plugin contract** but is not a
dependency of learn-cli: it is a *subject* that learn-cli hosts as an external
`--json` runtime. Its runtime dependencies stay `[]` and it must never
`import learn`. So the machine-readable half of the contract — the JSON Schemas
and the stdlib validator — is **cited (cite-don't-import)** into
`spanish/contract_cite/`, the same way `.claude/skills/` is vendored from
guildmaster (see [`skill-sources.md`](skill-sources.md)).

Each consumer owns its copy; spanish-cli validates its own tutor-verb `--json`
payloads against these schemas in CI (`tests/test_contract_conformance.py`),
which is exactly the conformance gate learn-cli's registry (t3) runs against the
subject as a subprocess.

## What was cited

| Cited file | Upstream source | Kind | Notes |
|------------|-----------------|------|-------|
| `spanish/contract_cite/_validate.py` | `learn/contract/_validate.py` | **verbatim** | Stdlib-only JSON-Schema validator (no `jsonschema`). Header carries the provenance stamp. Do not edit the body. |
| `spanish/contract_cite/schemas/*.json` (11 files) | `learn/contract/schemas/*.json` | **verbatim** | `overview`, `progress`, `advice`, `story`, `story_list`, `story_read`, `lesson`, `practice`, `record`, `doctor`, `error`. |
| `spanish/contract_cite/__init__.py` | `learn/contract/__init__.py` | **adapted** | Package name (`learn.contract` → `spanish.contract_cite`) and docstrings only; the public API (`validate`, `load_schema`, `list_schemas`, `CONTRACT_VERSION`, `SCHEMA_NAMES`, `MASTERY_LEVELS`, `RESULTS`, `STORY_LEVELS`) is preserved. |

## Provenance stamp

- **Source repo:** `agentculture/learn-cli`
- **Contract:** subject-plugin contract **v1.0** (`docs/specs/subject-plugin-contract.md`)
- **Source commit:** `ed81b87` (2026-07-11)
- **Cited on:** 2026-07-11
- **Cited by:** spanish-cli (task t5 of the learn uplift)

## Re-sync procedure

The contract is authoritative for a `major.minor` version. When learn-cli bumps
it, re-sync the citation deterministically:

```bash
# From the spanish-cli repo root, with a learn-cli checkout at ../learn-cli:
rm -rf spanish/contract_cite/schemas
cp -R ../learn-cli/learn/contract/schemas spanish/contract_cite/schemas
cp ../learn-cli/learn/contract/_validate.py spanish/contract_cite/_validate.py

# Re-apply the two headers (this doc + the _validate.py provenance stamp) and
# bump the "source commit" / "cited on" lines. The __init__.py is adapted, not
# copied — reconcile its API by hand if the upstream API changed.
```

`spanish doctor`'s `contract-schemas-pinned` check verifies the cited schema set
still matches `SCHEMA_NAMES`, and `tests/test_contract_conformance.py` fails the
build if a payload drifts out of the pinned version — so a stale or partial
re-sync is caught in CI, not at a learner's runtime.

## What is *not* cited

learn-cli's registry, conformance-gate runner, motivation layer (scores /
streaks / review queues), and cross-subject learner profile stay in learn-cli.
spanish-cli reports **raw observations only** (`result`, optional
`correct`/`total`, `duration_seconds`) and never computes a score — the
`record` ack's `recorded` object structurally forbids `score`/`grade`/`points`.
