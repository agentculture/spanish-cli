"""Unified CLI entry point for spanish-cli.

The agent-first global verbs (``whoami``, ``learn``, ``explain``, ``overview``,
``doctor``) are registered here under :mod:`spanish.cli._commands`,
alongside the ``cli`` noun group. Future noun groups register via their own
``register()`` functions following the same pattern.

Error propagation contract
--------------------------
Every handler raises :class:`spanish.cli._errors.CliError` on
failure; ``main()`` catches it via :func:`_dispatch` and routes through
:mod:`spanish.cli._output`. Unknown exceptions are wrapped into a
``CliError`` so no Python traceback leaks to stderr.

Argparse errors (unknown verb, missing arg) also route through the structured
format — ``_CliArgumentParser`` overrides ``.error()`` and the subparsers are
built with ``parser_class=_CliArgumentParser``. Whether errors render as text or
JSON depends on whether ``--json`` appears in the raw argv (:func:`main` sets
``_json_hint`` before ``parse_args``).
"""

from __future__ import annotations

import argparse
import sys

from spanish import __version__
from spanish.cli._errors import EXIT_USER_ERROR, CliError
from spanish.cli._output import emit_error

_ISSUES_URL = "https://github.com/agentculture/spanish-cli/issues"


class _CliArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that routes errors through :func:`emit_error`.

    Argparse's default error handler writes ``prog: error: <msg>`` to stderr
    and exits 2, skipping the CliError plumbing (and the ``hint:`` line agents
    look for). This subclass emits the structured format and exits with
    :attr:`EXIT_USER_ERROR`.

    JSON mode: parse-time errors happen before ``args.json`` exists, so we rely
    on a class-level ``_json_hint`` that :func:`main` pre-populates by scanning
    raw argv for ``--json``. Shared across all subparser instances.
    """

    _json_hint: bool = False

    def error(self, message: str) -> None:  # type: ignore[override]
        err = CliError(
            code=EXIT_USER_ERROR,
            message=message,
            remediation=f"run '{self.prog} --help' to see valid arguments",
        )
        emit_error(err, json_mode=type(self)._json_hint)
        raise SystemExit(err.code)


def _argv_has_json(argv: list[str] | None) -> bool:
    tokens = argv if argv is not None else sys.argv[1:]
    return any(t == "--json" or t.startswith("--json=") for t in tokens)


def _build_parser() -> argparse.ArgumentParser:
    from spanish.cli._commands import advice as _advice_cmd
    from spanish.cli._commands import cli as _cli_group
    from spanish.cli._commands import doctor as _doctor_cmd
    from spanish.cli._commands import explain as _explain_cmd
    from spanish.cli._commands import learn as _learn_cmd
    from spanish.cli._commands import lesson as _lesson_cmd
    from spanish.cli._commands import overview as _overview_cmd
    from spanish.cli._commands import practice as _practice_cmd
    from spanish.cli._commands import progress as _progress_cmd
    from spanish.cli._commands import record as _record_cmd
    from spanish.cli._commands import story as _story_cmd
    from spanish.cli._commands import whoami as _whoami_cmd

    # prog is the installed console script (`spanish`), not the distribution
    # name (`spanish-cli`). The agent-first rubric resolves the tool's own name
    # from [project.scripts] and requires `explain <that name>` to work.
    parser = _CliArgumentParser(
        prog="spanish",
        description="spanish — a private Spanish tutor (PyPI package: spanish-cli).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    # parser_class propagates to every subparser so their .error() routes
    # through _CliArgumentParser too.
    sub = parser.add_subparsers(dest="command", parser_class=_CliArgumentParser)

    # Agent-first introspection verbs.
    _whoami_cmd.register(sub)
    _learn_cmd.register(sub)
    _explain_cmd.register(sub)
    _cli_group.register(sub)
    # The eight subject-plugin (tutor) verbs, all top-level.
    _overview_cmd.register(sub)
    _progress_cmd.register(sub)
    _advice_cmd.register(sub)
    _story_cmd.register(sub)
    _lesson_cmd.register(sub)
    _practice_cmd.register(sub)
    _record_cmd.register(sub)
    _doctor_cmd.register(sub)

    return parser


def _dispatch(args: argparse.Namespace) -> int:
    """Invoke the registered handler and translate exceptions to exit codes.

    A handler may return ``None`` (success, exit 0) or an ``int`` exit code.
    Failures MUST raise :class:`CliError`; any other exception is wrapped into
    one so no Python traceback leaks.
    """
    json_mode = bool(getattr(args, "json", False))
    try:
        rc = args.func(args)
    except CliError as err:
        emit_error(err, json_mode=json_mode)
        return err.code
    except Exception as err:  # noqa: BLE001 - last-resort; wrap and route cleanly
        wrapped = CliError(
            code=EXIT_USER_ERROR,
            message=f"unexpected: {err.__class__.__name__}: {err}",
            remediation=f"file a bug at {_ISSUES_URL}",
        )
        emit_error(wrapped, json_mode=json_mode)
        return wrapped.code
    return rc if rc is not None else 0


def main(argv: list[str] | None = None) -> int:
    # Pre-parse peek so argparse-level errors honour --json.
    _CliArgumentParser._json_hint = _argv_has_json(argv)
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return _dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
