"""Smoke tests for the spanish-cli CLI entry point and its verbs."""

from __future__ import annotations

import json

import pytest

from spanish import __version__
from spanish.cli import main
from spanish.explain import known_paths


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_args_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main([])
    assert rc == 0
    assert "usage: spanish" in capsys.readouterr().out


def test_unknown_command_errors(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["bogus"])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert "hint:" in err


# --- whoami ---------------------------------------------------------------


def test_whoami_text(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["whoami"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "nick: spanish-cli" in out
    assert "backend: colleague" in out
    assert "model:" in out


def test_whoami_json(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["whoami", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["nick"] == "spanish-cli"
    assert payload["version"] == __version__
    assert payload["backend"] == "colleague"


# --- learn ----------------------------------------------------------------


def test_learn_text(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["learn"])
    assert rc == 0
    out = capsys.readouterr().out
    assert len(out) >= 200
    assert "spanish-cli" in out
    assert "Exit-code policy" in out
    assert "--json" in out
    assert "explain" in out


def test_learn_json(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["learn", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    # `tool` is the distribution / mesh nick; `command` is what you invoke.
    assert payload["tool"] == "spanish-cli"
    assert payload["command"] == "spanish"
    assert payload["version"] == __version__
    assert payload["json_support"] is True


# --- explain --------------------------------------------------------------


def test_explain_root(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain"])
    assert rc == 0
    out = capsys.readouterr().out
    # Titled by the command; names the distribution so both are discoverable.
    assert out.startswith("# spanish\n")
    assert "spanish-cli" in out


def test_explain_self(capsys: pytest.CaptureFixture[str]) -> None:
    # The agent-first rubric resolves the tool's name from [project.scripts]
    # and requires `explain <that name>` to work. The console script is
    # `spanish`; `spanish-cli` is the distribution / mesh nick. Both resolve.
    for name in ("spanish", "spanish-cli"):
        rc = main(["explain", name])
        assert rc == 0, f"explain {name} failed"
        assert capsys.readouterr().out.startswith("#")


def test_explain_self_matches_console_script() -> None:
    """`explain <console-script>` must resolve — this is what the rubric checks.

    Guards the defect that made `teken cli doctor --strict` fail: the catalog
    keyed its root on the distribution name while the script was named `spanish`.
    """
    from spanish.explain import known_paths

    assert ("spanish",) in known_paths()
    assert ("spanish-cli",) in known_paths()


def test_explain_json(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain", "whoami", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["path"] == ["whoami"]
    assert "spanish whoami" in payload["markdown"]


def test_explain_unknown_path_errors(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain", "nonexistent"])
    assert rc == 1
    captured = capsys.readouterr()
    assert captured.err.startswith("error:")
    assert "hint:" in captured.err


def test_every_catalog_path_resolves(capsys: pytest.CaptureFixture[str]) -> None:
    for path in known_paths():
        rc = main(["explain", *path])
        assert rc == 0, f"explain {' '.join(path)} failed"
        capsys.readouterr()


def _registered_paths() -> list[tuple[str, ...]]:
    """Every command path registered in the argparse tree (nouns + subverbs)."""
    import argparse

    from spanish.cli import _build_parser

    def walk(parser, prefix: tuple[str, ...]) -> list[tuple[str, ...]]:
        found: list[tuple[str, ...]] = []
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, subparser in action.choices.items():
                    found.append(prefix + (name,))
                    found.extend(walk(subparser, prefix + (name,)))
        return found

    return walk(_build_parser(), ())


def test_every_registered_path_has_catalog_entry() -> None:
    """Every registered noun/verb path must have an explain catalog entry."""
    catalog = set(known_paths())
    missing = [p for p in _registered_paths() if p not in catalog]
    assert missing == [], f"registered paths missing an explain entry: {missing}"
