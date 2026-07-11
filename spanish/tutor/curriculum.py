"""The committed Spanish curriculum — modules, lessons, items, exercises.

This is the *content* half of the LLM-free tutor engine (the other half is
per-learner state). It is Spanish-specific data only: the surrounding engine,
state, and CLI never hard-code course content, so a sibling language tutor swaps
this module (plus :mod:`spanish.tutor.subject` and ``content/stories/``) and
inherits the whole contract implementation unchanged.

Shape (mirrors culture-guide's proven ``curriculum`` layout — structured Python
data, path-addressable):

* a course is an ordered tuple of :class:`Module` (the web face renders one
  sub-page per module);
* each module holds ordered :class:`Lesson` groups; each lesson holds ordered
  :class:`Item` (curriculum items — the join key across lessons, practice,
  stories, ``record``, and ``progress.mastery``);
* each item carries the teachable ``points`` a driver must explain and check,
  plus its practice :class:`Exercise` batch.

Item ids are namespaced ``es.<area>.<topic>`` and match the contract id pattern
``^[a-z0-9][a-z0-9._-]*$``.
"""

from __future__ import annotations

from typing import NamedTuple


class Exercise(NamedTuple):
    """One checkable/gradable exercise (same shape as the contract exercise)."""

    id: str
    type: str  # multiple_choice|true_false|cloze|short_answer|translation|open|discussion
    item_id: str
    prompt: str
    choices: tuple[str, ...] = ()
    answer: str = ""
    rubric: str = ""


class Item(NamedTuple):
    """One curriculum item: a stable id, a label, teachable points, exercises."""

    id: str
    label: str
    points: tuple[str, ...]
    exercises: tuple[Exercise, ...]
    body: str = ""


class Lesson(NamedTuple):
    """An ordered group of items taught together as one lesson directive."""

    id: str
    title: str
    objectives: tuple[str, ...]
    items: tuple[Item, ...]


class Module(NamedTuple):
    """A course module. ``level`` is the coarse contract rung; CEFR lives in stories."""

    id: str
    title: str
    summary: str
    level: str  # beginner|intermediate|advanced
    lessons: tuple[Lesson, ...]


