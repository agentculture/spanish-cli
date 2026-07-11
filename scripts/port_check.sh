#!/usr/bin/env bash
# port_check.sh — verify spanish-cli's tutor port stays language-token-only
# relative to french-cli's reference implementation (task t4 of the learn
# uplift). See docs/contract-provenance.md and CLAUDE.md for the port spec.
#
# For every "mechanical" file (the tutor engine, state, stories, contract_cite,
# and the CLI command chassis), this script normalizes both this repo's copy
# and french-cli's copy with the same token map and diffs the result — a clean
# port shows zero output. Content files (subject.py, curriculum.py, the dev
# stories, catalog prose examples, docs/README prose) are expected to diverge
# and are only *listed*, not diffed byte-for-byte.
#
# Usage:
#   scripts/port_check.sh [path-to-french-cli-checkout]
#
# Default french-cli path: ../french-cli relative to this repo's parent
# (i.e. a sibling checkout at /home/spark/git/french-cli in this workspace).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRENCH="${1:-$(cd "$HERE/../french-cli" 2>/dev/null && pwd || echo /home/spark/git/french-cli)}"

if [ ! -d "$FRENCH" ]; then
  echo "error: french-cli checkout not found at '$FRENCH'" >&2
  echo "hint: pass its path as the first argument" >&2
  exit 2
fi

# Base token map: package/command name + env-var + path-segment tokens.
# Order matters (longer/more-specific tokens first).
BASE_SED='s/FRENCH_CLI/SPANISH_CLI/g; s/French/Spanish/g; s/french_cli/spanish_cli/g; s/french/spanish/g'

# A few files carry curriculum-specific example tokens (item/lesson/module ids)
# inside otherwise-generic docstrings or catalog examples. Extend the base map
# for just those files so the mechanical diff still holds.
CURRICULUM_SED='
s/fr\.greetings\.bonjour/es.saludos.hola/g;
s/fr\.greetings\.presentations/es.saludos.presentaciones/g;
s/fr\.numbers\.compter/es.numeros.contar/g;
s/fr\.numbers\.prix/es.numeros.precios/g;
s/fr\.food\.marche/es.comida.mercado/g;
s/fr\.food\.commander/es.comida.pedir/g;
s/fr\.routine\.journee/es.rutina.dia/g;
s/fr\.ville\.directions/es.ciudad.direcciones/g;
s/fr\.ville\.transport/es.ciudad.transporte/g;
s/l\.greetings/l.saludos/g;
s/l\.numbers/l.numeros/g;
s/l\.food/l.comida/g;
s/l\.routine/l.rutina/g;
s/l\.directions/l.direcciones/g;
s/premiers-pas/primeros-pasos/g;
s/la-vie-quotidienne/la-vida-cotidiana/g;
s/en-ville/en-la-ciudad/g;
s/prix-1/precios-1/g;
'

# The cited-by provenance line embeds this port's task id (t4 upstream vs t5
# here); normalize it away so an intentional, expected difference does not
# fail the mechanical check.
TASK_SED='s/task t[0-9]\+/task tN/g'

FAIL=0

# --- Tier 1: byte-verbatim citations (no token substitution at all) --------
VERBATIM_FILES=(
  "spanish/contract_cite/_validate.py::french/contract_cite/_validate.py"
  "spanish/contract_cite/schemas/advice.json::french/contract_cite/schemas/advice.json"
  "spanish/contract_cite/schemas/doctor.json::french/contract_cite/schemas/doctor.json"
  "spanish/contract_cite/schemas/error.json::french/contract_cite/schemas/error.json"
  "spanish/contract_cite/schemas/lesson.json::french/contract_cite/schemas/lesson.json"
  "spanish/contract_cite/schemas/overview.json::french/contract_cite/schemas/overview.json"
  "spanish/contract_cite/schemas/practice.json::french/contract_cite/schemas/practice.json"
  "spanish/contract_cite/schemas/progress.json::french/contract_cite/schemas/progress.json"
  "spanish/contract_cite/schemas/record.json::french/contract_cite/schemas/record.json"
  "spanish/contract_cite/schemas/story.json::french/contract_cite/schemas/story.json"
  "spanish/contract_cite/schemas/story_list.json::french/contract_cite/schemas/story_list.json"
  "spanish/contract_cite/schemas/story_read.json::french/contract_cite/schemas/story_read.json"
)

echo "== Tier 1: verbatim citations (no substitution) =="
for pair in "${VERBATIM_FILES[@]}"; do
  a="${pair%%::*}"
  b="${pair##*::}"
  if [ "$a" = "spanish/contract_cite/_validate.py" ]; then
    # The provenance docstring's "cited by" line legitimately differs
    # (consumer name + task id); normalize just that before the verbatim diff.
    if diff -q <(sed "$TASK_SED" "$HERE/$a") <(sed "s/french-cli/spanish-cli/; $TASK_SED" "$FRENCH/$b") >/dev/null; then
      echo "  OK   $a"
    else
      echo "  DIFF $a"
      diff -u <(sed "$TASK_SED" "$HERE/$a") <(sed "s/french-cli/spanish-cli/; $TASK_SED" "$FRENCH/$b") || true
      FAIL=1
    fi
  else
    if diff -q "$HERE/$a" "$FRENCH/$b" >/dev/null; then
      echo "  OK   $a"
    else
      echo "  DIFF $a"
      diff -u "$HERE/$a" "$FRENCH/$b" || true
      FAIL=1
    fi
  fi
done

