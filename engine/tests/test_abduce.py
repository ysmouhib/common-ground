import json

import pytest

from commonground import abduce, fol

DOC = "All humans are mortal. Socrates is a human. Therefore Socrates is mortal."
DOC2 = "Every politician promises change."
S1 = (0, DOC.index(".") + 1)
S2 = (S1[1] + 1, S1[1] + 1 + len("Socrates is a human."))


def record(**overrides):
    r = abduce.Record(
        camp="campA",
        documents=[abduce.Document("d1", DOC), abduce.Document("d2", DOC2)],
        statements=[
            abduce.RecordStatement("e1", abduce.STANCE_ENDORSED, "Mortal(socrates)", "d1", DOC[S1[0]:S2[1]], (S1[0], S2[1])),
            abduce.RecordStatement("r1", abduce.STANCE_FIRM, None, "d2", DOC2, (0, len(DOC2))),
        ],
    )
    for key, value in overrides.items():
        setattr(r, key, value)
    return r


def candidate(fol_text, quotes):
    return abduce.Candidate(fol_text, quotes)


GOOD_QUOTE = ("d1", DOC[S1[0]:S1[1]], S1)


def test_record_validation_accepts_verbatim_spans_and_parses_fol():
    record().validate()


@pytest.mark.parametrize("mutate, problem", [
    (lambda r: r.statements[0].__setattr__("span", (0, 3)), "does not match"),
    (lambda r: r.statements[0].__setattr__("span", (0, 10_000)), "outside document"),
    (lambda r: r.statements[0].__setattr__("stance", "maybe"), "stance"),
    (lambda r: r.statements[0].__setattr__("document", "nope"), "unknown document"),
    (lambda r: r.statements[0].__setattr__("fol_text", "Mortal((socrates)"), "expected NAME"),
    (lambda r: r.statements.append(r.statements[0]), "unique"),
    (lambda r: r.documents.append(abduce.Document("d1", "other")), "unique"),
])
def test_record_validation_rejects(mutate, problem):
    r = record()
    mutate(r)
    with pytest.raises(ValueError, match=problem):
        r.validate()


def test_scripted_source_returns_candidates_once_per_call_in_order():
    c1 = candidate("∀x (Human(x) → Mortal(x))", [GOOD_QUOTE])
    c2 = candidate("Human(socrates)", [("d1", DOC[S2[0]:S2[1]], S2)])
    src = abduce.ScriptedSource([c1, c2])
    pool = abduce.collect(src, record())
    assert src.calls == ["campA"]
    assert [fol.to_text(c.formula) for c in pool.candidates] == [
        fol.to_text(fol.parse("∀x (Human(x) → Mortal(x))")), fol.to_text(fol.parse("Human(socrates)"))]
    assert pool.dropped == []
    # every quote span exists verbatim in its source document
    docs = record().documents_by_id()
    for c in pool.candidates:
        for doc_id, quote, (start, end) in c.quotes:
            assert docs[doc_id].text[start:end] == quote


@pytest.mark.parametrize("cand, problem", [
    (candidate("not a formula", [GOOD_QUOTE]), "does not parse"),
    (candidate("Human(socrates)", []), "no supporting quote"),
    (candidate("Human(socrates)", [("d1", "Socrates is a mortal.", S1)]), "does not match"),
    (candidate("Human(socrates)", [("nope", DOC[:5], (0, 5))]), "unknown document"),
    (candidate("Human(socrates)", [("d1", DOC[:5], (0, 10_000))]), "outside document"),
    (candidate("  ", [GOOD_QUOTE]), "no FOL text"),
])
def test_invalid_candidates_are_dropped_with_reason(cand, problem):
    pool = abduce.collect(abduce.ScriptedSource([cand]), record())
    assert pool.candidates == []
    assert len(pool.dropped) == 1 and problem in pool.dropped[0].reason


def test_duplicate_candidates_are_dropped():
    cand = candidate("Human(socrates)", [GOOD_QUOTE])
    pool = abduce.collect(abduce.ScriptedSource([cand, cand]), record())
    assert len(pool.candidates) == 1
    assert pool.dropped[0].reason == "duplicate candidate"


def test_too_many_candidates_is_refused():
    cands = [candidate("Human(socrates)", [("d1", DOC[S1[0]:S1[1]], S1)]) for _ in range(abduce.MAX_CANDIDATES + 1)]
    with pytest.raises(ValueError, match="at most"):
        abduce.collect(abduce.ScriptedSource(cands), record())


