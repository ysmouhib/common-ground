"""Does a conclusion follow from premises? A three-way verdict with evidence.

    True       the premises entail the conclusion        (premises ∧ ¬conclusion has no model)
    False      the premises entail its negation          (premises ∧ conclusion has no model)
    Uncertain  neither: one model makes it true, another makes it false

Two further outcomes are reported instead of being forced into those three:
``Inconsistent`` (the premises themselves have no model, so everything "follows")
and ``Undecided`` (no engine settled the question within its limits).

Evidence and what it is worth:

* A "has a model" claim always carries an explicit finite structure that was
  re-checked by ``model.holds``. It does not depend on trusting a solver.
* A "has no model" claim is a refutation by Z3, or by grounding when the sentences
  are in the decidable Bernays-Schönfinkel class. ``lean.py`` can additionally
  have the Lean kernel check a proof of the same statement.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ground, smt
from .fol import Formula, Not
from .model import EvaluationError, Structure, holds

LABELS = ("True", "False", "Uncertain", "Inconsistent", "Undecided")


@dataclass
class SatAnswer:
    status: str  # "sat" | "unsat" | "unknown"
    structure: Structure | None = None
    engine: str = ""
    note: str = ""


def _verified(sentences: list[Formula], structure: Structure | None) -> bool:
    if structure is None:
        return False
    try:
        return all(holds(s, structure) for s in sentences)
    except EvaluationError:
        return False


def _by_grounding(sentences: list[Formula]) -> SatAnswer:
    try:
        result = ground.find_model(sentences)
    except ground.Unsupported as exc:
        return SatAnswer("unknown", note=str(exc))
    if result.satisfiable:
        if _verified(sentences, result.structure):
            return SatAnswer("sat", result.structure, "grounding")
        return SatAnswer("unknown", note="grounder returned a structure that failed re-checking")
    if result.complete:
        return SatAnswer("unsat", engine="grounding (decision procedure for this class)")
    return SatAnswer("unknown", note=f"no model with domain size {result.size}; not a proof for this class")


def satisfiable(sentences: list[Formula], timeout_ms: int = 5000, engine: str = "auto") -> SatAnswer:
    """Satisfiability with a checked witness. ``engine`` is "auto", "z3" or "grounding"."""
    if engine == "grounding":
        return _by_grounding(sentences)
    z = smt.check(sentences, timeout_ms)
    if z.status == "unsat":
        return SatAnswer("unsat", engine="z3")
    if z.status == "sat" and _verified(sentences, z.structure):
        return SatAnswer("sat", z.structure, "z3")
    if engine == "z3":
        note = "z3 reported sat without a checkable finite model" if z.status == "sat" else z.reason
        return SatAnswer("unknown", note=note)
    # Z3 timed out, or its model could not be read as a finite structure: try grounding.
    fallback = _by_grounding(sentences)
    if fallback.status != "unknown":
        return fallback
    return SatAnswer("unknown", note=f"z3: {z.status} {z.reason}; grounding: {fallback.note}".strip())


@dataclass
class Verdict:
    label: str
    premises_consistent: bool | None
    # structures that witness "the conclusion can be true" / "the conclusion can be false"
    model_true: Structure | None = None
    model_false: Structure | None = None
    engines: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "label": self.label,
            "premises_consistent": self.premises_consistent,
            "model_where_conclusion_holds": self.model_true.to_json() if self.model_true else None,
            "model_where_conclusion_fails": self.model_false.to_json() if self.model_false else None,
            "engines": self.engines,
            "notes": self.notes,
        }


def decide(premises: list[Formula], conclusion: Formula, timeout_ms: int = 5000, engine: str = "auto") -> Verdict:
    can_fail = satisfiable(premises + [Not(conclusion)], timeout_ms, engine)
    can_hold = satisfiable(premises + [conclusion], timeout_ms, engine)
    engines = {"conclusion_can_fail": can_fail.engine, "conclusion_can_hold": can_hold.engine}
    notes = [n for n in (can_fail.note, can_hold.note) if n]
    pair = (can_fail.status, can_hold.status)
    if pair == ("sat", "sat"):
        return Verdict("Uncertain", True, can_hold.structure, can_fail.structure, engines, notes)
    if pair == ("unsat", "sat"):
        return Verdict("True", True, can_hold.structure, None, engines, notes)
    if pair == ("sat", "unsat"):
        return Verdict("False", True, None, can_fail.structure, engines, notes)
    if pair == ("unsat", "unsat"):
        return Verdict("Inconsistent", False, None, None, engines, notes)
    # At least one side is unknown. A one-sided answer is still reported in the notes.
    consistent = True if "sat" in pair else None
    return Verdict("Undecided", consistent, can_hold.structure, can_fail.structure, engines,
                   notes + [f"conclusion_can_fail={can_fail.status}, conclusion_can_hold={can_hold.status}"])