# ---------------------------------------------------------------------------
# Module 1 — Primeros pasos (beginner / A1)
# ---------------------------------------------------------------------------
_M1 = Module(
    id="primeros-pasos",
    title="Primeros pasos",
    summary="Saludos, presentaciones, números y precios — lo esencial para sobrevivir.",
    level="beginner",
    lessons=(
        Lesson(
            id="l.saludos",
            title="Saludos y presentaciones",
            objectives=(
                "Saludar y despedirse en el momento adecuado del día.",
                "Presentarte y preguntar el nombre de alguien.",
            ),
            items=(
                Item(
                    id="es.saludos.hola",
                    label="Saludos y cortesía",
                    points=(
                        "Hola sirve a cualquier hora; buenos días se usa por la mañana, "
                        "buenas tardes después del mediodía y buenas noches por la noche.",
                        "Fórmulas de cortesía: por favor, gracias, de nada, perdón.",
                        "« ¿Cómo estás? » pregunta cómo te encuentras; se responde "
                        "« Estoy bien » o « Más o menos ».",
                    ),
                    exercises=(
                        Exercise(
                            id="hola-1",
                            type="translation",
                            item_id="es.saludos.hola",
                            prompt="Di en español: 'Hola, ¿cómo estás?'",
                            answer="Hola, ¿cómo estás?",
                        ),
                        Exercise(
                            id="hola-2",
                            type="multiple_choice",
                            item_id="es.saludos.hola",
                            prompt="¿Qué saludo es apropiado por la noche?",
                            choices=("Buenos días", "Buenas noches", "Buenas tardes"),
                            answer="Buenas noches",
                        ),
                    ),
                ),
                Item(
                    id="es.saludos.presentaciones",
                    label="Presentarte",
                    points=(
                        "« Me llamo ... » da tu nombre; « ¿Cómo te llamas? » lo pregunta.",
                        "« Mucho gusto » = encantado de conocerte; también se dice "
                        "« Encantado/a », concordando el género.",
                        "« Soy ... » + origen/profesión: soy inglés, soy estudiante.",
                    ),
                    exercises=(
                        Exercise(
                            id="presentaciones-1",
                            type="cloze",
                            item_id="es.saludos.presentaciones",
                            prompt="« ¿Cómo te ___? » — « Me llamo Clara. »",
                            answer="llamas",
                        ),
                        Exercise(
                            id="presentaciones-2",
                            type="open",
                            item_id="es.saludos.presentaciones",
                            prompt="Preséntate en tres frases cortas en español (nombre, "
                            "origen, un detalle más).",
                            rubric="Aprueba con un « me llamo » bien formado más "
                            "« soy »/« vengo de »; si una frase está mal formada, es "
                            "parcial.",
                        ),
                    ),
                ),
            ),
        ),
        Lesson(
            id="l.numeros",
            title="Números y precios",
            objectives=(
                "Contar en voz alta del 0 al 20.",
                "Pedir y entender precios en euros o pesos.",
            ),
            items=(
                Item(
                    id="es.numeros.contar",
                    label="Contar del 0 al 20",
                    points=(
                        "Del 0 al 15 son palabras individuales; a partir del 16 se "
                        "combinan: dieciséis, diecisiete, veinte.",
                        "Aprende del 0 al 20 de oído primero — reaparecen en precios, "
                        "horas y fechas.",
                        "Cuidado con la ortografía: dieciséis lleva tilde, a diferencia "
                        "de diecisiete.",
                    ),
                    exercises=(
                        Exercise(
                            id="contar-1",
                            type="translation",
                            item_id="es.numeros.contar",
                            prompt="Cuenta en voz alta del 11 al 15 en español.",
                            answer="once, doce, trece, catorce, quince",
                        ),
                        Exercise(
                            id="contar-2",
                            type="multiple_choice",
                            item_id="es.numeros.contar",
                            prompt="¿Qué número es « catorce »?",
                            choices=("12", "14", "40"),
                            answer="14",
                        ),
                    ),
                ),
                Item(
                    id="es.numeros.precios",
                    label="Precios",
                    points=(
                        "« ¿Cuánto cuesta? » y « ¿Cuánto es? » preguntan el precio.",
                        "Los precios se leen 'X con Y': cuatro con cincuenta — nunca "
                        "'cuatro y cincuenta' en un precio.",
                        "Redondea con cortesía: « Son diez pesos. » — « Aquí tiene, " "gracias. »",
                    ),
                    exercises=(
                        Exercise(
                            id="precios-1",
                            type="translation",
                            item_id="es.numeros.precios",
                            prompt="Di en español: 'Son siete con cincuenta.'",
                            answer="Son siete con cincuenta.",
                        ),
                        Exercise(
                            id="precios-2",
                            type="cloze",
                            item_id="es.numeros.precios",
                            prompt="« ¿___ cuesta? » — « Dos euros, señora. »",
                            answer="Cuánto",
                        ),
                    ),
                ),
            ),
        ),
    ),
)