def test_collect_is_deterministic_for_a_scripted_source():
    c1 = candidate("∀x (Human(x) → Mortal(x))", [GOOD_QUOTE])
    first = abduce.collect(abduce.ScriptedSource([c1]), record())
    second = abduce.collect(abduce.ScriptedSource([c1]), record())
    assert [fol.to_text(c.formula) for c in first.candidates] == [fol.to_text(c.formula) for c in second.candidates]


class Scripted:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def describe(self):
        return {"model": "scripted-chat", "temperature": 0.0}

    def complete(self, system, user):
        self.calls.append((system, user))
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply, {"total_tokens": 10}


GOOD_REPLY = json.dumps({"candidates": [
    {"fol": "∀x (Human(x) → Mortal(x))",
     "quotes": [{"document": "d1", "text": DOC[S1[0]:S1[1]], "span": list(S1)}]},
]})


def test_chat_source_parses_json_and_validates():
    src = abduce.ChatSource(Scripted(GOOD_REPLY))
    pool = abduce.collect(src, record())
    assert [fol.to_text(c.formula) for c in pool.candidates] == [fol.to_text(fol.parse("∀x (Human(x) → Mortal(x))"))]
    assert pool.dropped == []
    assert src.describe() == {"model": "scripted-chat", "temperature": 0.0}


def test_chat_source_accepts_fenced_reply_and_retries_bad_json():
    client = Scripted("not json", "```json" + chr(10) + GOOD_REPLY + chr(10) + "```")
    pool = abduce.collect(abduce.ChatSource(client), record())
    assert len(pool.candidates) == 1 and len(client.calls) == 2


def test_chat_source_without_json_raises():
    src = abduce.ChatSource(Scripted("nope", "still nope", "and nope"))
    with pytest.raises(ValueError, match="no JSON object"):
        abduce.collect(src, record())


def test_chat_source_drops_a_candidate_with_a_bad_span():
    reply = json.dumps({"candidates": [
        {"fol": "Human(socrates)",
         "quotes": [{"document": "d1", "text": "Socrates is a mortal.", "span": list(S1)}]},
    ]})
    pool = abduce.collect(abduce.ChatSource(Scripted(reply)), record())
    assert pool.candidates == [] and "does not match" in pool.dropped[0].reason


# --- CG3-3: the certified layer -------------------------------------------

from commonground import lean
from commonground.fol import Not

LEAN = lean.find_lean()
needs_lean = pytest.mark.skipif(LEAN is None, reason="no Lean 4.35.0 (set LEAN_BIN)")

AXIOM_ALL = "∀x (Human(x) → Mortal(x))"
AXIOM_SOC = "Human(socrates)"


def check_record(**overrides):
    r = abduce.Record(
        camp="campA",
        documents=[abduce.Document("d1", DOC)],
        statements=[
            abduce.RecordStatement("e1", abduce.STANCE_ENDORSED, "Mortal(socrates)", "d1", DOC[S1[0]:S2[1]], (S1[0], S2[1])),
            abduce.RecordStatement("r1", abduce.STANCE_FIRM, "¬Mortal(socrates)", "d1", DOC[S1[0]:S2[1]], (S1[0], S2[1])),
            abduce.RecordStatement("s1", abduce.STANCE_SOFT, "Flies(socrates)", "d1", DOC[S1[0]:S1[1]], S1),
        ],
    )
    for key, value in overrides.items():
        setattr(r, key, value)
    return r


def test_entailment_check_holds_by_solver_refutation():
    c = abduce.entailment_check([fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)], fol.parse("Mortal(socrates)"))
    assert c.outcome == "holds" and c.badge == abduce.BADGE_SOLVER


def test_entailment_check_fails_with_an_explicit_model():
    c = abduce.entailment_check([fol.parse(AXIOM_SOC)], fol.parse("Mortal(socrates)"))
    assert c.outcome == "fails" and c.badge == abduce.BADGE_SOLVER
    assert c.model_false is not None  # finite model where Mortal(socrates) is false


def test_non_entailment_check_holds_with_model_and_fails_when_entailed():
    ok = abduce.non_entailment_check([fol.parse(AXIOM_SOC)], fol.parse("Flies(socrates)"))
    assert ok.outcome == "holds" and ok.model_false is not None
    bad = abduce.non_entailment_check([fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)], fol.parse("Mortal(socrates)"))
    assert bad.outcome == "fails"


