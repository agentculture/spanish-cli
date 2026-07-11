"""``spanish doctor`` — self-check + contract pin (contract: subject_doctor).

Reconciled surface: keeps the mesh agent-identity checks the template chassis
verified (``prompt-file-present`` / ``backend-consistency`` and ``skills-present``,
mirroring ``steward doctor``) **and** adds the subject-plugin contract's checks
and pin. The JSON payload carries the contract-required fields
(``schema_version``, ``kind: subject_doctor``, ``subject``, ``contract_version``)
alongside the ``healthy`` + ``checks`` shape the agent-first rubric asserts.

``learn subject doctor`` (learn-cli's conformance gate) reads ``contract_version``
first, then validates the other seven verbs against that version's schemas. Exit
0 when healthy, 2 when not (an error-severity check failed).
"""

from __future__ import annotations

import argparse
import os
import tempfile

from spanish.cli._commands.whoami import find_culture_yaml, read_agent_fields
from spanish.cli._output import emit_result
from spanish.contract_cite import CONTRACT_VERSION, SCHEMA_NAMES, list_schemas
from spanish.tutor import state, stories, subject

# backend → required prompt file (the backend-consistency mapping).
_PROMPT_FILE = {
    "claude": "CLAUDE.md",
    "colleague": "AGENTS.colleague.md",
    "acp": "AGENTS.md",
    "gemini": "GEMINI.md",
}


def _identity_checks() -> list[dict[str, object]]:
    """The mesh agent-identity checks (steward doctor's invariants)."""
    cfg = find_culture_yaml()
    if cfg is None:
        return [
            {
                "id": "source-checkout",
                "passed": True,
                "severity": "info",
                "message": "no culture.yaml found alongside the package; identity checks skipped",
                "remediation": "",
            }
        ]
    root = cfg.parent
    backend = read_agent_fields()["backend"]
    checks: list[dict[str, object]] = []
    expected = _PROMPT_FILE.get(backend)
    if expected is None:
        checks.append(
            {
                "id": "backend-consistency",
                "passed": False,
                "severity": "error",
                "message": f"unknown backend '{backend}' in culture.yaml",
                "remediation": f"set backend to one of: {', '.join(sorted(_PROMPT_FILE))}",
            }
        )
    else:
        present = (root / expected).is_file()
        checks.append(
            {
                "id": "prompt-file-present",
                "passed": present,
                "severity": "error",
                "message": f"backend '{backend}' requires {expected} — "
                + ("present" if present else "missing"),
                "remediation": "" if present else f"create {expected} at the repo root",
            }
        )
    skills_dir = root / ".claude" / "skills"
    has_skills = skills_dir.is_dir() and any(skills_dir.iterdir())
    checks.append(
        {
            "id": "skills-present",
            "passed": has_skills,
            "severity": "warning",
            "message": ".claude/skills/ vendored" if has_skills else ".claude/skills/ missing",
            "remediation": "" if has_skills else "vendor the skill kit (see docs/skill-sources.md)",
        }
    )
    return checks


def _content_check() -> dict[str, object]:
    """content-store-present — story files load and validate against story.json."""
    files = stories.story_files()
    if not files:
        return {
            "id": "content-store-present",
            "passed": True,
            "severity": "warning",
            "message": "no story files found under content/stories/ yet",
            "remediation": "add graded stories at content/stories/*.json",
        }
    invalid: list[str] = []
    for path in files:
        try:
            story = stories.load_story(path)
        except Exception:  # noqa: BLE001 - any parse failure is an invalid file
            invalid.append(path.name)
            continue
        if stories.validate_story(story) or path.stem != story.get("id"):
            invalid.append(path.name)
    passed = not invalid
    return {
        "id": "content-store-present",
        "passed": passed,
        "severity": "error",
        "message": (
            f"{len(files)} story file(s) load and validate"
            if passed
            else f"invalid story file(s): {', '.join(invalid)}"
        ),
        "remediation": (
            ""
            if passed
            else "each story must validate against story.json and have " "filename == id"
        ),
    }


def _state_writable_check() -> dict[str, object]:
    """learner-state-writable — the XDG state dir accepts an atomic write."""
    target = state.state_dir()
    try:
        target.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(target), prefix=".doctor-", suffix=".tmp")
        os.close(fd)
        os.unlink(tmp)
        passed = True
        message = f"learner-state dir is writable ({target})"
        remediation = ""
    except OSError as exc:
        passed = False
        message = f"learner-state dir is not writable ({target}): {exc}"
        remediation = "set $SPANISH_CLI_LEARN_HOME to a writable directory"
    return {
        "id": "learner-state-writable",
        "passed": passed,
        "severity": "error",
        "message": message,
        "remediation": remediation,
    }


def _contract_pin_check() -> dict[str, object]:
    """contract-schemas-pinned — the cited schema set matches the pinned version."""
    on_disk = sorted(list_schemas())
    passed = on_disk == sorted(SCHEMA_NAMES)
    return {
        "id": "contract-schemas-pinned",
        "passed": passed,
        "severity": "warning",
        "message": (
            f"subject pins contract {CONTRACT_VERSION} ({len(on_disk)} schemas cited)"
            if passed
            else "cited schema set does not match the pinned contract"
        ),
        "remediation": "" if passed else "re-sync spanish/contract_cite from learn-cli",
    }


def _diagnose() -> dict[str, object]:
    checks = _identity_checks()
    checks += [_content_check(), _state_writable_check(), _contract_pin_check()]
    # healthy = no error-severity check failed (contract rule).
    healthy = not any(c["severity"] == "error" and not c["passed"] for c in checks)
    return {"healthy": healthy, "checks": checks}


def cmd_doctor(args: argparse.Namespace) -> int:
    report = _diagnose()
    payload = {
        "schema_version": CONTRACT_VERSION,
        "kind": "subject_doctor",
        "subject": subject.SUBJECT_ID,
        "contract_version": CONTRACT_VERSION,
        "healthy": report["healthy"],
        "checks": report["checks"],
    }
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result(payload, json_mode=True)
    else:
        status = "healthy" if payload["healthy"] else "unhealthy"
        lines = [f"spanish-cli doctor: {status} (contract {CONTRACT_VERSION})", ""]
        for check in payload["checks"]:
            mark = "ok" if check["passed"] else "FAIL"
            lines.append(f"[{mark}] {check['id']}: {check['message']}")
            if not check["passed"] and check["remediation"]:
                lines.append(f"  hint: {check['remediation']}")
        emit_result("\n".join(lines), json_mode=False)
    # Contract: exit 0 healthy, 2 (environment error) when not.
    return 0 if payload["healthy"] else 2


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "doctor",
        help="Self-check + contract pin (identity, content, state, schemas).",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_doctor)
