"""Learner-state persistence, XDG path resolution, and mastery inference."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from spanish.tutor import state

# --- path resolution --------------------------------------------------------


def test_home_env_wins(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SPANISH_CLI_LEARN_HOME", str(tmp_path / "explicit"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    assert state.state_dir() == tmp_path / "explicit"


def test_xdg_fallback(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SPANISH_CLI_LEARN_HOME", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    assert state.state_dir() == tmp_path / "xdg" / "spanish_cli" / "learn"


def test_home_default(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SPANISH_CLI_LEARN_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert state.state_dir() == tmp_path / ".local" / "share" / "spanish_cli" / "learn"


def test_learner_resolution_precedence(monkeypatch) -> None:
    monkeypatch.setenv("SPANISH_CLI_LEARNER", "env-user")
    assert state.resolve_learner("explicit") == "explicit"  # flag wins
    assert state.resolve_learner(None) == "env-user"  # then env
    monkeypatch.delenv("SPANISH_CLI_LEARNER", raising=False)
    assert state.resolve_learner(None)  # falls back to OS user, never empty


# --- persistence round-trip -------------------------------------------------


def test_save_load_round_trip() -> None:
    st = state.new_state("ori")
    state.record_result(st, item_id="es.saludos.hola", activity="lesson", result="pass")
    state.set_current(st, "primeros-pasos", "es.saludos.hola")
    path = state.save(st)
    assert path.is_file()

    reloaded = state.load("ori")
    assert reloaded["learner"] == "ori"
    assert reloaded["mastery"]["es.saludos.hola"] == "mastered"
    assert reloaded["current"] == {"module_id": "primeros-pasos", "item_id": "es.saludos.hola"}
    assert len(reloaded["history"]) == 1


def test_resume_across_sessions() -> None:
    st = state.load("resumer")  # fresh
    state.record_result(st, item_id="es.numeros.precios", activity="practice", result="partial")
    state.save(st)
    # A brand new load (new "session") sees the persisted mastery.
    again = state.load("resumer")
    assert again["mastery"]["es.numeros.precios"] == "practiced"


def test_atomic_write_leaves_no_temp_files() -> None:
    st = state.new_state("clean")
    state.save(st)
    leftovers = list(state.state_dir().glob(".tmp-*"))
    assert leftovers == []


def test_load_missing_returns_fresh() -> None:
    st = state.load("never-seen")
    assert st["mastery"] == {}
    assert st["history"] == []
    assert st["current"] is None


def test_future_version_refused() -> None:
    st = state.new_state("future")
    path = state.save(st)
    raw = json.loads(path.read_text())
    raw["state_version"] = 999
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(state.StateError):
        state.load("future")


def test_learner_mismatch_refused() -> None:
    st = state.new_state("owner")
    path = state.save(st)
    raw = json.loads(path.read_text())
    raw["learner"] = "someone-else"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(state.StateError):
        state.load("owner")


# --- mastery inference (never regressing) ----------------------------------


def test_inference_mapping() -> None:
    assert state.infer_mastery("fail") == "introduced"
    assert state.infer_mastery("partial") == "practiced"
    assert state.infer_mastery("pass") == "mastered"


def test_inference_never_regresses() -> None:
    st = state.new_state("ladder")
    state.record_result(st, item_id="x", activity="practice", result="pass")
    assert state.mastery_of(st, "x") == "mastered"
    # A later fail must NOT drop mastery back down.
    state.record_result(st, item_id="x", activity="practice", result="fail")
    assert state.mastery_of(st, "x") == "mastered"
    # History still records every raw result, though.
    assert len(st["history"]) == 2


def test_inference_climbs() -> None:
    st = state.new_state("climb")
    state.record_result(st, item_id="y", activity="practice", result="fail")
    assert state.mastery_of(st, "y") == "introduced"
    state.record_result(st, item_id="y", activity="practice", result="partial")
    assert state.mastery_of(st, "y") == "practiced"
    state.record_result(st, item_id="y", activity="practice", result="pass")
    assert state.mastery_of(st, "y") == "mastered"


def test_explicit_mastery_overrides_inference() -> None:
    st = state.new_state("explicit")
    state.record_result(st, item_id="z", activity="practice", result="fail", mastery="mastered")
    assert state.mastery_of(st, "z") == "mastered"


def test_touch_lifts_to_introduced() -> None:
    st = state.new_state("touch")
    state.touch_item(st, "fresh")
    assert state.mastery_of(st, "fresh") == "introduced"
    # Touching an already-practiced item does not knock it back down.
    state.set_mastery(st, "adv", "practiced")
    state.touch_item(st, "adv")
    assert state.mastery_of(st, "adv") == "practiced"


def test_recorded_object_is_raw_only() -> None:
    st = state.new_state("raw")
    recorded = state.record_result(
        st,
        item_id="es.numeros.precios",
        activity="practice",
        result="partial",
        exercise_id="precios-1",
        correct=1,
        total=2,
        duration_seconds=30.0,
        notes="hesitated on cincuenta",
    )
    assert set(recorded) == {
        "item_id",
        "activity",
        "result",
        "at",
        "exercise_id",
        "correct",
        "total",
        "duration_seconds",
        "notes",
    }
    for forbidden in ("score", "grade", "points"):
        assert forbidden not in recorded


def test_repeat_difficulty_bumps() -> None:
    st = state.new_state("rep")
    assert state.repeat_difficulty(st, "l.numeros") == 1
    assert state.bump_repeat(st, "l.numeros") == 2
    assert state.repeat_difficulty(st, "l.numeros") == 2


def test_bad_inputs_raise_value_error() -> None:
    st = state.new_state("bad")
    with pytest.raises(ValueError):
        state.record_result(st, item_id="a", activity="practice", result="excellent")
    with pytest.raises(ValueError):
        state.record_result(st, item_id="a", activity="dancing", result="pass")
    with pytest.raises(ValueError):
        state.record_result(st, item_id="a", activity="practice", result="pass", total=0)
