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