def test_consistency_check_holds_and_fails():
    ok = abduce.consistency_check([fol.parse(AXIOM_SOC)])
    assert ok.outcome == "holds"
    bad = abduce.consistency_check([fol.parse("P(a)"), fol.parse("¬P(a)")])
    assert bad.outcome == "fails"


def test_undecided_is_pending_never_false(monkeypatch):
    forced = abduce._verdict.Verdict("Undecided", True, notes=["forced"])
    monkeypatch.setattr(abduce._verdict, "decide", lambda *a, **k: forced)
    c = abduce.entailment_check([fol.parse(AXIOM_SOC)], fol.parse("Mortal(socrates)"))
    assert c.outcome == "pending" and c.badge == abduce.BADGE_PENDING


def test_check_system_certifies_a_minimal_sufficient_system():
    checks = abduce.check_system([fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)], check_record())
    assert checks.certified
    assert checks.consistent.outcome == "holds"
    assert all(c.outcome == "holds" for c in checks.sufficiency)
    assert all(c.outcome == "holds" for c in checks.firm_rejections)   # A ⊨ ¬¬Mortal(socrates)
    assert all(c.outcome == "holds" for c in checks.soft_rejections)   # A ⊭ Flies(socrates), with model
    assert all(c.outcome == "holds" for c in checks.minimality)         # both axioms needed


def test_check_system_catches_a_redundant_axiom():
    axioms = [fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC), fol.parse("∀x (Mortal(x) → Mortal(x))")]
    checks = abduce.check_system(axioms, check_record())
    assert not checks.certified
    redundant = [c for c in checks.minimality if c.outcome == "fails"]
    assert len(redundant) == 1 and "redundant" in redundant[0].detail


def test_check_system_catches_a_missing_entailment():
    checks = abduce.check_system([fol.parse(AXIOM_SOC)], check_record())
    assert not checks.certified
    assert any(c.outcome == "fails" for c in checks.sufficiency)


def test_check_system_marks_unformalized_statements_pending():
    r = check_record()
    r.statements[0].fol_text = None
    checks = abduce.check_system([fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)], r)
    assert not checks.certified
    assert checks.sufficiency[0].outcome == "pending"


@needs_lean
def test_entailment_check_is_kernel_checked_when_lean_accepts():
    c = abduce.entailment_check([fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)], fol.parse("Mortal(socrates)"),
                                lean_bin=LEAN)
    assert c.outcome == "holds" and c.badge == abduce.BADGE_KERNEL and "kernel" in c.detail


@needs_lean
def test_certify_sufficiency_accepts_a_theorem_and_rejects_a_non_theorem():
    axioms = [fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)]
    good = abduce.certify_sufficiency(axioms, [fol.parse("Mortal(socrates)")], LEAN)
    assert good[0].accepted
    bad = abduce.certify_sufficiency(axioms, [fol.parse("Flies(socrates)")], LEAN)
    assert not bad[0].accepted


# --- CG3-4: cost, search, hull ---------------------------------------------

from commonground.argmap import TooMany

DOCX = "Socrates is human. Socrates is mortal. Plato is human. Plato is mortal. Socrates does not fly."


def span_of(sub):
    i = DOCX.index(sub)
    return (i, i + len(sub))


def big_record():
    def st(sid, fol_text, quote):
        return abduce.RecordStatement(sid, abduce.STANCE_ENDORSED, fol_text, "dx", quote, span_of(quote))
    return abduce.Record(
        camp="campX",
        documents=[abduce.Document("dx", DOCX)],
        statements=[
            st("e1", "Human(socrates)", "Socrates is human."),
            st("e2", "Mortal(socrates)", "Socrates is mortal."),
            st("e3", "Human(plato)", "Plato is human."),
            st("e4", "Mortal(plato)", "Plato is mortal."),
            abduce.RecordStatement("s1", abduce.STANCE_SOFT, "Flies(socrates)", "dx",
                                  "Socrates does not fly.", span_of("Socrates does not fly.")),
        ],
    )


C1 = "∀x (Human(x) → Mortal(x))"


def big_pool():
    stated = [st.formula() for st in big_record().statements if st.stance == abduce.STANCE_ENDORSED]
    return stated + [fol.parse(C1)]


