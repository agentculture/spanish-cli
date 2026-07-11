"""Shared test fixtures.

Every test runs with ``$SPANISH_CLI_LEARN_HOME`` pointed at a fresh temp dir, so
no test reads or writes the developer's real learner state under
``~/.local/share/spanish_cli/learn``. Function-scoped, so each test starts from
an empty state store.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from spanish.cli import main


@pytest.fixture(autouse=True)
def learn_home(tmp_path, monkeypatch) -> str:
    """Isolate per-learner state in a temp dir for every test."""
    home = tmp_path / "learn-home"
    monkeypatch.setenv("SPANISH_CLI_LEARN_HOME", str(home))
    # Guard against a stray learner env leaking a real id into a test.
    monkeypatch.delenv("SPANISH_CLI_LEARNER", raising=False)
    return str(home)


def run_json(capsys: pytest.CaptureFixture[str], argv: list[str]) -> tuple[int, Any]:
    """Run a verb with --json, returning ``(exit_code, parsed_stdout)``.

    stderr is left in the capture buffer for the caller to inspect if needed.
    """
    rc = main(argv)
    out = capsys.readouterr().out
    return rc, (json.loads(out) if out.strip() else None)
