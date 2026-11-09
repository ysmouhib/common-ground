"""Finite structures and an independent evaluator.

Whenever a solver claims that a set of sentences is satisfiable, the claim is turned
into an explicit finite structure and re-checked here by plain recursion over the
syntax tree. This file imports no solver: it is the second opinion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from .fol import (And, BINARY, Const, Eq, Exists, Fn, Forall, Formula, Iff, Implies, Not, Or, Pred, Term,
                  Var, Xor)


@dataclass
class Structure:
    """A finite first-order structure with domain ``range(size)``."""

    size: int
    constants: dict[str, int] = field(default_factory=dict)
    predicates: dict[tuple[str, int], set[tuple[int, ...]]] = field(default_factory=dict)
    functions: dict[tuple[str, int], dict[tuple[int, ...], int]] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "size": self.size,
            "constants": dict(sorted(self.constants.items())),
            "predicates": {f"{n}/{a}": sorted(map(list, rows)) for (n, a), rows in sorted(self.predicates.items())},
            "functions": {f"{n}/{a}": sorted([list(k), v] for k, v in table.items())
                          for (n, a), table in sorted(self.functions.items())},
        }


class EvaluationError(ValueError):
    """The structure does not interpret a symbol the formula uses."""


def eval_term(t: Term, s: Structure, env: dict[str, int]) -> int:
    if isinstance(t, Var):
        if t.name not in env:
            raise EvaluationError(f"free variable {t.name!r}")
        return env[t.name]
    if isinstance(t, Const):
        if t.name not in s.constants:
            raise EvaluationError(f"constant {t.name!r} has no interpretation")
        return s.constants[t.name]
    key = (t.name, len(t.args))
    args = tuple(eval_term(a, s, env) for a in t.args)
    try:
        return s.functions[key][args]
    except KeyError:
        raise EvaluationError(f"function {t.name}/{len(t.args)} is undefined at {args}") from None


def holds(f: Formula, s: Structure, env: dict[str, int] | None = None) -> bool:
    """Truth of ``f`` in ``s`` under the variable assignment ``env`` (Tarski semantics)."""
    env = env or {}
    if isinstance(f, Pred):
        return tuple(eval_term(a, s, env) for a in f.args) in s.predicates.get((f.name, len(f.args)), ())
    if isinstance(f, Eq):
        return eval_term(f.left, s, env) == eval_term(f.right, s, env)
    if isinstance(f, Not):
        return not holds(f.body, s, env)
    if isinstance(f, And):
        return holds(f.left, s, env) and holds(f.right, s, env)
    if isinstance(f, Or):
        return holds(f.left, s, env) or holds(f.right, s, env)
    if isinstance(f, Implies):
        return (not holds(f.left, s, env)) or holds(f.right, s, env)
    if isinstance(f, Iff):
        return holds(f.left, s, env) == holds(f.right, s, env)
    if isinstance(f, Xor):
        return holds(f.left, s, env) != holds(f.right, s, env)
    if isinstance(f, Forall):
        return all(holds(f.body, s, {**env, f.var: d}) for d in range(s.size))
    if isinstance(f, Exists):
        return any(holds(f.body, s, {**env, f.var: d}) for d in range(s.size))
    raise TypeError(f"not a formula: {f!r}")


def all_structures(size: int, constants: list[str], predicates: list[tuple[str, int]]):
    """Every structure of the given size over a (small) relational signature. For tests."""
    tuples_by_pred = [list(product(range(size), repeat=a)) for _, a in predicates]
    const_choices = product(range(size), repeat=len(constants))
    for consts in const_choices:
        for bits in product(*[range(2 ** len(t)) for t in tuples_by_pred]):
            preds = {}
            for (name, arity), tuples, mask in zip(predicates, tuples_by_pred, bits):
                preds[(name, arity)] = {t for i, t in enumerate(tuples) if mask >> i & 1}
            yield Structure(size, dict(zip(constants, consts)), preds)


__all__ = ["Structure", "EvaluationError", "holds", "eval_term", "all_structures", "BINARY"]