def test_normal_form_splits_conjunctions_top_level_and_under_forall():
    parts = abduce.split_conjunctions(fol.parse("A ∧ B ∧ ∀x (C(x) ∧ D(x))"))
    assert [fol.to_text(p) for p in parts] == ["A", "B", "(∀x C(x))", "(∀x D(x))"]
    assert abduce.normal_form_size(fol.parse("A ∧ B")) == 2


def test_cost_counts_size_on_normal_form_and_plausibility():
    assert abduce.cost([fol.parse("A ∧ B")], {}, 0.3) == 0.6          # p = 1, size 2
    assert abduce.cost([fol.parse(C1)], {fol.to_text(fol.parse(C1)): 0.9}, 0.3) == pytest.approx(0.4)


def test_select_prefers_the_unstated_axiom_when_it_replaces_two_stated_claims():
    pool = big_pool()
    plaus = {fol.to_text(fol.parse(C1)): 0.9}
    sel = abduce.select(pool, big_record(), plaus, 0.3)
    assert sel.best_cost == pytest.approx(1.0)
    expected = [fol.to_text(fol.parse(C1)), fol.to_text(fol.parse("Human(socrates)")), fol.to_text(fol.parse("Human(plato)"))]
    assert sorted(sel.systems[0]) == sorted(expected) and len(sel.systems) == 1
    assert not sel.exhausted


def test_bnb_matches_brute_force_across_lambda():
    pool = big_pool()
    plaus = {fol.to_text(fol.parse(C1)): 0.9}
    rec = big_record()
    for lam in (0.05, 0.1, 0.2, 0.3, 0.5):
        a = abduce.select(pool, rec, plaus, lam)
        b = abduce.select_bruteforce(pool, rec, plaus, lam)
        assert sorted(map(sorted, a.systems)) == sorted(map(sorted, b.systems))
        assert a.best_cost == pytest.approx(b.best_cost)


def test_ties_are_all_reported():
    pool = big_pool()
    plaus = {fol.to_text(fol.parse(C1)): 0.7}   # u = 0.3: 0.3 + 3λ ties 4λ at λ = 0.3
    sel = abduce.select_bruteforce(pool, big_record(), plaus, 0.3)
    assert len(sel.systems) == 2 and sel.best_cost == pytest.approx(1.2)


def test_hull_intervals_match_a_lambda_grid_scan():
    pool = big_pool()
    plaus = {fol.to_text(fol.parse(C1)): 0.9}
    sel = abduce.select_bruteforce(pool, big_record(), plaus, 0.3)
    hull = abduce.hull_intervals(sel.all_certified, pool, plaus)
    by_text = {fol.to_text(f): f for f in pool}
    for lam in (0.05, 0.15, 0.3, 0.9):
        best = min(sel.all_certified, key=lambda t: abduce.cost([by_text[x] for x in t], plaus, lam))
        in_hull = [h for h in hull if h["lam_interval"][0] - 1e-9 <= lam <= h["lam_interval"][1] + 1e-9]
        assert len(in_hull) == 1
        assert sorted(in_hull[0]["system"]) == sorted(best)
    # at the boundary lambda = 0.1 both hull vertices are optimal (a reported tie)
    costs = [abduce.cost([by_text[x] for x in s], plaus, 0.1) for s in sel.all_certified]
    assert costs[0] == pytest.approx(costs[1])
    margins = abduce.margin_at(sel.all_certified, pool, plaus, 0.3)
    assert margins == pytest.approx(0.2)


def test_pool_cap_is_enforced():
    pool = [fol.parse(f"P{i}(a)") for i in range(abduce.MAX_POOL + 1)]
    with pytest.raises(TooMany):
        abduce.select(pool, big_record(), {}, 0.3)


# --- CG3-5 / CG3-6: negative controls and the symbolic baseline ------------


def test_negative_controls_battery_passes_on_a_certified_system():
    axioms = [fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)]
    report = abduce.negative_controls(axioms, check_record())
    assert report["all_passed"], report["controls"]
    assert report["controls"]["lean_negations_rejected"] is None  # no Lean in this run


