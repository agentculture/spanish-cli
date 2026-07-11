"""Payload builders — assemble every contract payload from state + content.

This is the deterministic, LLM-free core: given the curriculum, the committed
stories, and a learner's stored state, it produces the exact ``--json`` shapes
the subject-plugin contract defines (``overview``, ``progress``, ``advice``,
``lesson``, ``practice``, ``record`` ack, ``story list``/``read``). No content
strings are hard-coded here — the Spanish-ness comes from
:mod:`spanish.tutor.subject`, :mod:`spanish.tutor.curriculum`, and the story
files — so a sibling language tutor reuses this module verbatim.

The driver-facing directive *instructions* are language-neutral (the
Spanish-specific voice is in ``subject.PERSONA``), which keeps a sibling-language
port to a token swap of ``subject`` + ``curriculum`` + the story files.
"""

from __future__ import annotations

from typing import Any

from spanish.contract_cite import CONTRACT_VERSION
from spanish.tutor import curriculum, state, stories, subject

_CMD = subject.COMMAND


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _exercise_dict(ex: curriculum.Exercise) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": ex.id,
        "type": ex.type,
        "item_id": ex.item_id,
        "prompt": ex.prompt,
    }
    if ex.choices:
        out["choices"] = list(ex.choices)
    if ex.answer:
        out["answer"] = ex.answer
    if ex.rubric:
        out["rubric"] = ex.rubric
    return out


def _record_line(learner: str, item_id: str, activity: str, *, exercise: str | None = None) -> str:
    line = f"{_CMD} record --learner {learner} --item {item_id} --activity {activity}"
    if exercise:
        line += f" --exercise {exercise}"
    return line + " --result pass|partial|fail --json"


# ---------------------------------------------------------------------------
# Recommendation (the within-subject next step)
# ---------------------------------------------------------------------------
def recommend_next(st: dict[str, Any]) -> dict[str, Any]:
    """First not-yet-mastered item in course order → a runnable next step.

    Untouched item → start its lesson; touched-but-not-mastered → practice it.
    When everything authored is mastered, ``done`` flips true and the step is a
    maintenance/review one (learn-cli then drives depth mode).
    """
    for module, lesson, item in curriculum.all_items():
        level = state.mastery_of(st, item.id)
        if state.mastery_ordinal(level) >= 3:
            continue
        if state.mastery_ordinal(level) == 0:
            return {
                "done": False,
                "module_id": module.id,
                "item_id": item.id,
                "text": f"start '{item.label}' in {module.title}",
                "command": f"{_CMD} lesson start {lesson.id} --json",
            }
        return {
            "done": False,
            "module_id": module.id,
            "item_id": item.id,
            "text": f"practice '{item.label}' in {module.title} to reach mastered",
            "command": f"{_CMD} practice {item.id} --json",
        }
    return {
        "done": True,
        "text": "every item is mastered — review decayed items and try harder repeats",
        "command": f"{_CMD} practice review --json",
    }


def weak_items(st: dict[str, Any]) -> list[dict[str, str]]:
    """Touched-but-not-mastered items, weakest first (course order tiebreak)."""
    out: list[dict[str, str]] = []
    for item_id in curriculum.all_item_ids():
        level = st["mastery"].get(item_id)
        if level is not None and state.mastery_ordinal(level) < 3:
            out.append({"item_id": item_id, "mastery": level})
    out.sort(key=lambda w: state.mastery_ordinal(w["mastery"]))
    return out


# ---------------------------------------------------------------------------
# overview  (subject_overview)
# ---------------------------------------------------------------------------
def overview_payload() -> dict[str, Any]:
    modules = [
        {
            "id": m.id,
            "title": m.title,
            "summary": m.summary,
            "level": m.level,
        }
        for m in curriculum.MODULES
    ]
    content_counts = curriculum.counts()
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "subject_overview",
        "subject": subject.SUBJECT_ID,
        "display_name": subject.DISPLAY_NAME,
        "tagline": subject.TAGLINE,
        "description": subject.DESCRIPTION,
        "language": subject.LANGUAGE,
        "modules": modules,
        "content": {
            "stories": stories.story_count(),
            "lessons": content_counts["lessons"],
            "exercises": content_counts["exercises"] + _story_exercise_count(),
        },
    }


def _story_exercise_count() -> int:
    total = 0
    for summary in stories.list_summaries():
        total += int(summary.get("exercises", 0) or 0)
    return total


# ---------------------------------------------------------------------------
# progress
# ---------------------------------------------------------------------------
def progress_payload(st: dict[str, Any], learner: str) -> dict[str, Any]:
    mastery = dict(st["mastery"])
    mastered = [iid for iid, lvl in mastery.items() if state.mastery_ordinal(lvl) >= 3]
    payload: dict[str, Any] = {
        "schema_version": CONTRACT_VERSION,
        "kind": "progress",
        "subject": subject.SUBJECT_ID,
        "learner": learner,
        "started_at": st.get("started_at", ""),
        "last_seen_at": st.get("last_seen_at", ""),
        "current": st.get("current"),
        "items_total": len(curriculum.all_item_ids()),
        "items_touched": len(mastery),
        "items_mastered": len(mastered),
        "completed": sorted(mastered),
        "mastery": mastery,
        "weak": weak_items(st),
        "next": recommend_next(st),
    }
    return payload


