"""Shared helpers for the tutor verbs (learner resolution, state, emit).

Every learner-scoped tutor verb (``progress``, ``advice``, ``lesson``,
``practice``, ``record``, ``story read``) resolves a learner id, loads that
learner's state (turning a corrupt/future state file into a clean environment
error), and emits a JSON payload on ``--json``. These helpers keep that plumbing
in one place so the command modules stay thin and the contract conventions —
``--learner`` everywhere, errors as ``{code, message, remediation}`` — hold
uniformly.
"""

from __future__ import annotations

import argparse
from typing import Any

from spanish.cli._errors import EXIT_ENV_ERROR, CliError
from spanish.cli._output import emit_result
from spanish.tutor import state


def add_json(p: argparse.ArgumentParser) -> None:
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")


def add_learner(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--learner",
        help="Learner id (human or agent). Default: $SPANISH_CLI_LEARNER or the OS user.",
    )


def resolve_learner(args: argparse.Namespace) -> str:
    return state.resolve_learner(getattr(args, "learner", None))


def load_state(learner: str) -> dict[str, Any]:
    """Load a learner's state, mapping a bad state file to an env error."""
    try:
        return state.load(learner)
    except state.StateError as exc:
        raise CliError(
            code=EXIT_ENV_ERROR,
            message=str(exc),
            remediation="fix or remove the state file under $SPANISH_CLI_LEARN_HOME "
            "(or $XDG_DATA_HOME/spanish_cli/learn)",
        ) from exc


def emit(payload: dict[str, Any], args: argparse.Namespace, *, text: str | None = None) -> int:
    """Emit ``payload`` as JSON, or ``text`` (falling back to the payload) in text mode."""
    if getattr(args, "json", False):
        emit_result(payload, json_mode=True)
    else:
        emit_result(text if text is not None else payload, json_mode=False)
    return 0
