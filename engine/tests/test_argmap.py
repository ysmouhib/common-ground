import json
from itertools import combinations
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from commonground import argmap
from commonground.fol import parse

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

# Random "statement sets": each statement is a small clause over 4 propositional atoms.
LITERALS = st.sampled_from(["A", "¬A", "B", "¬B", "C", "¬C", "D", "¬D"])
CLAUSES = st.lists(LITERALS, min_size=1, max_size=3, unique=True).map(" ∨ ".join)


def brute_force(items, sat):
    subsets = [frozenset(c) for r in range(len(items) + 1) for c in combinations(items, r)]
    status = {s: sat(s) for s in subsets}
    muses = {s for s in subsets if not status[s] and all(status[s - {x}] for x in s)}
    msses = {s for s in subsets if status[s] and all(not status[s | {x}] for x in items if x not in s)}
    return muses, msses


@given(st.lists(CLAUSES, min_size=1, max_size=7))
@settings(max_examples=120, deadline=None)
def test_marco_equals_brute_force_and_duality_holds(texts):
    formulas = {f"s{i}": parse(t) for i, t in enumerate(texts)}
    items = sorted(formulas)
    oracle = argmap._oracle(formulas, [], 2000)
    muses, msses = argmap.enumerate_mus_mss(items, oracle)
    expected_muses, expected_msses = brute_force(items, oracle)
    assert set(muses) == expected_muses and len(muses) == len(expected_muses)
    assert set(msses) == expected_msses and len(msses) == len(expected_msses)
    # Hitting-set duality: the minimal correction sets are exactly the minimal hitting sets of the MUSes.
    corrections = {frozenset(items) - m for m in msses}
    assert corrections == set(argmap.minimal_hitting_sets(muses, items))


def test_justifications_are_minimal_and_complete():
    premises = {"a": parse("P(c)"), "b": parse("∀x (P(x) → Q(x))"), "c": parse("Q(c)"), "d": parse("R(c)")}
    assert argmap.justifications(premises, parse("Q(c)")) == [["c"], ["a", "b"]]
    assert argmap.justifications(premises, parse("S(c)")) == []


def test_a_contradiction_among_premises_is_not_a_justification():
    premises = {"a": parse("P(c)"), "b": parse("¬P(c)"), "c": parse("Q(c)")}
    assert argmap.justifications(premises, parse("Z(c)")) == []
    assert argmap.justifications(premises, parse("Q(c)")) == [["c"]]


def test_plastic_bag_debate_positions_are_compatible():
    _, statements = argmap.load_debate(str(EXAMPLES / "plastic_bags.json"))
    report = argmap.analyze(statements)
    assert report["positions_compatible"] is True and report["conflicts"] == []
    assert report["minimal_concessions"] == []  # nothing has to be given up
    assert report["compatibility_witness"]["rechecked_by_independent_evaluator"] is True
    assert report["statements_without_formula"] == ["D1"]
    conclusions = report["conclusions"]
    assert conclusions["X1"]["justifications"] == [["A1", "A2", "A3", "A4"]]
    assert conclusions["X2"]["justifications"] == [["C2", "C4"]]
    assert conclusions["X3"]["justifications"] == [["A2", "C1", "S1"]]
    assert conclusions["X4"]["justifications"] == [["A1", "A2", "A3", "A4", "B1", "C2", "C4"]]
    assert conclusions["X1"]["from_each_position"] == {"advocate": "True", "critic": "Uncertain"}
    assert conclusions["X3"]["from_each_position"] == {"advocate": "Uncertain", "critic": "Uncertain"}
    assert conclusions["X3"]["from_all_premises"] == "True"


def test_constructed_contradiction_is_located_exactly():
    _, statements = argmap.load_debate(str(EXAMPLES / "remote_work.json"))
    report = argmap.analyze(statements)
    assert report["positions_compatible"] is False
    assert report["position_consistent"] == {"con": True, "pro": True}
    assert [c["statements"] for c in report["conflicts"]] == [["N1", "N2", "P4", "P5"], ["N1", "N2", "P1", "P2", "P3"]]
    concessions = [c["statements"] for c in report["minimal_concessions"]]
    assert concessions[:2] == [["N1"], ["N2"]] and len(concessions) == 8
    assert report["uncontested"] == ["S1"]
    assert report["conclusions"]["Y1"]["justifications"] == [["P4", "P5"], ["P1", "P2", "P3"]]


def test_stored_analysis_is_pinned_to_its_input():
    _, statements = argmap.load_debate(str(EXAMPLES / "plastic_bags.json"))
    first = argmap.input_hash(statements)
    changed = [s if s.id != "A4" else argmap.Statement(s.id, s.owner, s.kind, parse("ShouldAdopt(targetedBagPolicy)"))
               for s in statements]
    assert argmap.input_hash(changed) != first
    assert json.dumps(argmap.analyze(statements), sort_keys=True) == json.dumps(argmap.analyze(statements), sort_keys=True)
