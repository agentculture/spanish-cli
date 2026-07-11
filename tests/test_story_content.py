"""Committed story content validates against the contract story schema.

Globs ``content/stories/*.json`` (no hard-coded filenames or counts, so t7a's
real ladder validates here as it lands) and validates each file against the
cited ``story`` schema, plus the pinned ``filename == id`` rule.
"""

from __future__ import annotations

import json

import pytest

from spanish.contract_cite import validate
from spanish.tutor import stories

_FILES = stories.story_files()


def test_content_dir_exists() -> None:
    assert stories.content_dir() is not None, "content/stories/ must exist"


def test_at_least_one_story() -> None:
    assert _FILES, "expected at least one story file under content/stories/"


@pytest.mark.parametrize("path", _FILES, ids=[p.name for p in _FILES])
def test_story_file_valid(path) -> None:
    story = stories.load_story(path)
    errors = validate(story, "story")
    assert errors == [], f"{path.name} invalid: {errors}"


@pytest.mark.parametrize("path", _FILES, ids=[p.name for p in _FILES])
def test_filename_equals_id(path) -> None:
    story = json.loads(path.read_text(encoding="utf-8"))
    assert path.stem == story.get("id"), f"{path.name}: filename must equal story id"


@pytest.mark.parametrize("path", _FILES, ids=[p.name for p in _FILES])
def test_story_schema_version_and_subject(path) -> None:
    story = json.loads(path.read_text(encoding="utf-8"))
    assert story["schema_version"] == "1.0"
    assert story["subject"] == "spanish"


def test_dev_stories_present_and_prefixed() -> None:
    """The dev fixtures ship and are prefixed 'dev-' so they never collide with t7a."""
    ids = {p.stem for p in _FILES}
    dev_ids = {i for i in ids if i.startswith("dev-")}
    assert dev_ids, "expected dev-prefixed starter stories"
