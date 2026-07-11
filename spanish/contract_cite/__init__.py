"""The subject-plugin contract, CITED (cite-don't-import) into spanish-cli.

.. provenance::

    * source repo:    agentculture/learn-cli
    * source paths:   learn/contract/__init__.py (adapted) + learn/contract/schemas/*.json
                      (verbatim) + learn/contract/_validate.py (verbatim)
    * contract:       subject-plugin contract v1.0
    * source commit:  ed81b87 (2026-07-11)
    * cited on:       2026-07-11
    * cited by:       spanish-cli (task t5 of the learn uplift)

spanish-cli is a *subject* hosted by learn-cli, not a dependency of it: its
runtime deps stay ``[]`` and it must never import ``learn``. So the machine-
readable half of the contract (the schemas + the stdlib validator) is copied in
here. spanish-cli validates its own ``--json`` payloads against these schemas in
CI (``tests/test_contract_conformance.py``), which is exactly the conformance
gate learn-cli's registry (t3) runs against the subject as a subprocess.

The ``__init__`` here is *adapted* from ``learn.contract`` (package name +
docstrings), while ``_validate.py`` and ``schemas/*.json`` are *verbatim*
citations. See ``docs/contract-provenance.md`` for the ledger and re-sync
procedure. Keep these in lockstep with the upstream contract version.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from spanish.contract_cite._validate import validate as _validate_instance

#: The contract version this package ships. Payloads carry it as
#: ``schema_version``; the subject pins it via ``doctor``'s ``contract_version``.
CONTRACT_VERSION = "1.0"

#: Ordered mastery ladder every subject reports per item. Index = how
#: well-understood; inference never regresses down this ladder.
MASTERY_LEVELS: tuple[str, ...] = ("unknown", "introduced", "practiced", "mastered")

#: Raw result vocabulary the driver records back. Subjects report these — never
#: numeric scores; learn-cli's motivation layer computes scores from the ledger.
RESULTS: tuple[str, ...] = ("pass", "partial", "fail")

#: Difficulty ladder for stories (graded readers and narrative scenarios).
STORY_LEVELS: tuple[str, ...] = ("beginner", "intermediate", "advanced")

#: Every schema shipped by this contract version (stem of ``schemas/*.json``).
SCHEMA_NAMES: tuple[str, ...] = (
    "overview",
    "progress",
    "advice",
    "story",
    "story_list",
    "story_read",
    "lesson",
    "practice",
    "record",
    "doctor",
    "error",
)


def _schemas_root() -> Any:
    return resources.files(__package__).joinpath("schemas")


def list_schemas() -> tuple[str, ...]:
    """The schema names present on disk, sorted (should equal SCHEMA_NAMES)."""
    root = _schemas_root()
    return tuple(
        sorted(
            entry.name[: -len(".json")] for entry in root.iterdir() if entry.name.endswith(".json")
        )
    )


def load_schema(name: str) -> dict[str, Any]:
    """Load a contract schema by name (e.g. ``"story"``).

    Raises :class:`KeyError` for a name outside :data:`SCHEMA_NAMES` so callers
    fail loudly on typos rather than reading an unshipped file.
    """
    if name not in SCHEMA_NAMES:
        raise KeyError(f"unknown contract schema '{name}' (valid: {', '.join(SCHEMA_NAMES)})")
    text = _schemas_root().joinpath(f"{name}.json").read_text(encoding="utf-8")
    return json.loads(text)


def _loader(ref: str) -> dict[str, Any] | None:
    """Resolve a sibling-file ``$ref`` (``story.json``) to its schema."""
    stem = ref[: -len(".json")] if ref.endswith(".json") else ref
    if stem in SCHEMA_NAMES:
        return load_schema(stem)
    return None


def validate(instance: Any, schema_name: str) -> list[str]:
    """Validate a payload against a named contract schema; [] means valid."""
    return _validate_instance(instance, load_schema(schema_name), loader=_loader)
