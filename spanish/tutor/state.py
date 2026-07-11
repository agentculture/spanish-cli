"""Per-learner tutor state — one JSON file per learner, XDG-pathed, atomic.

The subject CLI owns the learner's mastery ladder and raw-result history *within
this subject*; learn-cli owns the cross-subject ledger and all scoring. This
module is that subject-side store. It is pure logic — no argparse, no printing;
the CLI layer calls it and renders.

Design (carried over from culture-guide's proven ``teach.state``, generalized to
the contract):

* **XDG path resolution** — ``$SPANISH_CLI_LEARN_HOME`` >
  ``$XDG_DATA_HOME/spanish_cli/learn`` > ``~/.local/share/spanish_cli/learn``.
* **Atomic writes** — write a temp file in the same dir, then ``os.replace``
  (atomic on POSIX), so two driver processes can never leave a half-written
  file.
* **Tolerant-but-typed loads** — missing fields fall back to defaults (an older
  file still loads); a *future* ``state_version``, a learner-id mismatch, or a
  wrong-typed field is refused with :class:`StateError` (the CLI turns it into a
  clean environment error) rather than crashing deeper.
* **Mastery never regresses on inference** — ``fail → introduced``,
  ``partial → practiced``, ``pass → mastered``; an explicit ``mastery`` overrides.

Nothing here is Spanish-specific: the store keys off ``subject.SUBJECT_ID`` and
the item ids the curriculum defines, so a sibling language tutor reuses it as-is.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from spanish.contract_cite import MASTERY_LEVELS, RESULTS
from spanish.tutor import subject

#: Internal on-disk state-file version (distinct from the contract's payload
#: ``schema_version``). Bumped only when this file's own shape changes.
STATE_VERSION = 1

#: Activities a record may report (matches the contract ``recorded.activity``).
ACTIVITIES: tuple[str, ...] = ("lesson", "practice", "story")

# A raw result implies *at least* this mastery level when --mastery is omitted.
# The "pass" key trips bandit B105 (reads it as a password); it is a result
# label, not a secret.
_RESULT_TO_MASTERY = {  # nosec B105
    "fail": "introduced",
    "partial": "practiced",
    "pass": "mastered",
}

#: Env var a learner can set to avoid passing --learner every call.
_LEARNER_ENV = "SPANISH_CLI_LEARNER"

#: Env var overriding the state directory (highest precedence, per the contract).
_HOME_ENV = "SPANISH_CLI_LEARN_HOME"

_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]")


class StateError(Exception):
    """Raised on an unreadable / future-version / inconsistent state file."""


# ---------------------------------------------------------------------------
# Identity + path resolution
# ---------------------------------------------------------------------------
def resolve_learner(explicit: str | None = None) -> str:
    """Learner id: ``--learner`` > ``$SPANISH_CLI_LEARNER`` > OS user > ``default``.

    The contract requires the resolved id to be echoed in every payload's
    ``learner`` field, even when defaulted; callers pass the return value through.
    The learner may be a human or an agent.
    """
    candidate = explicit or os.environ.get(_LEARNER_ENV)
    if not candidate:
        try:
            candidate = getpass.getuser()
        except Exception:  # noqa: BLE001 - getuser can raise on odd environments
            candidate = "default"
    return candidate.strip() or "default"


def state_dir() -> Path:
    """Data dir: ``$SPANISH_CLI_LEARN_HOME`` > ``$XDG_DATA_HOME/spanish_cli/learn``
    > ``~/.local/share/spanish_cli/learn``."""
    override = os.environ.get(_HOME_ENV)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / "spanish_cli" / "learn"


def _safe_filename(learner: str) -> str:
    """A filesystem-safe, collision-free stem for a learner id.

    A plain sanitized id can collide (``a/b`` and ``a_b`` both → ``a_b``). When
    sanitization changes the id, a short content hash of the *original* is
    appended so distinct learners never share a file. Already-safe ids keep
    their readable name.
    """
    safe = _SAFE_ID.sub("_", learner)
    if safe != learner or not safe:
        digest = hashlib.sha256(learner.encode("utf-8")).hexdigest()[:8]
        safe = f"{safe or 'id'}-{digest}"
    return safe


def state_path(learner: str) -> Path:
    return state_dir() / f"{_safe_filename(learner)}.json"


# ---------------------------------------------------------------------------
# Time (injectable for tests)
# ---------------------------------------------------------------------------
def now_iso(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


# ---------------------------------------------------------------------------
# Construction / load / save
# ---------------------------------------------------------------------------
def new_state(learner: str, *, now: datetime | None = None) -> dict[str, Any]:
    stamp = now_iso(now)
    return {
        "state_version": STATE_VERSION,
        "subject": subject.SUBJECT_ID,
        "learner": learner,
        "started_at": stamp,
        "last_seen_at": stamp,
        "current": None,
        "mastery": {},
        "history": [],
        "repeats": {},
    }


# Expected JSON type per field — a present field of the wrong type means a
# malformed (but parseable) file, refused cleanly rather than crashed on later.
_FIELD_TYPES: dict[str, type | tuple[type, ...]] = {
    "started_at": str,
    "last_seen_at": str,
    "current": (dict, type(None)),
    "mastery": dict,
    "history": list,
    "repeats": dict,
}


def _coerce(raw: dict[str, Any], learner: str) -> dict[str, Any]:
    """Typed, identity-safe projection of ``raw`` onto the current schema."""
    embedded = raw.get("learner")
    if embedded is not None and embedded != learner:
        raise StateError(f"state file for '{learner}' carries a different learner ({embedded!r})")
    base = new_state(learner)
    for key, expected in _FIELD_TYPES.items():
        if key in raw:
            if not isinstance(raw[key], expected):
                raise StateError(f"state field '{key}' has the wrong type")
            base[key] = raw[key]
    base["learner"] = learner
    base["subject"] = subject.SUBJECT_ID
    base["state_version"] = STATE_VERSION
    return base


def load(learner: str) -> dict[str, Any]:
    """Load a learner's state, or a fresh default if none exists.

    Raises :class:`StateError` on a corrupt file or a *newer* state version.
    """
    path = state_path(learner)
    if not path.is_file():
        return new_state(learner)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise StateError(f"cannot read state file {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise StateError(f"state file {path} is not a JSON object")
    version = raw.get("state_version", STATE_VERSION)
    if isinstance(version, int) and version > STATE_VERSION:
        raise StateError(
            f"state file {path} has state_version {version}, "
            f"newer than this CLI supports ({STATE_VERSION})"
        )
    return _coerce(raw, learner)


def save(state: dict[str, Any], *, now: datetime | None = None) -> Path:
    """Atomically persist ``state``; stamps ``last_seen_at``. Returns the path."""
    state["last_seen_at"] = now_iso(now)
    state["state_version"] = STATE_VERSION
    path = state_path(state["learner"])
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)  # atomic on POSIX
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def exists(learner: str) -> bool:
    return state_path(learner).is_file()


def delete(learner: str) -> bool:
    """Remove a learner's state file. Returns True if a file was removed."""
    path = state_path(learner)
    if path.is_file():
        path.unlink()
        return True
    return False