# ---------------------------------------------------------------------------
# Module 2 — La vida cotidiana (intermediate / A2)
# ---------------------------------------------------------------------------
_M2 = Module(
    id="la-vida-cotidiana",
    title="La vida cotidiana",
    summary="Comida y el mercado, pedir en un café, y verbos de la rutina diaria.",
    level="intermediate",
    lessons=(
        Lesson(
            id="l.comida",
            title="En el mercado y en el café",
            objectives=(
                "Nombrar alimentos comunes y comprarlos por cantidad.",
                "Pedir con cortesía en un café y solicitar la cuenta.",
            ),
            items=(
                Item(
                    id="es.comida.mercado",
                    label="Vocabulario del mercado",
                    points=(
                        "Alimentos básicos: el pan, el queso, las manzanas, los "
                        "tomates, la leche.",
                        "Las cantidades usan de: un kilo de manzanas, una docena de "
                        "huevos, una rebanada de queso.",
                        "En el mercado se saluda siempre antes de pedir: « Buenos "
                        "días, ¿tiene manzanas frescas? »",
                    ),
                    exercises=(
                        Exercise(
                            id="mercado-1",
                            type="multiple_choice",
                            item_id="es.comida.mercado",
                            prompt="¿Cómo se dice 'goat cheese' en español?",
                            choices=(
                                "el queso de cabra",
                                "el pan integral",
                                "la papa",
                            ),
                            answer="el queso de cabra",
                        ),
                        Exercise(
                            id="mercado-2",
                            type="cloze",
                            item_id="es.comida.mercado",
                            prompt="Clara compra un ___ de manzanas.",
                            answer="kilo",
                        ),
                    ),
                ),
                Item(
                    id="es.comida.pedir",
                    label="Pedir en un café",
                    points=(
                        "« Quisiera ..., por favor » es la fórmula cortés para pedir.",
                        "« Un café » suele ser espresso; « un café con leche » lleva " "leche.",
                        "« La cuenta, por favor » pide la cuenta.",
                    ),
                    exercises=(
                        Exercise(
                            id="pedir-1",
                            type="translation",
                            item_id="es.comida.pedir",
                            prompt="Pide con cortesía: 'Quisiera un café y un "
                            "croissant, por favor.'",
                            answer="Quisiera un café y un croissant, por favor.",
                        ),
                        Exercise(
                            id="pedir-2",
                            type="open",
                            item_id="es.comida.pedir",
                            prompt="Representa un diálogo pidiendo dos cosas en un "
                            "café y solicitando la cuenta.",
                            rubric="Aprueba con un pedido cortés con « quisiera » "
                            "más « la cuenta »; si falta la cuenta, es parcial.",
                        ),
                    ),
                ),
            ),
        ),
        Lesson(
            id="l.rutina",
            title="El día a día",
            objectives=(
                "Describir una rutina diaria con verbos reflexivos.",
                "Decir con qué frecuencia haces las cosas.",
            ),
            items=(
                Item(
                    id="es.rutina.dia",
                    label="Verbos de la rutina diaria",
                    points=(
                        "Reflexivos: me levanto, me lavo, me visto.",
                        "Momentos del día: por la mañana, por la tarde, por la noche.",
                        "Frecuencia: todos los días, a menudo, a veces, nunca.",
                    ),
                    exercises=(
                        Exercise(
                            id="dia-1",
                            type="cloze",
                            item_id="es.rutina.dia",
                            prompt="Por la mañana, ___ levanto a las siete.",
                            answer="me",
                        ),
                        Exercise(
                            id="dia-2",
                            type="short_answer",
                            item_id="es.rutina.dia",
                            prompt="Describe tu mañana en dos frases.",
                            rubric="Aprueba con dos frases bien formadas con verbos "
                            "reflexivos; una frase es parcial.",
                        ),
                    ),
                ),
            ),
        ),
    ),
)

# ---------------------------------------------------------------------------
# Module 3 — En la ciudad (advanced rung of this ladder / A2)
# ---------------------------------------------------------------------------
_M3 = Module(
    id="en-la-ciudad",
    title="En la ciudad",
    summary="Moverse por la ciudad: pedir direcciones y usar el transporte público.",
    level="advanced",
    lessons=(
        Lesson(
            id="l.direcciones",
            title="Pedir direcciones y usar el transporte",
            objectives=(
                "Pedir y seguir direcciones sencillas.",
                "Comprar un billete y usar el transporte público.",
            ),
            items=(
                Item(
                    id="es.ciudad.direcciones",
                    label="Pedir direcciones",
                    points=(
                        "« Perdón, ¿dónde está ...? » / « Busco la estación. »",
                        "Direcciones: todo recto, a la izquierda, a la derecha, "
                        "hasta la esquina.",
                        "« ¿Está lejos? » — « No, está a cinco minutos a pie. »",
                    ),
                    exercises=(
                        Exercise(
                            id="direcciones-1",
                            type="translation",
                            item_id="es.ciudad.direcciones",
                            prompt="Pregunta con cortesía: 'Perdón, ¿dónde está la " "estación?'",
                            answer="Perdón, ¿dónde está la estación?",
                        ),
                        Exercise(
                            id="direcciones-2",
                            type="multiple_choice",
                            item_id="es.ciudad.direcciones",
                            prompt="'Gire a la izquierda' se dice:",
                            choices=("todo recto", "a la izquierda", "a la derecha"),
                            answer="a la izquierda",
                        ),
                    ),
                ),
                Item(
                    id="es.ciudad.transporte",
                    label="Transporte público",
                    points=(
                        "Tomar el metro / el autobús / el tren; un billete, un abono.",
                        "« ¿Qué autobús va a ...? » — « El 27 va al centro. »",
                        "« Un billete de ida y vuelta a Barcelona, por favor. »",
                    ),
                    exercises=(
                        Exercise(
                            id="transporte-1",
                            type="cloze",
                            item_id="es.ciudad.transporte",
                            prompt="Tomo el ___ para ir al trabajo.",
                            answer="metro",
                        ),
                        Exercise(
                            id="transporte-2",
                            type="open",
                            item_id="es.ciudad.transporte",
                            prompt="Compra un billete de ida y vuelta a Barcelona y "
                            "pregunta a qué hora sale.",
                            rubric="Aprueba con un pedido cortés de « ida y vuelta » "
                            "más una pregunta de hora (« a qué hora »); si falta uno, "
                            "es parcial.",
                        ),
                    ),
                ),
            ),
        ),
    ),
)