# ---------------------------------------------------------------------------
# advice
# ---------------------------------------------------------------------------
def advice_payload(st: dict[str, Any], learner: str) -> dict[str, Any]:
    advice: list[dict[str, Any]] = []
    if not st["mastery"]:
        nxt = recommend_next(st)
        advice.append(
            {
                "focus": nxt.get("item_id", ""),
                "reason": "You haven't started this subject yet.",
                "suggestion": nxt["text"].replace("start '", "Begin with '"),
                "command": nxt["command"],
            }
        )
    else:
        for weak in weak_items(st)[:3]:
            module, _lesson, item = curriculum.find_item(weak["item_id"]) or (None, None, None)
            label = item.label if item is not None else weak["item_id"]
            advice.append(
                {
                    "focus": weak["item_id"],
                    "reason": f"'{label}' is at '{weak['mastery']}', not yet mastered.",
                    "suggestion": f"Run a short practice pass on {label} before moving on.",
                    "command": f"{_CMD} practice {weak['item_id']} --json",
                }
            )
        if not advice:  # everything touched is mastered
            advice.append(
                {
                    "focus": "",
                    "reason": "Every touched item is mastered.",
                    "suggestion": "Review decayed items and try a harder lesson repeat "
                    "or a fresh story.",
                    "command": f"{_CMD} practice review --json",
                }
            )
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "advice",
        "subject": subject.SUBJECT_ID,
        "learner": learner,
        "advice": advice,
    }


# ---------------------------------------------------------------------------
# lesson  (lesson_directive)
# ---------------------------------------------------------------------------
def _lesson_items_payload(lesson: curriculum.Lesson) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in lesson.items:
        entry: dict[str, Any] = {"id": item.id, "label": item.label, "points": list(item.points)}
        if item.body:
            entry["body"] = item.body
        items.append(entry)
    return items


def lesson_payload(
    learner: str,
    *,
    mode: str,
    module: curriculum.Module,
    lesson: curriculum.Lesson,
    difficulty: int,
) -> dict[str, Any]:
    record_lines = [_record_line(learner, item.id, "lesson") for item in lesson.items]
    record_lines.append(f"{_CMD} progress --learner {learner} --json")
    instructions = [
        "Teach one item at a time; explain each teachable point with a short "
        "spoken exchange the learner completes.",
        "Ask a brief comprehension check after each point and adapt the pace to " "the answers.",
        "Finish with a short role-play that uses the whole lesson in context.",
        "Grade each check pass|partial|fail and record every result before ending " "the session.",
    ]
    if difficulty > 1:
        instructions.insert(
            0,
            f"This is repeat rung {difficulty}: raise the bar — less English, faster "
            "pace, and demand fuller answers than the first pass.",
        )
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "lesson_directive",
        "subject": subject.SUBJECT_ID,
        "learner": learner,
        "mode": mode,
        "lesson": {
            "id": lesson.id,
            "module_id": module.id,
            "title": lesson.title,
            "level": module.level,
            "difficulty": difficulty,
            "objectives": list(lesson.objectives),
            "items": _lesson_items_payload(lesson),
        },
        "directive": {
            "persona": subject.PERSONA,
            "instructions": instructions,
            "record_with": record_lines,
        },
    }


# ---------------------------------------------------------------------------
# practice  (practice_directive)
# ---------------------------------------------------------------------------
def practice_payload(
    learner: str,
    *,
    scope: str,
    exercises: list[dict[str, Any]],
) -> dict[str, Any]:
    first = exercises[0]
    example = _record_line(
        learner, first.get("item_id", scope), "practice", exercise=first.get("id")
    )
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "practice_directive",
        "subject": subject.SUBJECT_ID,
        "learner": learner,
        "scope": scope,
        "exercises": exercises,
        "directive": {
            "persona": subject.PERSONA,
            "instructions": [
                "Run the exercises one at a time, conversationally — do not dump "
                "them as a list.",
                "Grade pass|partial|fail against the answer or rubric; explain any "
                "miss briefly, in context.",
                "Record each result immediately after grading it.",
            ],
            "record_with": [example],
        },
    }


# ---------------------------------------------------------------------------
# record ack  (record_ack)
# ---------------------------------------------------------------------------
def record_ack_payload(
    learner: str,
    *,
    recorded: dict[str, Any],
    item_id: str,
    level: str,
    next_step: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "record_ack",
        "subject": subject.SUBJECT_ID,
        "learner": learner,
        "recorded": recorded,
        "mastery": {"item_id": item_id, "level": level},
        "next": next_step,
    }


# ---------------------------------------------------------------------------
# story list / read
# ---------------------------------------------------------------------------
def story_list_payload(level: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "story_list",
        "subject": subject.SUBJECT_ID,
        "stories": stories.list_summaries(level),
    }


def story_read_payload(learner: str, story: dict[str, Any]) -> dict[str, Any]:
    exercises = story.get("exercises", []) or []
    record_lines: list[str] = []
    if exercises:
        first = exercises[0]
        item_id = first.get("item_id") or story.get("id", "")
        record_lines.append(
            f"{_CMD} record --learner {learner} --item {item_id} "
            f"--exercise {first.get('id', '')} --activity story --result pass|partial|fail --json"
        )
    else:
        record_lines.append(
            f"{_CMD} record --learner {learner} --item {story.get('id', '')} "
            "--activity story --result pass|partial|fail --json"
        )
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "story_read",
        "subject": subject.SUBJECT_ID,
        "learner": learner,
        "story": story,
        "directive": {
            "persona": subject.PERSONA,
            "instructions": [
                "Present the story one paragraph at a time; let the learner attempt "
                "it before translating.",
                "Use the glossary entries when the learner is stuck; do not " "pre-translate.",
                "Run each comprehension exercise conversationally, grade "
                "pass|partial|fail, and record every result.",
            ],
            "record_with": record_lines,
        },
    }