@needs_lean
def test_negative_controls_lean_rejects_the_negations():
    axioms = [fol.parse(AXIOM_ALL), fol.parse(AXIOM_SOC)]
    report = abduce.negative_controls(axioms, check_record(), lean_bin=LEAN)
    assert report["controls"]["lean_negations_rejected"] is True
    assert report["controls"]["lean_accepts_a_theorem"] is True   # the rejections are not a broken Lean
    assert report["all_passed"]


def test_negative_controls_detect_a_broken_system():
    # a system that does not entail an endorsed claim is not certified, and the battery says
    # exactly that, by name — not through a side effect of some other control
    report = abduce.negative_controls([fol.parse(AXIOM_SOC)], check_record())
    assert report["controls"]["system_certified"] is False
    assert not report["all_passed"]
    # the checker-side controls that do not presuppose sufficiency still behave
    assert report["controls"]["fresh_claim_not_entailed"] and report["controls"]["violated_rejection_caught"]
    # an inconsistent system entails anything, even a claim over a symbol the record never uses
    bad = abduce.negative_controls([fol.parse("Mortal(socrates)"), fol.parse("Q(a) ∧ ¬Q(a)")], check_record())
    assert bad["controls"]["fresh_claim_not_entailed"] is False and not bad["all_passed"]


def test_baseline_system_runs_stated_and_minimal_stated_through_the_checks():
    base = abduce.baseline_system(big_record())
    assert base["stated"].certified
    assert base["minimal_stated"].certified
    assert base["minimal_formulas"] == base["stated_formulas"]  # nothing redundant here


def test_baseline_minimal_subset_drops_a_redundant_stated_claim():
    r = check_record()
    r.statements.append(abduce.RecordStatement(
        "e2", abduce.STANCE_ENDORSED, "Mortal(socrates)", "d1", DOC[S1[0]:S2[1]], (S1[0], S2[1])))
    base = abduce.baseline_system(r)
    # e2 duplicates e1's formula and the firm negation is entailed by e1: the minimal subset is smaller
    assert len(base["minimal_formulas"]) < len(base["stated_formulas"])
    assert base["minimal_stated"].certified


# --- soundness review 2026-11-14: one regression test per hole that was found ----------

import hashlib
import random

P = fol.parse
UNDECIDED = abduce._verdict.Verdict("Undecided", None, notes=["forced"])


def test_non_entailment_and_consistency_without_verdict_are_pending(monkeypatch):
    # the solvers (the dependency) give no verdict; the checks must not turn that into one
    monkeypatch.setattr(abduce._verdict, "decide", lambda *a, **k: UNDECIDED)
    c = abduce.non_entailment_check([P(AXIOM_SOC)], P("Flies(socrates)"))
    assert c.outcome == "pending" and c.badge == abduce.BADGE_PENDING and c.model_false is None
    monkeypatch.setattr(abduce._verdict, "satisfiable",
                        lambda *a, **k: abduce._verdict.SatAnswer("unknown", note="forced"))
    c = abduce.consistency_check([P(AXIOM_SOC)])
    assert c.outcome == "pending" and c.badge == abduce.BADGE_PENDING and c.model is None


def test_minimality_without_verdict_blocks_certification(monkeypatch):
    axioms = [P(AXIOM_ALL), P(AXIOM_SOC)]
    real = abduce._verdict.decide

    def decide(premises, conclusion, *a, **k):   # only the removal checks get no verdict
        return UNDECIDED if len(premises) < len(axioms) else real(premises, conclusion, *a, **k)

    monkeypatch.setattr(abduce._verdict, "decide", decide)
    checks = abduce.check_system(axioms, check_record())
    assert checks.minimality and all(c.outcome == "pending" for c in checks.minimality)
    assert not checks.certified


def test_checks_carry_their_evidence():
    ok = abduce.consistency_check([P(AXIOM_SOC)])
    assert ok.model is not None and ok.to_json()["model"]["size"] >= 1
    checks = abduce.check_system([P(AXIOM_ALL), P(AXIOM_SOC)], check_record())
    assert checks.consistent.to_json()["model"] is not None
    # a needed axiom shows the model of the rest in which the witness claim fails
    assert all(m.outcome == "holds" and m.to_json()["model_where_claim_fails"] for m in checks.minimality)
    assert all(c.to_json()["model_where_claim_fails"] for c in checks.soft_rejections)


