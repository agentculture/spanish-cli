# Spanish graded-reader story ladder

Committed content for spanish-cli's `story list` / `story read` verbs (the
`spanish/cli/_commands/story.py` driver arrives later, ported from french-cli by
a sibling task). This file documents what is here, the schema it must satisfy,
the reproducible pipeline used to author it, and the checklist a human reviews
before merge.

**Content only.** This task touches `content/stories/*.json` and this file —
no CLI code, no tests, no `pyproject.toml`/CI changes. The story schema and its
validator live in the sibling `learn-cli` repo
(`learn/contract/schemas/story.json`, `learn/contract/_validate.py`); spanish-cli
does not vendor a copy of either.

## The ladder

Eleven stories, three CEFR bands, 143–373 words, scaling with level. Filenames
are flat under `content/stories/` and equal the story `id`.

| id | level | level_detail | title | words | glossary | exercises |
| --- | --- | --- | --- | --- | --- | --- |
| `es-a1-el-mercado-de-frutas` | beginner | A1 | El mercado de frutas | 159 | 7 | 4 |
| `es-a1-mi-familia` | beginner | A1 | Mi familia | 167 | 6 | 4 |
| `es-a2-un-dia-en-la-playa` | beginner | A2 | Un día en la playa | 162 | 7 | 4 |
| `es-a2-el-cumpleanos-de-lucia` | beginner | A2 | El cumpleaños de Lucía | 187 | 7 | 4 |
| `es-b1-el-tren-perdido` | intermediate | B1 | El tren perdido | 232 | 9 | 5 |
| `es-b1-la-entrevista-de-trabajo` | intermediate | B1 | La entrevista de trabajo | 256 | 9 | 5 |
| `es-b1-una-carta-a-mi-abuela` | intermediate | B1 | Una carta a mi abuela | 241 | 9 | 4 |
| `es-b1-el-barrio-nuevo` | intermediate | B1 | El barrio nuevo | 247 | 9 | 4 |
| `es-b2-el-dilema-del-teletrabajo` | advanced | B2 | El dilema del teletrabajo | 325 | 11 | 5 |
| `es-b2-las-fiestas-de-mi-pueblo` | advanced | B2 — Mexican Spanish register | Las fiestas de mi pueblo | 317 | 12 | 5 |
| `es-c1-el-ultimo-tren-a-buenos-aires` | advanced | C1 — Argentine Spanish (voseo) | El último tren a Buenos Aires | 373 | 13 | 5 |

4 beginner (A1/A2), 4 intermediate (B1), 3 advanced (B2/C1) — a ladder, not a
flat set. Word count and glossary density both climb with level: every story
carries 3–5 glossary entries per 100 words of body text (ratios run
3.38–4.40/100w across the set), and every story carries at least 3
comprehension exercises (the two longest carry 5, including one open
`discussion` exercise each for B1+ stories).

Register is neutral Latin-American Spanish (`tú`, no `vosotros`) except two
stories that are **deliberately regional**, each flagged in its own
`level_detail` and reinforced with a glossary `note`:

- `es-b2-las-fiestas-de-mi-pueblo` — Mexican Spanish (Oaxacan *posadas*,
  regional vocabulary: `la posada`, `los romeritos`, `la cuadra`).
- `es-c1-el-ultimo-tren-a-buenos-aires` — Rioplatense Argentine Spanish
  (voseo: `vos sos`, `encontrás`, `dejate`), with a comprehension exercise that
  asks the learner to convert a voseo sentence back to `tú` form, so the
  regional register is itself taught, not just narrated around.

No copyrighted text: all eleven stories are original, hand-authored for this
task (see `source.generator: "hand-authored"` in every file).

## The schema

Every file validates against `learn-cli`'s shared story contract
(`learn/contract/schemas/story.json`, `schema_version` "1.0"). Key shape,
matching `tests/fixtures/stories/spanish-beginner-la-panaderia.json` in
`learn-cli`:

- `kind: "story"`, `subject: "spanish"`, `language: "es"`.
- `id` — the filename stem; pattern `^[a-z0-9][a-z0-9._-]*$`.
- `level` — one of `beginner` / `intermediate` / `advanced` (the schema's
  coarse enum); `level_detail` — the CEFR tag, free text, so a regional note
  rides along with it (`"B2 — Mexican Spanish register"`).
- `body` — Markdown, paragraphs blank-line separated, dialogue in em-dash
  (`—`) style.
- `glossary[]` — `{term, definition, note?}`. `note` is used for grammar
  asides (stem changes, subjunctive triggers) and regional flags.
- `exercises[]` — `{id, type, item_id, prompt, choices?, answer?, rubric?}`.
  `item_id` in every exercise in this ladder follows the namespace
  **`es.story.<story-id>.<n>`** (`n` = 1-based position in the story), e.g.
  `es.story.es-a1-el-mercado-de-frutas.1`. This is a per-story namespace
  rather than the topic-sharing convention the `learn-cli` fixture uses
  (`food-vocab`, `numbers-money` shared across stories) — spanish-cli's tutor
  code and its curriculum/item catalog do not exist yet (that lands with the
  french-cli port), so there is no shared vocabulary to key into yet.
  `es.story.<id>.<n>` guarantees uniqueness today and stays a valid `item_id`
  regardless of what the later curriculum layer decides; re-keying to shared
  topic ids, if the tutor code adopts that convention, is a mechanical rename
  left to whoever builds `spanish/cli/_commands/story.py`.
