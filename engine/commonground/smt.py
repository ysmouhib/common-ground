"""Satisfiability of first-order sentences with Z3, with models read back as explicit structures."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import z3

from .fol import (And, Const, Eq, Exists, Fn, Forall, Formula, Iff, Implies, Not, Or, Pred, Term, Var, Xor,
                  signature)
from .model import Structure


@dataclass
class SmtResult:
    status: str  # "sat" | "unsat" | "unknown"
    structure: Structure | None = None
    reason: str = ""


class _Translator:
    def __init__(self, ctx: z3.Context):
        self.ctx = ctx
        self.entity = z3.DeclareSort("Entity", ctx)
        self.decls: dict[tuple[str, str, int], object] = {}

    def const(self, name: str):
        key = ("c", name, 0)
        if key not in self.decls:
            self.decls[key] = z3.Const(f"c:{name}", self.entity)
        return self.decls[key]

    def pred(self, name: str, arity: int):
        key = ("p", name, arity)
        if key not in self.decls:
            if arity == 0:
                self.decls[key] = z3.Bool(f"p:{name}/0", self.ctx)
            else:
                self.decls[key] = z3.Function(f"p:{name}/{arity}", *([self.entity] * arity), z3.BoolSort(self.ctx))
        return self.decls[key]

    def func(self, name: str, arity: int):
        key = ("f", name, arity)
        if key not in self.decls:
            self.decls[key] = z3.Function(f"f:{name}/{arity}", *([self.entity] * (arity + 1)))
        return self.decls[key]

    def term(self, t: Term, env: dict[str, object]):
        if isinstance(t, Var):
            return env[t.name]
        if isinstance(t, Const):
            return self.const(t.name)
        return self.func(t.name, len(t.args))(*[self.term(a, env) for a in t.args])

    def formula(self, f: Formula, env: dict[str, object], depth: int = 0):
        if isinstance(f, Pred):
            p = self.pred(f.name, len(f.args))
            return p if not f.args else p(*[self.term(a, env) for a in f.args])
        if isinstance(f, Eq):
            return self.term(f.left, env) == self.term(f.right, env)
        if isinstance(f, Not):
            return z3.Not(self.formula(f.body, env, depth), self.ctx)
        if isinstance(f, (Forall, Exists)):
            bound = z3.Const(f"v:{f.var}:{depth}", self.entity)
            body = self.formula(f.body, {**env, f.var: bound}, depth + 1)
            return z3.ForAll([bound], body) if isinstance(f, Forall) else z3.Exists([bound], body)
        a, b = self.formula(f.left, env, depth), self.formula(f.right, env, depth)
        if isinstance(f, And):
            return z3.And(a, b)
        if isinstance(f, Or):
            return z3.Or(a, b)
        if isinstance(f, Implies):
            return z3.Implies(a, b)
        if isinstance(f, Iff):
            return a == b
        if isinstance(f, Xor):
            return z3.Xor(a, b)
        raise TypeError(f"not a formula: {f!r}")


def _structure(model: z3.ModelRef, tr: _Translator, sentences: list[Formula], max_size: int) -> Structure | None:
    sig = signature(sentences)
    universe = list(model.get_universe(tr.entity) or [])
    index = {e.sexpr(): i for i, e in enumerate(universe)}

    def element(value) -> int:
        key = value.sexpr()
        if key not in index:
            index[key] = len(universe)
            universe.append(value)
        return index[key]

    constants = {name: element(model.eval(tr.const(name), model_completion=True)) for name in sig.constants}
    if not universe:
        element(model.eval(z3.Const("w:witness", tr.entity), model_completion=True))
    if len(universe) > max_size:
        return None
    predicates: dict[tuple[str, int], set[tuple[int, ...]]] = {}
    for name, arity in sig.predicates:
        p = tr.pred(name, arity)
        rows: set[tuple[int, ...]] = set()
        for combo in product(range(len(universe)), repeat=arity):
            app = p if arity == 0 else p(*[universe[i] for i in combo])
            if z3.is_true(model.eval(app, model_completion=True)):
                rows.add(combo)
        predicates[(name, arity)] = rows
    functions: dict[tuple[str, int], dict[tuple[int, ...], int]] = {}
    for name, arity in sig.functions:
        fn = tr.func(name, arity)
        table = {}
        for combo in product(range(len(universe)), repeat=arity):
            value = model.eval(fn(*[universe[i] for i in combo]), model_completion=True)
            if value.sexpr() not in index:
                return None  # the interpretation leaves the finite universe: not a finite structure we can check
            table[combo] = index[value.sexpr()]
        functions[(name, arity)] = table
    return Structure(len(universe), constants, predicates, functions)


def check(sentences: list[Formula], timeout_ms: int = 5000, max_model_size: int = 40) -> SmtResult:
    """Is the conjunction of ``sentences`` satisfiable? ``unsat`` is a refutation by Z3;
    ``sat`` comes with a finite structure when Z3's model can be read as one."""
    ctx = z3.Context()
    tr = _Translator(ctx)
    solver = z3.Solver(ctx=ctx)
    solver.set("timeout", timeout_ms)
    for s in sentences:
        solver.add(tr.formula(s, {}))
    answer = solver.check()
    if answer == z3.unsat:
        return SmtResult("unsat")
    if answer == z3.sat:
        try:
            return SmtResult("sat", _structure(solver.model(), tr, sentences, max_model_size))
        except z3.Z3Exception as exc:  # model could not be evaluated
            return SmtResult("sat", None, f"model not readable: {exc}")
    return SmtResult("unknown", None, solver.reason_unknown())