@needs_lean
def test_kernel_check_exports_the_lean_source_and_its_hash():
    c = abduce.entailment_check([P(AXIOM_ALL), P(AXIOM_SOC)], P("Mortal(socrates)"), lean_bin=LEAN)
    cert = c.to_json()["certificate"]
    assert cert["toolchain"] == lean.TOOLCHAIN and "theorem t_0" in cert["lean_source"]
    assert cert["sha256"] == hashlib.sha256(cert["lean_source"].encode("utf-8")).hexdigest()
    lean.assert_generated(cert["lean_source"])   # the exported text is the generated text
    # a solver-only verdict carries no certificate
    assert abduce.entailment_check([P(AXIOM_ALL), P(AXIOM_SOC)], P("Mortal(socrates)")).certificate is None


def test_a_refutation_outside_the_decidable_class_says_what_it_rests_on():
    inside = abduce.entailment_check([P(AXIOM_ALL), P(AXIOM_SOC)], P("Mortal(socrates)"))
    assert inside.outcome == "holds" and "Bernays" not in inside.detail
    for premises, goal in ((["∀x P(f(x))"], "P(f(a))"),                       # function symbol
                           (["a = b", "P(a)"], "P(b)"),                         # equality
                           (["∀x ∃y R(x, y)", "∀x ∀y (R(x, y) → Q(x))"], "Q(a)")):  # ∃ under ∀
        outside = abduce.entailment_check([P(p) for p in premises], P(goal))
        assert outside.outcome == "holds" and outside.badge == abduce.BADGE_SOLVER
        assert "rests on Z3 alone" in outside.detail


def test_a_system_is_a_set_duplicate_axioms_count_once():
    checks = abduce.check_system([P(AXIOM_ALL), P(AXIOM_SOC), P(AXIOM_SOC)], check_record())
    assert checks.certified and len(checks.minimality) == 2


def test_negated_iff_and_xor_reach_the_normal_form():
    assert abduce.normal_form_size(P("¬(A ⊕ B)")) == abduce.normal_form_size(P("A ↔ B")) == 2
    assert abduce.normal_form_size(P("¬(A ↔ B)")) == abduce.normal_form_size(P("A ⊕ B")) == 1


C1T = fol.to_text(fol.parse(C1))


@pytest.mark.parametrize("plaus, lam", [
    ({C1T: 1.5}, 0.3), ({C1T: -0.1}, 0.3), ({C1T: float("nan")}, 0.3), ({C1T: "0.9"}, 0.3), ({C1T: True}, 0.3),
    ({}, 0.0), ({}, -1.0), ({}, float("inf")), ({}, "0.3"),
])
def test_charges_outside_their_range_are_refused(plaus, lam):
    # outside λ > 0 and p in [0, 1] a charge can be negative, and cost pruning is no longer valid
    for search in (abduce.select, abduce.select_bruteforce):
        with pytest.raises(ValueError):
            search(big_pool(), big_record(), plaus, lam)


def test_the_check_budget_is_reported_and_is_not_a_false_alarm():
    pool, rec, plaus = big_pool(), big_record(), {C1T: 0.9}
    full = abduce.select_bruteforce(pool, rec, plaus, 0.3)
    assert not full.exhausted
    # a budget of exactly the checks needed finishes the search: no "exhausted" then
    exact = abduce.select_bruteforce(pool, rec, plaus, 0.3, max_checks=full.checks)
    assert not exact.exhausted and exact.systems == full.systems
    for search in (abduce.select, abduce.select_bruteforce):
        capped = search(pool, rec, plaus, 0.3, max_checks=1)
        assert capped.exhausted and capped.checks == 1
        # the one check went to the stated system A₀: certified, yet not the optimum
        assert len(capped.systems) == 1 and capped.systems != full.systems
        assert capped.best_cost > full.best_cost


def test_hull_keeps_only_systems_that_some_lambda_selects():
    pool = [P("A1"), P("B1"), P("C1")]
    # (size 2, implausibility 0.5) is larger and less plausible than (1, 0): on no interval
    hull = abduce.hull_intervals([["A1"], ["B1", "C1"]], pool, {"C1": 0.5})
    assert [(h["size"], h["lam_interval"]) for h in hull] == [(1, [0.0, float("inf")])]
    # equal size: the less implausible one only; systems on the same point are ties
    hull = abduce.hull_intervals([["A1"], ["B1"], ["C1"]], pool, {"C1": 0.5})
    assert len(hull) == 1 and hull[0]["system"] == ["A1"] and hull[0]["tied_systems"] == [["B1"]]


