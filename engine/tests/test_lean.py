import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from commonground import lean
from commonground.fol import Not, Pred, Const, parse
from commonground.verdict import decide

from .strategies import SENTENCES

LEAN = lean.find_lean()
needs_lean = pytest.mark.skipif(LEAN is None, reason=f"no Lean {lean.TOOLCHAIN} (set LEAN_BIN)")

HOSTILE = [
    "x := by sorry\n#eval IO.println 1", "p0", "end CG", "«evil»", "a b", "∀", "-- comment", "/- block -/",
    "import Lean", "axiom", "instance", "t_0", "native_decide", "\n#print axioms foo", "🙂", "a.b.c", "'", "h0",
]


@pytest.mark.parametrize("name", HOSTILE)
def test_symbol_names_never_reach_lean(name):
    """Whatever a predicate or constant is called, the Lean text is the same, character for character."""
    def source(symbol):
        premises = [Pred(symbol, (Const(symbol),))]
        return lean.assemble([lean.theorem(0, premises, Pred(symbol, (Const(symbol),)))])

    hostile = source(name)
    lean.assert_generated(hostile)
    assert hostile == source("Harmless")


@given(st.lists(SENTENCES, min_size=1, max_size=3), SENTENCES)
@settings(max_examples=150, deadline=None)
def test_generated_source_stays_inside_the_vocabulary(premises, goal):
    lean.assert_generated(lean.assemble([lean.theorem(7, premises, goal)]))


@pytest.mark.parametrize("text", [
    "#eval IO.println 1", "import Lean", "theorem t : False := by sorry", "axiom a : False",
    "open Lean in run_cmd pure ()", "macro \"x\" : term => `(1)", "initialize foo : Nat ← pure 1",
    "theorem t_0 : False := by native_decide", "unsafe def f := 1", "@[extern \"c\"] def g : Nat := 0",
])
def test_handwritten_lean_is_refused(text):
    with pytest.raises(lean.UnsafeSource):
        lean.assert_generated(lean.HEADER + text + "\n" + lean.FOOTER)


def test_translation_shape():
    theorem = lean.theorem(3, [parse("∀x (P(x) → Q(x))"), parse("P(a)")], parse("Q(a) ⊕ Z"))
    assert theorem.name == "t_3"
    assert "(h0 : (∀ x0 : Entity, ((p0 x0) → (p1 x0))))" in theorem.source
    assert ": (¬ ((p1 c0) ↔ p2)) := by" in theorem.source
    assert theorem.symbols["predicates"] == {"p0": "P/1", "p1": "Q/1", "p2": "Z/0"}
    assert theorem.symbols["constants"] == {"c0": "a"}


def test_nested_binders_get_distinct_names():
    source = lean.theorem(0, [parse("∀x ∃y (R(x, y) ∧ ∀x R(x, y))")], parse("∃x ∃y R(x, y)")).source
    assert "(∀ x0 : Entity, (∃ x1 : Entity, ((p0 x0 x1) ∧ (∀ x2 : Entity, (p0 x2 x1)))))" in source


@needs_lean
def test_true_statements_are_certified_and_false_ones_are_not():
    rule, fact = parse("∀x (P(x) → Q(x))"), parse("P(a)")
    problems = [
        ([rule, fact], parse("Q(a)")),                       # follows
        ([rule, fact], parse("¬Q(a)")),                      # the opposite: must be refused
        ([rule], parse("Q(a)")),                             # does not follow: must be refused
        ([parse("∀x P(x)")], parse("∃x P(x)")),              # needs a non-empty domain
        ([parse("∀x ∃y R(x, y)"), parse("∀x ∀y (R(x, y) → Q(x))")], parse("Q(a)")),
        ([fact, parse("¬P(a)")], None),                      # contradictory premises
        ([fact], None),                                      # consistent premises: must be refused
    ]
    certificates = lean.certify(problems, LEAN)
    assert [c.accepted for c in certificates] == [True, False, False, True, True, True, False]
    assert all(set(c.axioms) <= lean.ALLOWED_AXIOMS for c in certificates if c.accepted)


@needs_lean
@given(st.lists(st.tuples(st.lists(SENTENCES, min_size=1, max_size=3), SENTENCES), min_size=8, max_size=8))
@settings(max_examples=12, deadline=None)
def test_lean_never_certifies_what_the_solver_refutes(problems):
    """Differential soundness: a kernel-accepted theorem must be an entailment for the solver too."""
    certificates = lean.certify(problems, LEAN)
    for (premises, goal), certificate in zip(problems, certificates):
        if certificate.accepted:
            assert decide(premises, goal).label in ("True", "Inconsistent")


@needs_lean
def test_a_failed_theorem_is_not_mistaken_for_a_proof():
    """Lean keeps a failed theorem in the environment with ``sorryAx``; it must still count as failed."""
    certificate = lean.certify([([parse("P(a)")], parse("Q(a)"))], LEAN)[0]
    assert not certificate.accepted and certificate.reason


def test_not_is_used_for_refutation_goals():
    theorem = lean.theorem(0, [parse("P(a)")], Not(parse("Q(a)")))
    assert ": (¬ (p1 c0)) := by" in theorem.source
