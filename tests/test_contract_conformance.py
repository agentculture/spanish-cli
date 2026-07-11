"""Contract conformance — every tutor verb emits a schema-valid --json payload.

This is the subject-side mirror of learn-cli's ``learn subject doctor`` gate: it
spawns each of the eight verbs, parses ``--json`` stdout, and validates it
against the cited contract schema (``spanish/contract_cite``). It also checks the
contractual exit codes (0 success, 1 user error, 2 environment error) and the
``schema_version`` / ``contract_version`` pins.
"""

from __future__ import annotations

import json

import pytest

from spanish.cli import main
from spanish.contract_cite import CONTRACT_VERSION, validate
from tests.conftest import run_json

LEARNER = "conformance-bot"


def _valid(payload: dict, schema: str) -> None:
    errors = validate(payload, schema)
    assert errors == [], f"{schema} payload invalid: {errors}"


# --- the eight verbs, each schema-valid ------------------------------------


def test_overview_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["overview", "--json"])
    assert rc == 0
    _valid(payload, "overview")
    assert payload["schema_version"] == CONTRACT_VERSION
    assert payload["kind"] == "subject_overview"
    assert payload["subject"] == "spanish"
    # Reconciled: still carries the agent-first rubric's `sections` key.
    assert isinstance(payload["sections"], list) and payload["sections"]


def test_progress_conforms_new_learner(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["progress", "--learner", LEARNER, "--json"])
    assert rc == 0
    _valid(payload, "progress")
    assert payload["learner"] == LEARNER
    assert payload["items_touched"] == 0
    assert payload["next"]["done"] is False


def test_advice_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["advice", "--learner", LEARNER, "--json"])
    assert rc == 0
    _valid(payload, "advice")


def test_story_list_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["story", "list", "--json"])
    assert rc == 0
    _valid(payload, "story_list")
    assert payload["stories"], "dev stories must be discoverable"


def test_story_read_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["story", "read", "dev-cafe", "--learner", LEARNER, "--json"])
    assert rc == 0
    _valid(payload, "story_read")
    _valid(payload["story"], "story")  # embedded story is itself valid content


def test_lesson_start_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["lesson", "start", "l.saludos", "--learner", LEARNER, "--json"])
    assert rc == 0
    _valid(payload, "lesson")
    assert payload["mode"] == "start"
    assert payload["lesson"]["difficulty"] == 1


def test_lesson_next_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["lesson", "next", "--learner", LEARNER, "--json"])
    assert rc == 0
    _valid(payload, "lesson")
    assert payload["mode"] == "next"


def test_lesson_repeat_harder_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    main(["lesson", "start", "l.numeros", "--learner", LEARNER, "--json"])
    capsys.readouterr()
    rc, payload = run_json(
        capsys, ["lesson", "repeat", "l.numeros", "--harder", "--learner", LEARNER, "--json"]
    )
    assert rc == 0
    _valid(payload, "lesson")
    assert payload["mode"] == "repeat"
    assert payload["lesson"]["difficulty"] == 2


def test_practice_scoped_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(
        capsys, ["practice", "es.numeros.precios", "--learner", LEARNER, "--json"]
    )
    assert rc == 0
    _valid(payload, "practice")
    assert payload["scope"] == "es.numeros.precios"


def test_practice_review_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["practice", "--learner", LEARNER, "--json"])
    assert rc == 0
    _valid(payload, "practice")
    assert payload["scope"] == "review"


def test_record_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(
        capsys,
        [
            "record",
            "--learner",
            LEARNER,
            "--item",
            "es.numeros.precios",
            "--activity",
            "practice",
            "--exercise",
            "precios-1",
            "--result",
            "pass",
            "--correct",
            "1",
            "--total",
            "1",
            "--duration-seconds",
            "38",
            "--json",
        ],
    )
    assert rc == 0
    _valid(payload, "record")
    assert payload["recorded"]["item_id"] == "es.numeros.precios"
    assert payload["mastery"]["level"] == "mastered"


def test_doctor_conforms(capsys: pytest.CaptureFixture[str]) -> None:
    rc, payload = run_json(capsys, ["doctor", "--json"])
    assert rc == 0  # healthy repo
    _valid(payload, "doctor")
    assert payload["contract_version"] == CONTRACT_VERSION
    assert payload["kind"] == "subject_doctor"


# --- exit codes + error shape ----------------------------------------------


def test_unknown_story_is_user_error(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["story", "read", "es-does-not-exist", "--json"])
    assert rc == 1  # user error
    err = capsys.readouterr().err
    payload = json.loads(err)
    _valid(payload, "error")
    assert payload["code"] == 1


def test_unknown_practice_scope_is_user_error(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["practice", "no-such-scope", "--json"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().err)
    _valid(payload, "error")


def test_bad_state_file_is_environment_error(
    capsys: pytest.CaptureFixture[str], learn_home
) -> None:
    """A future-version state file is refused as an environment (exit 2) error."""
    import pathlib

    home = pathlib.Path(learn_home)
    home.mkdir(parents=True, exist_ok=True)
    (home / "brokenlearner.json").write_text(
        json.dumps({"state_version": 999, "learner": "brokenlearner"}), encoding="utf-8"
    )
    rc = main(["progress", "--learner", "brokenlearner", "--json"])
    assert rc == 2  # environment error
    payload = json.loads(capsys.readouterr().err)
    _valid(payload, "error")
    assert payload["code"] == 2


def test_record_recorded_forbids_score_fields(capsys: pytest.CaptureFixture[str]) -> None:
    """The recorded object structurally rejects score/grade/points (contract §1)."""
    rc, payload = run_json(
        capsys,
        [
            "record",
            "--learner",
            LEARNER,
            "--item",
            "es.saludos.hola",
            "--result",
            "pass",
            "--json",
        ],
    )
    assert rc == 0
    recorded = payload["recorded"]
    assert "score" not in recorded and "grade" not in recorded and "points" not in recorded
    # And injecting one makes the schema reject it (proves the `not` clause bites).
    recorded_with_score = dict(recorded, score=99)
    bad = dict(payload, recorded=recorded_with_score)
    assert validate(bad, "record") != []