def test_hull_intervals_agree_with_a_scan_on_random_systems():
    rng = random.Random(7)
    atoms = [f"Q{i}" for i in range(6)]
    pool = [P(a) for a in atoms]
    for _ in range(200):
        plaus = {a: rng.choice([0.1, 0.3, 0.5, 0.7, 0.9, 1.0]) for a in atoms}
        systems = [sorted(rng.sample(atoms, rng.randint(1, 6))) for _ in range(rng.randint(1, 7))]

        def c(texts, lam):
            return abduce.cost([P(t) for t in texts], plaus, lam)

        hull = abduce.hull_intervals(systems, pool, plaus)
        assert hull
        for h in hull:   # every reported interval is real, and the system is optimal inside it
            lo, hi = h["lam_interval"]
            assert 0 <= lo < hi
            mid = lo + 1.0 if hi == float("inf") else (lo + hi) / 2
            assert c(h["system"], mid) == pytest.approx(min(c(s, mid) for s in systems))
        for lam in (0.013, 0.07, 0.21, 0.37, 0.93, 2.3):   # and every λ > 0 is covered
            inside = [h for h in hull if h["lam_interval"][0] - 1e-9 <= lam <= h["lam_interval"][1] + 1e-9]
            assert inside
            assert all(c(h["system"], lam) == pytest.approx(min(c(s, lam) for s in systems)) for h in inside)


CLAIM = "Claim."


def varied_record(statements):
    return abduce.Record("campV", [abduce.Document("dv", CLAIM)],
                         [abduce.RecordStatement(sid, stance, f, "dv", CLAIM, (0, len(CLAIM)))
                          for sid, stance, f in statements])


VARIED = {
    # a firm rejection in E⁺, an axiom of normal-form size 2, a chain of two unstated axioms
    "firm-and-conjunct": (
        [("e1", "endorsed", "Human(socrates)"), ("e2", "endorsed", "Mortal(socrates)"),
         ("r1", "rejected_firm", "Immortal(socrates)"), ("s1", "rejected_soft", "Flies(socrates)")],
        ["∀x (Human(x) → Mortal(x))", "∀x (Mortal(x) → ¬Immortal(x))",
         "∀x (Human(x) → (Mortal(x) ∧ ¬Immortal(x)))"]),
    # a candidate that violates the soft rejection, and a conjunction of two stated claims
    "soft-violation": (
        [("e1", "endorsed", "Human(socrates)"), ("e2", "endorsed", "Mortal(socrates)"),
         ("e3", "endorsed", "Human(plato)"), ("e4", "endorsed", "Mortal(plato)"),
         ("s1", "rejected_soft", "Flies(plato)")],
        ["∀x (Human(x) → Mortal(x))", "∀x (Human(x) → Flies(x))", "Human(socrates) ∧ Human(plato)"]),
}


@pytest.mark.parametrize("case, seed, lam", [
    ("firm-and-conjunct", 1, 0.05), ("firm-and-conjunct", 2, 0.3), ("firm-and-conjunct", 3, 0.8),
    ("soft-violation", 4, 0.1), ("soft-violation", 5, 0.45),
])
def test_bnb_matches_brute_force_on_varied_pools(case, seed, lam):
    statements, candidates = VARIED[case]
    rec = varied_record(statements)
    pool = abduce._targets(rec) + [P(c) for c in candidates]
    rng = random.Random(seed)
    plaus = {fol.to_text(P(c)): rng.choice([0.1, 0.3, 0.5, 0.7, 0.9]) for c in candidates}
    a = abduce.select(pool, rec, plaus, lam)
    b = abduce.select_bruteforce(pool, rec, plaus, lam)
    assert not a.exhausted and not b.exhausted
    assert a.systems and sorted(map(sorted, a.systems)) == sorted(map(sorted, b.systems))
    assert a.best_cost == pytest.approx(b.best_cost)
    by_text = {fol.to_text(f): f for f in pool}
    for texts in a.systems:   # what is selected is certified, and never breaks the soft rejection
        assert abduce.check_system([by_text[t] for t in texts], rec).certified
    # every system the pruned search certified is one the exhaustive search certified
    assert {tuple(s) for s in a.all_certified} <= {tuple(s) for s in b.all_certified}