# --- Tier 2: mechanical files (language-token substitution only) -----------
MECHANICAL_FILES=(
  "spanish/tutor/engine.py::french/tutor/engine.py"
  "spanish/tutor/state.py::french/tutor/state.py"
  "spanish/tutor/stories.py::french/tutor/stories.py"
  "spanish/tutor/__init__.py::french/tutor/__init__.py"
  "spanish/cli/__init__.py::french/cli/__init__.py"
  "spanish/cli/_errors.py::french/cli/_errors.py"
  "spanish/cli/_output.py::french/cli/_output.py"
  "spanish/cli/_commands/__init__.py::french/cli/_commands/__init__.py"
  "spanish/cli/_commands/_tutor.py::french/cli/_commands/_tutor.py"
  "spanish/cli/_commands/advice.py::french/cli/_commands/advice.py"
  "spanish/cli/_commands/cli.py::french/cli/_commands/cli.py"
  "spanish/cli/_commands/doctor.py::french/cli/_commands/doctor.py"
  "spanish/cli/_commands/explain.py::french/cli/_commands/explain.py"
  "spanish/cli/_commands/learn.py::french/cli/_commands/learn.py"
  "spanish/cli/_commands/lesson.py::french/cli/_commands/lesson.py"
  "spanish/cli/_commands/overview.py::french/cli/_commands/overview.py"
  "spanish/cli/_commands/practice.py::french/cli/_commands/practice.py"
  "spanish/cli/_commands/progress.py::french/cli/_commands/progress.py"
  "spanish/cli/_commands/story.py::french/cli/_commands/story.py"
  "spanish/cli/_commands/whoami.py::french/cli/_commands/whoami.py"
  "spanish/explain/__init__.py::french/explain/__init__.py"
  "spanish/__init__.py::french/__init__.py"
  "spanish/__main__.py::french/__main__.py"
)

# Files within the mechanical set that also carry curriculum-example tokens
# (docstring examples referencing item/lesson ids) and need the extended map.
CURRICULUM_EXAMPLE_FILES=(
  "spanish/cli/_commands/record.py"
)

echo
echo "== Tier 2: mechanical files (language-token substitution) =="
for pair in "${MECHANICAL_FILES[@]}"; do
  a="${pair%%::*}"
  b="${pair##*::}"
  extra=""
  for f in "${CURRICULUM_EXAMPLE_FILES[@]}"; do
    [ "$a" = "$f" ] && extra="$CURRICULUM_SED"
  done
  if diff -q <(sed "$BASE_SED $extra" "$FRENCH/$b") "$HERE/$a" >/dev/null; then
    echo "  OK   $a"
  else
    echo "  DIFF $a"
    diff -u <(sed "$BASE_SED $extra" "$FRENCH/$b") "$HERE/$a" || true
    FAIL=1
  fi
done

# spanish/contract_cite/__init__.py: mechanical, but its provenance docstring
# legitimately carries this repo's own task-id stamp (t5, vs t4 upstream);
# normalize that one token out of *both* sides before comparing.
a="spanish/contract_cite/__init__.py"
b="french/contract_cite/__init__.py"
if diff -q <(sed "$BASE_SED" "$FRENCH/$b" | sed "$TASK_SED") <(sed "$TASK_SED" "$HERE/$a") >/dev/null; then
  echo "  OK   $a"
else
  echo "  DIFF $a"
  diff -u <(sed "$BASE_SED" "$FRENCH/$b" | sed "$TASK_SED") <(sed "$TASK_SED" "$HERE/$a") || true
  FAIL=1
fi

# --- Tier 3: mechanical + curriculum-id example map (catalog prose) --------
echo
echo "== Tier 3: catalog.py (language tokens + curriculum-id examples) =="
if diff -q <(sed "$BASE_SED; $CURRICULUM_SED" "$FRENCH/french/explain/catalog.py") "$HERE/spanish/explain/catalog.py" >/dev/null; then
  echo "  OK   spanish/explain/catalog.py"
else
  echo "  DIFF spanish/explain/catalog.py"
  diff -u <(sed "$BASE_SED; $CURRICULUM_SED" "$FRENCH/french/explain/catalog.py") "$HERE/spanish/explain/catalog.py" || true
  FAIL=1
fi

# --- Intentional divergence (content) — listed for the record, not diffed --
echo
echo "== Intentional content divergence (not mechanically diffed) =="
cat <<'EOF'
  spanish/tutor/subject.py           — subject identity knobs (Spanish)
  spanish/tutor/curriculum.py        — Spanish curriculum content (3 modules /
                                        5 lessons / 9 items / 18 exercises,
                                        same structure as french/tutor/curriculum.py)
  content/stories/dev-*.json         — Spanish dev stories (dev-cafe, dev-directions,
                                        dev-mercado; item_id namespace es.*)
  content/stories/es-*.json          — the 11-story graded-reader ladder (pre-existing,
                                        out of scope for this port)
  docs/contract-provenance.md        — provenance stamp (cited-by names this repo/task)
  README.md, pyproject.toml          — per-project prose/metadata (description,
                                        skill count, etc.)
  CLAUDE.md                          — this repo's own runtime prompt (not a
                                        french-cli artifact)
EOF

echo
if [ "$FAIL" -eq 0 ]; then
  echo "port_check: PASS — mechanical file set matches french-cli modulo language tokens."
  exit 0
else
  echo "port_check: FAIL — unexpected divergence in the mechanical file set (see DIFF entries above)."
  exit 1
fi
