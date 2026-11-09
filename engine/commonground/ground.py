"""Finite-model search by grounding to propositional SAT (PySAT).

Given sentences without function symbols or equality, fix a domain of ``n``
elements, expand every quantifier over the domain and hand the result to a CDCL
solver. A satisfying assignment is read back as an explicit structure.

What an answer means:

* SAT at size ``n``: the sentences have a model. The model is returned and can be
  re-checked by ``model.holds``; nothing here needs to be trusted.
* UNSAT at size ``n``: there is no model with at most ``n - k`` elements, where
  ``k`` is the number of constants. That is a bounded result in general. It is a
  proof of unsatisfiability exactly when the sentences are in the
  Bernays-Schönfinkel class (no existential in the scope of a universal, once
  negations are pushed in) and ``n`` is at least ``epr_bound``; see ``epr_bound``.

Why one size suffices and constants can be taken pairwise distinct: without
equality, cloning an element of a model gives another model. So a model with
``m`` elements yields one with ``m + k`` elements in which the ``k`` constants
name different elements.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from pysat.solvers import Solver

from .fol import (And, BINARY, Const, Eq, Exists, Fn, Forall, Formula, Iff, Implies, Not, Or, Pred, QUANT,
                  Var, Xor, signature)
from .model import Structure


class Unsupported(ValueError):
    """The sentences use function symbols or equality, which this grounder does not handle."""


# ----------------------------------------------------------------- negation normal form


def nnf(f: Formula, positive: bool = True) -> Formula:
    """Push negations to the atoms; ↔ and ⊕ are expanded. The result uses ∧ ∨ ¬atom ∀ ∃ only."""
    if isinstance(f, (Pred, Eq)):
        return f if positive else Not(f)
    if isinstance(f, Not):
        return nnf(f.body, not positive)
    if isinstance(f, And):
        a, b = nnf(f.left, positive), nnf(f.right, positive)
        return And(a, b) if positive else Or(a, b)
    if isinstance(f, Or):
        a, b = nnf(f.left, positive), nnf(f.right, positive)
        return Or(a, b) if positive else And(a, b)
    if isinstance(f, Implies):
        a, b = nnf(f.left, not positive), nnf(f.right, positive)
        return Or(a, b) if positive else And(a, b)
    if isinstance(f, (Iff, Xor)):
        same = isinstance(f, Iff) == positive  # asserting "left and right agree"?
        l_pos, l_neg = nnf(f.left, True), nnf(f.left, False)
        r_pos, r_neg = nnf(f.right, True), nnf(f.right, False)
        if same:
            return And(Or(l_neg, r_pos), Or(l_pos, r_neg))
        return And(Or(l_pos, r_pos), Or(l_neg, r_neg))
    if isinstance(f, Forall):
        body = nnf(f.body, positive)
        return Forall(f.var, body) if positive else Exists(f.var, body)
    if isinstance(f, Exists):
        body = nnf(f.body, positive)
        return Exists(f.var, body) if positive else Forall(f.var, body)
    raise TypeError(f"not a formula: {f!r}")


def _exists_profile(f: Formula, under_forall: bool) -> tuple[int, bool]:
    """(number of existential quantifiers outside every universal, any existential inside a universal?)."""
    if isinstance(f, (Pred, Eq, Not)):
        return 0, False
    if isinstance(f, (And, Or)):
        n1, b1 = _exists_profile(f.left, under_forall)
        n2, b2 = _exists_profile(f.right, under_forall)
        return n1 + n2, b1 or b2
    if isinstance(f, Forall):
        return _exists_profile(f.body, True)
    if isinstance(f, Exists):
        n, b = _exists_profile(f.body, under_forall)
        return (n, True) if under_forall else (n + 1, b)
    raise TypeError(f"not in negation normal form: {f!r}")


def epr_bound(sentences: list[Formula]) -> int | None:
    """Domain size at which grounding decides satisfiability, or None outside the class.

    For sentences whose negation normal form has no existential under a universal
    (and no functions or equality), each outer existential can be replaced by a fresh
    constant; the result is universal, so it has a model iff it has one whose elements
    are exactly the named ones. Hence the bound: constants + outer existentials, at
    least 1.
    """
    sig = signature(sentences)
    if sig.functions or sig.uses_equality:
        return None
    total = 0
    for s in sentences:
        n, nested = _exists_profile(nnf(s), False)
        if nested:
            return None
        total += n
    return max(1, len(sig.constants) + total)


# ---------------------------------------------------------------------------- grounding


class _Encoder:
    """Tseitin encoding of ground formulas over a fixed domain."""

    def __init__(self, size: int, constants: dict[str, int]):
        self.size = size
        self.constants = constants
        self.atom_var: dict[tuple, int] = {}
        self.cache: dict[tuple, int] = {}
        self.clauses: list[list[int]] = []
        self.next = 0
        self.true = self._fresh()
        self.clauses.append([self.true])

    def _fresh(self) -> int:
        self.next += 1
        return self.next

    def atom(self, name: str, args: tuple[int, ...]) -> int:
        key = (name, args)
        if key not in self.atom_var:
            self.atom_var[key] = self._fresh()
        return self.atom_var[key]

    def _and(self, lits: list[int]) -> int:
        lits = sorted(set(lits))
        if any(-x in lits for x in lits):
            return -self.true
        lits = [x for x in lits if x != self.true]
        if -self.true in lits:
            return -self.true
        if not lits:
            return self.true
        if len(lits) == 1:
            return lits[0]
        key = ("and", tuple(lits))
        if key not in self.cache:
            v = self._fresh()
            for x in lits:
                self.clauses.append([-v, x])
            self.clauses.append([v] + [-x for x in lits])
            self.cache[key] = v
        return self.cache[key]

    def _or(self, lits: list[int]) -> int:
        return -self._and([-x for x in lits])

    def lit(self, f: Formula, env: dict[str, int]) -> int:
        """Literal equivalent to the NNF formula ``f`` under ``env``."""
        if isinstance(f, Pred):
            return self.atom(f.name, tuple(self._term(a, env) for a in f.args))
        if isinstance(f, Not):
            return -self.lit(f.body, env)
        if isinstance(f, And):
            return self._and([self.lit(f.left, env), self.lit(f.right, env)])
        if isinstance(f, Or):
            return self._or([self.lit(f.left, env), self.lit(f.right, env)])
        if isinstance(f, Forall):
            return self._and([self.lit(f.body, {**env, f.var: d}) for d in range(self.size)])
        if isinstance(f, Exists):
            return self._or([self.lit(f.body, {**env, f.var: d}) for d in range(self.size)])
        raise Unsupported(f"cannot ground {type(f).__name__}")

    def _term(self, t, env: dict[str, int]) -> int:
        if isinstance(t, Var):
            return env[t.name]
        if isinstance(t, Const):
            return self.constants[t.name]
        raise Unsupported("function symbols are not supported by the grounder")


@dataclass
class GroundProblem:
    """Sentences grounded over one domain, each guarded by its own selector literal."""

    size: int
    constants: dict[str, int]
    predicates: tuple[tuple[str, int], ...]
    selectors: list[int]
    encoder: _Encoder

    def solver(self) -> Solver:
        return Solver(name="glucose4", bootstrap_with=self.encoder.clauses)

    def structure(self, model: list[int]) -> Structure:
        true = {v for v in model if v > 0}
        preds: dict[tuple[str, int], set[tuple[int, ...]]] = {p: set() for p in self.predicates}
        for (name, args), var in self.encoder.atom_var.items():
            if var in true:
                preds[(name, len(args))].add(args)
        return Structure(self.size, dict(self.constants), preds)


def ground(sentences: list[Formula], size: int) -> GroundProblem:
    """Ground ``sentences`` over ``range(size)``; sentence ``i`` holds iff ``selectors[i]`` is true."""
    sig = signature(sentences)
    if sig.functions or sig.uses_equality:
        raise Unsupported("function symbols and equality are not supported by the grounder")
    if size < max(1, len(sig.constants)):
        raise ValueError("domain smaller than the number of constants")
    constants = {name: i for i, name in enumerate(sig.constants)}
    enc = _Encoder(size, constants)
    selectors = [enc.lit(nnf(s), {}) for s in sentences]
    return GroundProblem(size, constants, sig.predicates, selectors, enc)


@dataclass
class GroundResult:
    satisfiable: bool
    structure: Structure | None
    size: int
    complete: bool  # True when an UNSAT answer is a proof (Bernays-Schönfinkel, size >= bound)


def default_size(sentences: list[Formula], extra: int = 3, cap: int = 12) -> int:
    """The decision bound when there is one, otherwise ``constants + extra`` (bounded search)."""
    bound = epr_bound(sentences)
    if bound is not None:
        return bound
    return min(cap, max(1, len(signature(sentences).constants)) + extra)


def find_model(sentences: list[Formula], size: int | None = None) -> GroundResult:
    """Search for a model of all ``sentences`` with exactly ``size`` elements."""
    bound = epr_bound(sentences)
    n = size if size is not None else default_size(sentences)
    problem = ground(sentences, n)
    with problem.solver() as solver:
        if solver.solve(assumptions=problem.selectors):
            return GroundResult(True, problem.structure(solver.get_model()), n, True)
    return GroundResult(False, None, n, bound is not None and n >= bound)


__all__ = ["Unsupported", "nnf", "epr_bound", "ground", "find_model", "default_size", "GroundProblem",
           "GroundResult", "BINARY", "QUANT", "product", "Fn", "Eq"]
