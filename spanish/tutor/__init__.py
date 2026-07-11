"""The Spanish tutor engine — the subject-plugin contract implementation.

This subpackage is the LLM-free engine behind spanish-cli's eight tutor verbs. It
owns committed content and per-learner state, resolves what to teach next, and
emits structured teaching directives; the driving agent (or human) does the
conversational tutoring and writes results back via ``record``.

Layers:

* :mod:`~spanish.tutor.subject` — the Spanish-specific identity knobs (the first
  thing a sibling language tutor swaps).
* :mod:`~spanish.tutor.curriculum` — committed modules / lessons / items /
  exercises.
* :mod:`~spanish.tutor.stories` — discovery + loading of ``content/stories/``.
* :mod:`~spanish.tutor.state` — per-learner mastery + history, XDG-pathed, atomic.
* :mod:`~spanish.tutor.engine` — deterministic payload builders for every verb.

The contract schemas + validator live cited in :mod:`spanish.contract_cite`.
"""

from __future__ import annotations

__all__ = ["curriculum", "engine", "state", "stories", "subject"]