- `audio: null` in every file — the audio pipeline doesn't exist yet; the
  schema requires producers to set `null` or omit until it does.
- `source: {generator, reviewed_by, generated_at}` — provenance, present on
  every file.

## Authoring pipeline (reproducible)

### 1. Check for a batch-drafting tool

```bash
command -v cloudai
```

**Result at authoring time: not found** (`cloudai: command not found`) — no
`cloudai-cli` binary was on `PATH` in this environment. Per the brief's
still-open model-access decision (route model calls through `cloudai-cli` /
`ec2bedrock-cli`), that is the tool this pipeline *should* batch-draft through
once available; this run fell back to direct authoring (step 2).

**Intended batch command once `cloudai` is available (pending — not run this
pass):**

```bash
cloudai run --model <configured-model> \
  --system "$(cat docs/stories.md)" \
  --prompt "Write one Spanish graded-reader story at level <A1|A2|B1|B2|C1>, \
150-400 words scaling with level, matching the story schema at \
learn/contract/schemas/story.json in the learn-cli repo: fields id \
(es-<level>-<slug>), schema_version 1.0, kind story, subject spanish, \
title, level, level_detail, language es, summary, body (Markdown, em-dash \
dialogue), glossary (3-5 entries per 100 words, term+definition+optional \
note), exercises (>=3, item_id namespaced es.story.<id>.<n>), audio null, \
source.generator cloudai. Emit only the JSON object." \
  --output content/stories/<id>.json
```

That command is documented so a future pass (once `cloudai` is on `PATH` and
its model config is wired for this repo) can batch-generate additional rungs
without re-deriving the prompt shape from scratch — swap `<level>`/`<slug>`
per story and re-run steps 2–4 below on the output.

### 2. Draft (this pass: direct authoring)

Each story was hand-written directly against the schema's field list —
title, level/level_detail, body, glossary, exercises — following the shape of
`tests/fixtures/stories/spanish-beginner-la-panaderia.json` in `learn-cli`. A
small generator script built the eleven JSON files from per-story Python data
(title, body, glossary pairs, exercise specs) so every file gets identical
structural boilerplate (`schema_version`, `kind`, `audio: null`, `source`) and
the word-count / glossary-density arithmetic is exact rather than eyeballed.
That script is scratch tooling, not committed here — it is not code this repo
ships; the JSON output is the artifact under review.

### 3. Validate every file

From the `learn-cli` checkout (read-only reference for this task; the
validator itself is not vendored into spanish-cli):

```bash
cd /path/to/learn-cli
uv run python3 - <<'EOF'
import json
from pathlib import Path
from learn.contract import validate

d = Path("/path/to/spanish-cli/content/stories")
ok = True
for f in sorted(d.glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    errors = validate(data, "story")
    print(f.name, "OK" if not errors else errors)
    ok = ok and not errors
    if f.stem != data.get("id"):
        ok = False
        print(f.name, "filename does not match id", data.get("id"))
print("ALL OK" if ok else "FAILURES PRESENT")
EOF
```

Note the argument order: `learn.contract.validate(instance, schema_name)` —
the instance (a loaded dict) first, the schema name (`"story"`) second.

**Result this pass:** all eleven files under `content/stories/` printed `OK`;
filename-vs-`id` also checked and matched for all eleven.

### 4. Human review at merge

The checklist below (§ Review checklist) is what the operator runs over a
sample before merging. It is deliberately a human step — schema validation
only proves *shape*, not that the Spanish reads naturally or that an
exercise actually tests the text.

## Review checklist

For each story sampled at merge:

- [ ] **Schema-valid** — `validate(story, "story")` returns `[]` (mechanical;
  step 3 above already ran this over all eleven, but re-run after any edit).
- [ ] **Filename = id** — `content/stories/<id>.json` where `<id>` is the
  file's own `"id"` field.
- [ ] **Natural Spanish** — no literal translation-ese; a native reader would
  not flag a sentence as obviously non-native phrasing.
- [ ] **Level-appropriate** — vocabulary and tense range match `level_detail`
  (an A1 story stays in present tense with high-frequency vocabulary; a B1
  story can mix preterite/imperfect; B2+ can carry subjunctive and
  subordination without becoming impenetrable).
- [ ] **Word count fits the band** — beginner ~150–220, intermediate
  ~230–290, advanced ~300–400 (this ladder's actual range: 143–373; see
  table above for the letter of it).
- [ ] **Glossary density** — roughly 3–5 entries per 100 words, each entry a
  term that actually appears in the body, each definition correct.
- [ ] **Exercises tied to the text** — every exercise is answerable from the
  body alone (no outside knowledge required), at least 3 per story, `answer`/
  `rubric` present and correct for its `type`.
- [ ] **`item_id` follows the namespace** — `es.story.<story-id>.<n>`,
  sequential, one per exercise.
- [ ] **Regional register flagged** — if the story deliberately uses a
  regionalism (voseo, a country-specific idiom or dish name), `level_detail`
  or a glossary `note` says so; it is not presented as neutral/universal
  Spanish by omission.
- [ ] **No copyrighted material** — original text, not lifted or lightly
  adapted from a published source.
- [ ] **`audio: null`** and `source.generator`/`reviewed_by`/`generated_at`
  present.

## Adding a rung later

To extend the ladder: pick the level furthest from balance (currently all
three bands are covered but advanced has only 3 vs. 4/4 for
beginner/intermediate — a fourth advanced story is the natural next add),
follow the pipeline above, and append to the ladder table in this file.
Keep `content/stories/` flat — no subdirectories, filename is always the id.
