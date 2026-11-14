"""Load: which axioms of a selected system are load-bearing.

load(a) = |{ e in E⁺ : every minimal premise set for e inside A contains a }|
(RESEARCH.md §2.4). Computed two ways and cross-checked in the tests:
`load_vector` directly as certified removal checks (A without a entails no longer
e — |A|·|E⁺| entailment calls, no enumeration), and `justifications_load` through
`argmap.justifications` (the minimal premise sets themselves). Every removal check
is a real entailment check, solver- or kernel-backed. Load is deductive
indispensability inside one selected system — never "centrality" (THEORY.md limit 9).
"""

from __future__ import annotations

from . import fol, verdict
from .argmap import justifications
from .fol import Formula


def load_vector(axioms: list[Formula], targets: list[Formula], timeout_ms: int = 5000) -> list[dict]:
    """load(a) = number of targets e with A \\ {a} ⊭ e, each removal a certified check.
    A removal check without a verdict is not a non-entailment and not an entailment: it is
    counted in ``pending``, so ``load`` is then a lower bound, never a silently smaller number."""
    out = []
    for a in axioms:
        rest = [x for x in axioms if fol.to_text(x) != fol.to_text(a)]
        count = 0
        pending = 0
        for e in targets:
            v = verdict.decide(rest, e, timeout_ms)
            if v.label in ("False", "Uncertain"):
                count += 1
            elif v.label == "Undecided":
                pending += 1
        out.append({"axiom": fol.to_text(a), "load": count, "pending": pending})
    return out


def justifications_load(axioms: list[Formula], targets: list[Formula], timeout_ms: int = 5000,
                        limit: int = 2000) -> list[dict]:
    """The same count via argmap.justifications: every minimal premise set for e inside A contains a.
    An undecided subset raises argmap.Undecided there, so ``pending`` is always 0 here."""
    premises = {fol.to_text(a): a for a in axioms}
    out = []
    for a in axioms:
        key = fol.to_text(a)
        count = 0
        for e in targets:
            sets = justifications(premises, e, timeout_ms, limit)
            if sets and all(key in s for s in sets):
                count += 1
        out.append({"axiom": key, "load": count, "pending": 0})
    return out
