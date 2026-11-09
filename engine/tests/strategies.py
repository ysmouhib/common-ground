"""Random formulas for property tests."""
from hypothesis import strategies as st

from commonground.fol import (And, Const, Exists, Forall, Iff, Implies, Not, Or, Pred, Var, Xor)

CONSTANTS = ["a", "b"]
UNARY = ["P", "Q"]
BINARY_PREDS = ["R"]
VARS = ["x", "y"]


def atoms(bound: tuple[str, ...]):
    terms = st.sampled_from([Const(c) for c in CONSTANTS] + [Var(v) for v in bound])
    unary = st.builds(lambda p, t: Pred(p, (t,)), st.sampled_from(UNARY), terms)
    binary = st.builds(lambda p, t, u: Pred(p, (t, u)), st.sampled_from(BINARY_PREDS), terms, terms)
    nullary = st.sampled_from([Pred("Z", ())])
    return st.one_of(unary, unary, binary, nullary)


def formulas(depth: int = 3, bound: tuple[str, ...] = (), quantifiers: bool = True):
    if depth == 0:
        return atoms(bound)
    sub = formulas(depth - 1, bound, quantifiers)
    options = [
        atoms(bound),
        st.builds(Not, sub),
        st.builds(And, sub, sub),
        st.builds(Or, sub, sub),
        st.builds(Implies, sub, sub),
        st.builds(Iff, sub, sub),
        st.builds(Xor, sub, sub),
    ]
    if quantifiers:
        for var in VARS:
            inner = formulas(depth - 1, bound + (var,), quantifiers)
            options.append(st.builds(lambda body, v=var: Forall(v, body), inner))
            options.append(st.builds(lambda body, v=var: Exists(v, body), inner))
    return st.one_of(options)


SENTENCES = formulas(3)
GROUND = formulas(3, quantifiers=False)
