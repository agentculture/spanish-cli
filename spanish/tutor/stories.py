"""Committed story content — discovery, loading, and validation.

Stories are flat JSON files under ``content/stories/`` (pinned decision:
``filename == story id``), each conforming to the shared contract ``story``
schema. This module globs that directory (no hard-coded filenames or counts, so
the ladder can grow underneath it), loads stories, and builds the ``story list``
/ ``story read`` payload bodies. It is subject-agnostic — the Spanish-ness lives
entirely in the JSON files.

Content-dir resolution (first that exists wins):

1. ``$SPANISH_CLI_CONTENT_DIR`` — explicit override (tests, alternate content);
2. the repo-root ``content/stories/`` walking up from this file (source checkout);
3. the packaged ``spanish/_content/stories/`` (the wheel force-includes it).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from spanish.contract_cite import validate

_CONTENT_ENV = "SPANISH_CLI_CONTENT_DIR"


def _candidate_dirs() -> list[Path]:
    dirs: list[Path] = []
    override = os.environ.get(_CONTENT_ENV)
    if override:
        dirs.append(Path(override).expanduser())
    here = Path(__file__).resolve()
    for parent in here.parents:
        dirs.append(parent / "content" / "stories")
    # Packaged copy next to the installed package (wheel force-include target).
    dirs.append(here.parent.parent / "_content" / "stories")
    return dirs


def content_dir() -> Path | None:
    """The first existing story-content directory, or ``None`` if none exists."""
    for candidate in _candidate_dirs():
        if candidate.is_dir():
            return candidate
    return None


def story_files() -> list[Path]:
    """Every ``*.json`` story file, sorted by filename. Empty if no content dir."""
    root = content_dir()
    if root is None:
        return []
    return sorted(root.glob("*.json"))


def load_story(path: Path) -> dict[str, Any]:
    """Parse one story file to a dict. Raises on unreadable / non-object JSON."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path.name}: story file is not a JSON object")
    return raw


def validate_story(story: dict[str, Any]) -> list[str]:
    """Validate a story object against the cited ``story`` schema ([] = valid)."""
    return validate(story, "story")


def _summary(story: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": story.get("id", ""),
        "title": story.get("title", ""),
        "level": story.get("level", ""),
        "exercises": len(story.get("exercises", []) or []),
    }
    for optional in ("level_detail", "language", "summary"):
        if optional in story:
            out[optional] = story[optional]
    return out


def list_summaries(level: str | None = None) -> list[dict[str, Any]]:
    """Story summaries for the catalog, optionally filtered by coarse ``level``.

    Malformed files are skipped rather than crashing the whole listing; the
    content-validation CI test is what fails the build on a bad file.
    """
    out: list[dict[str, Any]] = []
    for path in story_files():
        try:
            story = load_story(path)
        except (json.JSONDecodeError, ValueError, OSError):
            continue
        if level is not None and story.get("level") != level:
            continue
        out.append(_summary(story))
    return out


def read_story(story_id: str) -> dict[str, Any] | None:
    """Return the full committed story object for ``story_id``, or ``None``.

    Lookup is by filename stem (the pinned ``filename == id`` rule), so it is a
    direct file open, not a directory scan.
    """
    root = content_dir()
    if root is None:
        return None
    path = root / f"{story_id}.json"
    if not path.is_file():
        return None
    try:
        return load_story(path)
    except (json.JSONDecodeError, ValueError, OSError):
        return None


def story_count() -> int:
    """Number of story files (best-effort; 0 when no content dir)."""
    return len(story_files())