# ---------------------------------------------------------------------------
# Mastery
# ---------------------------------------------------------------------------
def mastery_ordinal(level: str) -> int:
    try:
        return MASTERY_LEVELS.index(level)
    except ValueError:
        return 0


def mastery_of(state: dict[str, Any], item_id: str) -> str:
    return state["mastery"].get(item_id, "unknown")


def set_mastery(state: dict[str, Any], item_id: str, level: str) -> None:
    if level not in MASTERY_LEVELS:
        raise ValueError(f"unknown mastery level '{level}'")
    state["mastery"][item_id] = level


def infer_mastery(result: str) -> str:
    """The mastery level a raw result implies (before the never-regress rule)."""
    return _RESULT_TO_MASTERY[result]


def touch_item(state: dict[str, Any], item_id: str) -> None:
    """First exposure lifts an untouched item to at least ``introduced``."""
    if item_id not in state["mastery"]:
        state["mastery"][item_id] = "introduced"


def set_current(state: dict[str, Any], module_id: str, item_id: str) -> None:
    state["current"] = {"module_id": module_id, "item_id": item_id}


def bump_repeat(state: dict[str, Any], lesson_id: str) -> int:
    """Increment the harder-repeat count and return the new difficulty rung."""
    count = int(state["repeats"].get(lesson_id, 0)) + 1
    state["repeats"][lesson_id] = count
    return 1 + count


def repeat_difficulty(state: dict[str, Any], lesson_id: str) -> int:
    """Current difficulty rung for a lesson (1 = first pass, +1 per harder repeat)."""
    return 1 + int(state["repeats"].get(lesson_id, 0))


# ---------------------------------------------------------------------------
# The write-back (record)
# ---------------------------------------------------------------------------
def record_result(
    state: dict[str, Any],
    *,
    item_id: str,
    activity: str,
    result: str,
    exercise_id: str | None = None,
    story_id: str | None = None,
    lesson_id: str | None = None,
    correct: int | None = None,
    total: int | None = None,
    duration_seconds: float | None = None,
    notes: str | None = None,
    mastery: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append the raw result to history and update the item's mastery.

    Returns the normalized ``recorded`` object (the contract's scoring input):
    raw observations only — never a score/grade/points. Mastery is inferred from
    ``result`` unless ``mastery`` is given, and inference never regresses.
    """
    if result not in RESULTS:
        raise ValueError(f"result must be one of {', '.join(RESULTS)}")
    if activity not in ACTIVITIES:
        raise ValueError(f"activity must be one of {', '.join(ACTIVITIES)}")
    if mastery is not None and mastery not in MASTERY_LEVELS:
        raise ValueError(f"mastery must be one of {', '.join(MASTERY_LEVELS)}")
    if total is not None and total < 1:
        raise ValueError("total must be >= 1 when given")
    if correct is not None and correct < 0:
        raise ValueError("correct must be >= 0 when given")

    recorded: dict[str, Any] = {
        "item_id": item_id,
        "activity": activity,
        "result": result,
        "at": now_iso(now),
    }
    if exercise_id:
        recorded["exercise_id"] = exercise_id
    if story_id:
        recorded["story_id"] = story_id
    if lesson_id:
        recorded["lesson_id"] = lesson_id
    if correct is not None:
        recorded["correct"] = correct
    if total is not None:
        recorded["total"] = total
    if duration_seconds is not None:
        recorded["duration_seconds"] = duration_seconds
    if notes:
        recorded["notes"] = notes

    state["history"].append(recorded)

    if mastery is not None:
        set_mastery(state, item_id, mastery)
    else:
        inferred = infer_mastery(result)
        if mastery_ordinal(inferred) >= mastery_ordinal(mastery_of(state, item_id)):
            set_mastery(state, item_id, inferred)
    return recorded
