import pytest
from hypothesis import given, settings

from commonground.fol import (And, Const, Exists, Forall, Implies, Not, Or, ParseError, Pred, SignatureError, Var,
                              Xor, check_signature, close, parse, signature, to_text, unbound_variable_like)

from .strategies import SENTENCES


def test_precedence_and_associativity():
    A, B, C = Pred("A"), Pred("B"), Pred("C")
    assert parse("A ∧ B ∨ C") == Or(And(A, B), C)
    assert parse("A ∨ B ∧ C") == Or(A, And(B, C))
    assert parse("A → B → C") == Implies(A, Implies(B, C))
    assert parse("A ⊕ B → C") == Implies(Xor(A, B), C)
    assert parse("¬A ∧ B") == And(Not(A), B)
    assert parse("A -> B") == parse("A → B")
    assert parse("A <-> B") == parse("A ↔ B") == parse("A ⟷ B")


def test_flat_right_reads_mixed_connectives_the_other_way():
    A, B, C = Pred("A"), Pred("B"), Pred("C")
    assert parse("A ∧ B ∨ C", connectives="flat-right") == And(A, Or(B, C))
    assert parse("A ∧ B ∨ C") == Or(And(A, B), C)


def test_variables_are_what_a_quantifier_binds():
    f = parse("∀x (Loves(x, mary) → ∃y Loves(y, x))")
    assert f == Forall("x", Implies(Pred("Loves", (Var("x"), Const("mary"))),
                                    Exists("y", Pred("Loves", (Var("y"), Var("x"))))))
    assert parse("P(x)") == Pred("P", (Const("x"),))  # unbound: a constant until closed


def test_quantifier_scope_conventions():
    tight = parse("∃x P(x) ∧ Q(x)", scope="tight")
    wide = parse("∃x P(x) ∧ Q(x)", scope="wide")
    assert tight == And(Exists("x", Pred("P", (Var("x"),))), Pred("Q", (Const("x"),)))
    assert wide == Exists("x", And(Pred("P", (Var("x"),)), Pred("Q", (Var("x"),))))
    assert unbound_variable_like(tight) == ["x"] and unbound_variable_like(wide) == []


def test_names_from_the_dataset_are_accepted():
    assert parse("ValuedAt(yalesendowment, y42.3billion)").args[1] == Const("y42.3billion")
    assert parse("GrowthCompanies’Stocks(kO)").name == "GrowthCompanies’Stocks"


def test_universal_closure_of_unbound_variables():
    closed, names = close(parse("P(x) → Q(x, bob)"))
    assert names == ["x"]
    assert closed == Forall("x", Implies(Pred("P", (Var("x"),)), Pred("Q", (Var("x"), Const("bob")))))
    # constants that merely look short are left alone
    for text in ("P(a)", "Published(y1984)", "R(a, b1)"):
        assert close(parse(text)) == (parse(text), [])


@pytest.mark.parametrize("text", [
    "", "P(x", "P(x))", "∀ (P)", "P(x) ∧", "P(x) Q(x)", "P(,)", "(", "→ A",
    "#eval IO.println 1", "P(x); Q", "theorem t : False := by sorry", "A := B", "import Lean", "A\x00B", "{A}",
])
def test_everything_outside_the_grammar_is_rejected(text):
    with pytest.raises(ParseError):
        parse(text)


def test_size_limits():
    with pytest.raises(ParseError):
        parse("A ∧ " * 2000 + "A")
    with pytest.raises(ParseError):
        parse("(" * 500 + "A" + ")" * 500)


def test_signature_must_be_consistent():
    check_signature(signature([parse("P(a) ∧ Q(a, b)")]))
    with pytest.raises(SignatureError):
        check_signature(signature([parse("P(a) ∧ P(a, b)")]))
    with pytest.raises(SignatureError):
        check_signature(signature([parse("P(a) ∧ Q(P)")]))


@given(SENTENCES)
@settings(max_examples=300, deadline=None)
def test_printing_then_parsing_is_the_identity(f):
    text = to_text(f)
    assert parse(text, "tight") == f
    assert parse(text, "wide") == f
    assert parse(text, "tight", "flat-right") == f
