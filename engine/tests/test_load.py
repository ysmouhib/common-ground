import pytest

from commonground import fol, load
from commonground.fol import parse

ALL = "∀x (Human(x) → Mortal(x))"
SOC = "Human(socrates)"
PLATO = "Human(plato)"

AXIOMS = [parse(ALL), parse(SOC), parse(PLATO)]
TARGETS = [parse("Mortal(socrates)"), parse("Mortal(plato)"), parse("Human(socrates)"), parse("Human(plato)")]


def test_load_vector_counts_claims_that_need_the_axiom():
    vec = load.load_vector(AXIOMS, TARGETS)
    by_axiom = {v["axiom"]: v["load"] for v in vec}
    # without the general axiom, neither mortality follows: load 2
    assert by_axiom[fol.to_text(parse(ALL))] == 2
    # without Human(socrates), Mortal(socrates) and Human(socrates) fail: load 2
    assert by_axiom[fol.to_text(parse(SOC))] == 2
    assert by_axiom[fol.to_text(parse(PLATO))] == 2


def test_load_via_justifications_matches_removal_checks():
    a = load.load_vector(AXIOMS, TARGETS)
    b = load.justifications_load(AXIOMS, TARGETS)
    assert a == b


def test_load_zero_for_a_redundant_axiom():
    axioms = AXIOMS + [parse("Mortal(socrates)")]
    vec = load.load_vector(axioms, TARGETS)
    by_axiom = {v["axiom"]: v["load"] for v in vec}
    assert by_axiom[fol.to_text(parse("Mortal(socrates)"))] == 0


def test_a_removal_check_without_verdict_is_pending_not_load_zero(monkeypatch):
    # the solver (the dependency) gives no verdict on any removal: that is neither "still
    # entailed" nor "no longer entailed", so the count stays a lower bound with its pending tally
    from commonground import verdict
    assert all(v["pending"] == 0 for v in load.load_vector(AXIOMS, TARGETS))
    monkeypatch.setattr(verdict, "decide", lambda *a, **k: verdict.Verdict("Undecided", None, notes=["forced"]))
    vec = load.load_vector(AXIOMS, TARGETS)
    assert all(v["load"] == 0 and v["pending"] == len(TARGETS) for v in vec)