#: The course, in order. The web face renders one sub-page per module.
MODULES: tuple[Module, ...] = (_M1, _M2, _M3)


# ---------------------------------------------------------------------------
# Indices + lookups (built once, module-level)
# ---------------------------------------------------------------------------
def all_lessons() -> tuple[tuple[Module, Lesson], ...]:
    """Every (module, lesson) pair in course order."""
    return tuple((m, lesson) for m in MODULES for lesson in m.lessons)


def all_items() -> tuple[tuple[Module, Lesson, Item], ...]:
    """Every (module, lesson, item) triple in course order."""
    return tuple((m, lesson, item) for m, lesson in all_lessons() for item in lesson.items)


def all_item_ids() -> tuple[str, ...]:
    """Stable item ids in course order (the mastery-map / join keys)."""
    return tuple(item.id for _, _, item in all_items())


def all_exercises() -> tuple[Exercise, ...]:
    """Every practice exercise across the curriculum, in course order."""
    return tuple(ex for _, _, item in all_items() for ex in item.exercises)


_ITEM_INDEX: dict[str, tuple[Module, Lesson, Item]] = {
    item.id: (m, lesson, item) for m, lesson, item in all_items()
}
_LESSON_INDEX: dict[str, tuple[Module, Lesson]] = {
    lesson.id: (m, lesson) for m, lesson in all_lessons()
}
_MODULE_INDEX: dict[str, Module] = {m.id: m for m in MODULES}


def find_item(item_id: str) -> tuple[Module, Lesson, Item] | None:
    return _ITEM_INDEX.get(item_id)


def find_lesson(lesson_id: str) -> tuple[Module, Lesson] | None:
    return _LESSON_INDEX.get(lesson_id)


def find_module(module_id: str) -> Module | None:
    return _MODULE_INDEX.get(module_id)


class LessonTarget(NamedTuple):
    """A resolved lesson-verb target: the module + the lesson to teach."""

    module: Module
    lesson: Lesson


def resolve_lesson_target(token: str) -> LessonTarget:
    """Resolve a lesson token — a lesson id, a module id, or an item id.

    A module id resolves to its first lesson; an item id resolves to the lesson
    that contains it. Raises :class:`KeyError` with the token if nothing matches
    (the CLI turns that into a ``CliError`` listing valid targets).
    """
    needle = token.strip()
    hit = find_lesson(needle)
    if hit is not None:
        return LessonTarget(module=hit[0], lesson=hit[1])
    module = find_module(needle)
    if module is not None:
        return LessonTarget(module=module, lesson=module.lessons[0])
    item_hit = find_item(needle)
    if item_hit is not None:
        return LessonTarget(module=item_hit[0], lesson=item_hit[1])
    raise KeyError(token)


def valid_lesson_targets() -> list[str]:
    """All accepted lesson tokens (module ids + lesson ids), for error hints."""
    return [m.id for m in MODULES] + [lesson.id for _, lesson in all_lessons()]


def exercises_for_scope(scope: str) -> tuple[str, tuple[Exercise, ...]] | None:
    """Resolve a practice ``scope`` to ``(resolved_scope, exercises)``.

    ``scope`` may be an item id (that item's exercises), a module id (all its
    items' exercises), or a lesson id (that lesson's exercises). Returns ``None``
    when nothing matches (the caller raises a ``CliError``).
    """
    item_hit = find_item(scope)
    if item_hit is not None:
        return item_hit[2].id, item_hit[2].exercises
    module = find_module(scope)
    if module is not None:
        exercises = tuple(
            ex for lesson in module.lessons for it in lesson.items for ex in it.exercises
        )
        return module.id, exercises
    lesson_hit = find_lesson(scope)
    if lesson_hit is not None:
        exercises = tuple(ex for it in lesson_hit[1].items for ex in it.exercises)
        return lesson_hit[1].id, exercises
    return None


def counts() -> dict[str, int]:
    """Deterministic content counts for the overview payload."""
    return {
        "modules": len(MODULES),
        "lessons": len(all_lessons()),
        "items": len(all_item_ids()),
        "exercises": len(all_exercises()),
    }