def test_negative_controls_pass_when_the_system_refutes_its_soft_rejection():
    # A ⊨ ¬r, so A ∪ {r} has no model: the violated-rejection control is still about the
    # rejection check, and a certified system passes the battery
    rec = varied_record([("e1", "endorsed", "Purr(cats) ∧ ¬Bark(cats)"), ("s1", "rejected_soft", "Bark(cats)")])
    axioms = [P("Purr(cats) ∧ ¬Bark(cats)")]
    assert abduce.check_system(axioms, rec).certified
    report = abduce.negative_controls(axioms, rec)
    assert report["all_passed"], report["controls"]
    assert report["controls"]["violated_rejection_caught"] is True


def test_a_lean_that_rejects_everything_does_not_pass_the_control(monkeypatch):
    # the Lean runner (the dependency) fails on every problem, as after a timeout or a bad
    # install: "the negations were rejected" must not then read as a passed control
    monkeypatch.setattr(abduce._lean, "certify", lambda problems, lean_bin, **k: [
        abduce._lean.Certificate(f"t_{i}", False, reason="forced") for i, _ in enumerate(problems)])
    report = abduce.negative_controls([P(AXIOM_ALL), P(AXIOM_SOC)], check_record(), lean_bin="broken-lean")
    assert report["controls"]["lean_negations_rejected"] is True
    assert report["controls"]["lean_accepts_a_theorem"] is False
    assert not report["all_passed"]


@pytest.mark.parametrize("mutate, problem", [
    (lambda r: r.__setitem__("statements", "oops"), "must be lists"),
    (lambda r: r.pop("camp"), 'needs "camp"'),
    (lambda r: r.__setitem__("camp", "  "), "non-empty name"),
    (lambda r: r["statements"][0].__setitem__("span", ["0", "22"]), "two integers"),
    (lambda r: r["statements"][0].__setitem__("span", [0.0, 22.0]), "two integers"),
    (lambda r: r["statements"][0].__setitem__("span", [0, 22, 3]), "two integers"),
    (lambda r: r["statements"][0].__setitem__("fol", 5), "must be a formula"),
    (lambda r: r["statements"][0].__setitem__("fol", ""), "must be a formula"),
    (lambda r: r["statements"][0].__setitem__("fol", "Mortal((socrates)"), "does not parse"),
    (lambda r: r["statements"][0].__setitem__("quote", "All humans are mortals"), "does not match"),
    (lambda r: r["statements"][0].pop("quote"), 'needs "quote"'),
    (lambda r: r["statements"].append("not an object"), "must be an object"),
    (lambda r: r["documents"].append({"id": "d2"}), 'needs "id" and "text"'),
])
def test_record_json_is_validated_with_a_reason(mutate, problem):
    raw = {"camp": "campA", "documents": [{"id": "d1", "text": DOC}],
           "statements": [{"id": "e1", "stance": "endorsed", "fol": "Mortal(socrates)", "document": "d1",
                           "quote": DOC[S1[0]:S1[1]], "span": list(S1)}]}
    assert abduce.record_from_json(json.loads(json.dumps(raw))).camp == "campA"
    mutate(raw)
    with pytest.raises(ValueError, match=problem):
        abduce.record_from_json(raw)


@pytest.mark.parametrize("data", [[], {"candidates": "x"}, {"candidates": ["P(a)"]},
                                  {"candidates": [{"fol": "P(a)", "quotes": "x"}]},
                                  {"candidates": [{"fol": "P(a)", "quotes": ["x"]}]}])
def test_candidates_json_shape_is_validated(data):
    with pytest.raises(ValueError):
        abduce.candidates_from_json(data)


def test_a_candidate_with_a_malformed_quote_is_dropped_not_a_crash():
    data = {"candidates": [{"fol": "Human(socrates)", "quotes": [{"document": ["d1"], "text": 3, "span": "x"}]},
                           {"fol": 7, "quotes": []}]}
    pool = abduce.collect(abduce.ScriptedSource(abduce.candidates_from_json(data)), record())
    assert pool.candidates == [] and len(pool.dropped) == 2


def test_the_prompt_shows_formulas_the_grammar_accepts():
    assert fol.to_text(P("∀x (Human(x) → Mortal(x))")) and "∀x (Human(x) → Mortal(x))" in abduce.PROMPT
    assert "forall" not in abduce.PROMPT   # the grammar has no such keyword
