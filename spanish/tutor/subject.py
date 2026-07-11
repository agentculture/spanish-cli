"""Subject identity — the Spanish-specific knobs.

Ported from french-cli's ``french.tutor.subject`` (task t4 of the learn
uplift); this is the *first* module a subject port rewrites: everything here
is language-specific, and nothing else in :mod:`spanish.tutor` hard-codes
"Spanish", "es", or the persona. The contract plumbing (``state``, ``engine``,
``stories``, ``contract_cite``, and the CLI command chassis) is
subject-agnostic and ports unchanged.

Port checklist for the next sibling language tutor (see
``docs/contract-provenance.md`` for the full token map):

* ``SUBJECT_ID`` ``"spanish"`` → ``"<language>"``
* ``COMMAND``    ``"spanish"`` → ``"<language>"``  (the console script on PATH)
* ``DISPLAY_NAME`` / ``LANGUAGE`` / ``TAGLINE`` / ``DESCRIPTION`` / ``PERSONA``
* the whole of :mod:`spanish.tutor.curriculum` (module/lesson/item content)
* the ``content/stories/*.json`` files
"""

from __future__ import annotations

#: The subject's registry id (matches ``^[a-z][a-z0-9-]*$``). The value learn-cli
#: keys this subject on, and the ``subject`` field of every contract payload.
SUBJECT_ID = "spanish"

#: The installed console script on PATH. Embedded verbatim in every ``command``
#: and ``record_with`` line a directive hands the driver, so it must be runnable.
COMMAND = "spanish"

#: Human-facing display name (the web face's course title).
DISPLAY_NAME = "Spanish"

#: BCP-47 tag of the language being taught.
LANGUAGE = "es"

#: One-line hook for the catalog.
TAGLINE = "Written and spoken Spanish through graded stories, lessons, and practice."

#: Longer self-description for ``overview``.
DESCRIPTION = (
    "A graded-reader Spanish tutor: greeting-to-getting-around lessons, market "
    "and cafe stories, and spaced practice from A1 upward. The CLI is LLM-free "
    "— it resolves what to teach and emits structured teaching directives; an "
    "agent or human driver does the conversational tutoring over --json."
)

#: The tutor persona a directive hands the driving agent (verb-agnostic voice).
PERSONA = (
    "You are a patient, practical Spanish tutor. Teach in short spoken exchanges, "
    "start from what the learner already knows, and lean less on English as they "
    "improve. Encourage, correct gently, and keep every turn usable out loud."
)
