"""The engines against each other and against exhaustive enumeration."""
from hypothesis import given, settings
from hypothesis import strategies as st

from commonground import ground, smt
from commonground.fol import Not, parse, signature
from commonground.model import Structure, all_structures, holds
from commonground.verdict import decide, satisfiable

from .strategies import BINARY_PREDS, CONSTANTS, GROUND, SENTENCES, UNARY

SIGNATURE = [(p, 1) for p in UNARY] + [(p, 2) for p in BINARY_PREDS] + [("Z", 0)]


def random_structure(draw, size):
    preds = {}
    for name, arity in SIGNATURE:
        from itertools import product
        tuples = list(product(range(size), repeat=arity))
        preds[(name, arity)] = {t for t in tuples if draw(st.booleans())}
    return Structure(size, {c: draw(st.integers(0, size - 1)) for c in CONSTANTS}, preds)


@given(SENTENCES, st.data())
@settings(max_examples=200, deadline=None)
def test_negation_normal_form_keeps_the_meaning(f, data):
    structure = random_structure(data.draw, data.draw(st.integers(1, 3)))
    assert holds(ground.nnf(f), structure) == holds(f, structure)
    assert holds(ground.nnf(Not(f)), structure) == (not holds(f, structure))


@given(SENTENCES)
@settings(max_examples=120, deadline=None)
def test_a_model_from_the_grounder_is_a_model(f):
    result = ground.find_model([f], size=3)
    if result.satisfiable:
        assert holds(f, result.structure)


@given(SENTENCES)
@settings(max_examples=120, deadline=None)
def test_a_model_from_z3_is_a_model(f):
    result = smt.check([f])
    if result.status == "sat" and result.structure is not None:
        assert holds(f, result.structure)


def exhaustive_sat(sentences, size):
    sig = signature(sentences)
    return any(all(holds(s, m) for s in sentences)
               for m in all_structures(size, list(sig.constants), list(sig.predicates)))


@given(GROUND, GROUND)
@settings(max_examples=120, deadline=None)
def test_quantifier_free_sentences_agree_with_exhaustive_enumeration(f, g):
    """Ground sentences are in the decidable class with a tiny bound, so enumeration is the truth."""
    sentences = [f, g]
    bound = ground.epr_bound(sentences)
    assert bound is not None and bound <= 2
    truth = exhaustive_sat(sentences, bound)
    assert (smt.check(sentences).status == "sat") == truth
    answer = ground.find_model(sentences)
    assert answer.satisfiable == truth and answer.complete


UNARY_ONLY = st.sampled_from([
    "∀x (P(x) → Q(x))", "∃x (P(x) ∧ ¬Q(x))", "∀x (P(x) ∨ Q(x))", "∃x P(x)", "∀x ¬P(x)", "P(a)", "¬Q(a)",
    "∀x (Q(x) → ¬P(x))", "∃x (Q(x) ∧ P(x))", "∀x (P(x) ↔ Q(x))", "P(a) ⊕ Q(a)", "∃x ¬Q(x)", "∀x Q(x)",
])


@given(st.lists(UNARY_ONLY, min_size=1, max_size=5, unique=True))
@settings(max_examples=150, deadline=None)
def test_decidable_class_three_way_agreement(texts):
    """Z3, grounding at the decision bound, and exhaustive enumeration at that bound all agree."""
    sentences = [parse(t) for t in texts]
    bound = ground.epr_bound(sentences)
    assert bound is not None
    grounded = ground.find_model(sentences)
    assert grounded.complete
    assert grounded.satisfiable == (smt.check(sentences).status == "sat")
    if bound <= 3:  # enumeration stays small: 2 unary predicates, at most 1 constant
        assert grounded.satisfiable == exhaustive_sat(sentences, bound)


def test_bound_counts_constants_and_outer_existentials():
    assert ground.epr_bound([parse("∀x P(x)")]) == 1
    assert ground.epr_bound([parse("P(a) ∧ Q(b)"), parse("∃x ¬P(x)")]) == 3
    assert ground.epr_bound([parse("¬∀x P(x)")]) == 1          # a negated universal is an existential
    assert ground.epr_bound([parse("∀x ∃y R(x, y)")]) is None  # existential under a universal
    assert ground.epr_bound([parse("¬∃x ∀y R(x, y)")]) is None
    assert ground.epr_bound([parse("a = b")]) is None


def test_unsat_outside_the_class_is_reported_as_bounded_only():
    # "R is a strict order without a last element" has only infinite models.
    sentences = [parse("∀x ¬R(x, x)"), parse("∀x ∀y ∀z ((R(x, y) ∧ R(y, z)) → R(x, z))"), parse("∀x ∃y R(x, y)")]
    result = ground.find_model(sentences, size=4)
    assert not result.satisfiable and not result.complete
    assert satisfiable(sentences, timeout_ms=1500, engine="grounding").status == "unknown"


def test_verdicts():
    rule, fact = parse("∀x (P(x) → Q(x))"), parse("P(a)")
    assert decide([rule, fact], parse("Q(a)")).label == "True"
    assert decide([rule, fact], parse("¬Q(a)")).label == "False"
    assert decide([rule], parse("Q(a)")).label == "Uncertain"
    assert decide([fact, parse("¬P(a)")], parse("Q(a)")).label == "Inconsistent"
    assert decide([parse("∀x P(x)")], parse("∃x P(x)")).label == "True"  # domains are non-empty
    assert decide([parse("∀x ∃y R(x, y)"), parse("∀x ∀y (R(x, y) → Q(x))")], parse("Q(a)")).label == "True"


def test_uncertain_comes_with_two_checked_models():
    premises, conclusion = [parse("∀x (P(x) → Q(x))")], parse("Q(a)")
    verdict = decide(premises, conclusion)
    assert verdict.label == "Uncertain"
    assert all(holds(p, verdict.model_true) for p in premises) and holds(conclusion, verdict.model_true)
    assert all(holds(p, verdict.model_false) for p in premises) and not holds(conclusion, verdict.model_false)


def test_engines_can_be_forced():
    premises, conclusion = [parse("∀x (P(x) → Q(x))"), parse("P(a)")], parse("Q(a)")
    assert decide(premises, conclusion, engine="z3").label == "True"
    assert decide(premises, conclusion, engine="grounding").label == "True"
