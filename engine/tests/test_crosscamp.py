import json

import pytest

from commonground import abduce, crosscamp, fol, lean

LEAN = lean.find_lean()
needs_lean = pytest.mark.skipif(LEAN is None, reason="no Lean 4.35.0 (set LEAN_BIN)")


def make_record(camp, doc_id, text, statements):
    def span_of(sub):
        i = text.index(sub)
        return (i, i + len(sub))

    stmts = [abduce.RecordStatement(sid, stance, fol_text, doc_id, quote, span_of(quote))
             for sid, stance, fol_text, quote in statements]
    return abduce.Record(camp, [abduce.Document(doc_id, text)], stmts)


def make_camp(camp, doc_id, text, statements, candidates=(), plaus=None, lam=0.3):
    record = make_record(camp, doc_id, text, statements)
    cands = []
    for f, q in candidates:
        i = text.index(q)
        cands.append(abduce.Candidate(f, [(doc_id, q, (i, i + len(q)))]))
    src = abduce.ScriptedSource(cands)
    report = abduce.report_camp(record, src, dict(plaus or {}), lam=lam)
    return crosscamp.Camp(record, report)


# camp A and camp B share exactly the claim Q(a)
TEXT_A = "A says: P(a) holds. And Q(a) holds too."
TEXT_B = "B says: Q(a) holds. Also R(a) holds."


def camps_shared_q():
    a = make_camp("A", "da", TEXT_A,
                  [("e1", "endorsed", "P(a)", "P(a) holds."),
                   ("e2", "endorsed", "Q(a)", "Q(a) holds too.")])
    b = make_camp("B", "db", TEXT_B,
                  [("e1", "endorsed", "Q(a)", "Q(a) holds."),
                   ("e2", "endorsed", "R(a)", "R(a) holds.")])
    return [a, b]


def test_stated_common_ground_is_exactly_the_shared_claim():
    cg = crosscamp.common_ground(camps_shared_q())
    agreed = [e["statement"] for e in cg["stated"]["agreed"]]
    assert agreed == ["Q(a)"]
    assert cg["stated"]["union_consistent"]["outcome"] == "holds"
    assert cg["no_certified_systems"] == []
    # tier 2 with no candidates: the stated systems are selected, so same agreement
    assert len(cg["per_system_pair"]) == 1
    agreed2 = [e["statement"] for e in cg["per_system_pair"][0]["agreed"]]
    assert agreed2 == ["Q(a)"]


def test_report_is_json_serializable():
    cg = crosscamp.common_ground(camps_shared_q())
    json.dumps(cg)
    assert crosscamp.to_jsonable(cg)["camps"] == ["A", "B"]


def test_three_camps_need_unanimity():
    a = make_camp("A", "da", TEXT_A, [("e1", "endorsed", "P(a)", "P(a) holds."),
                                      ("e2", "endorsed", "Q(a)", "Q(a) holds too.")])
    b = make_camp("B", "db", TEXT_B, [("e1", "endorsed", "Q(a)", "Q(a) holds."),
                                      ("e2", "endorsed", "R(a)", "R(a) holds.")])
    text_c = "C says: Q(a) holds."
    c = make_camp("C", "dc", text_c, [("e1", "endorsed", "Q(a)", "Q(a) holds.")])
    cg = crosscamp.common_ground([a, b, c])
    assert [e["statement"] for e in cg["stated"]["agreed"]] == ["Q(a)"]
    # every agreed statement carries one check per camp
    assert all(len(e["checks"]) == 3 for e in cg["stated"]["agreed"])


def test_stated_conflict_makes_the_union_inconsistent_and_agreement_empty():
    a = make_camp("A", "da", "A says: P(a) holds.", [("e1", "endorsed", "P(a)", "P(a) holds.")])
    b = make_camp("B", "db", "B says: not P(a).", [("e1", "rejected_firm", "P(a)", "not P(a).")])
    cg = crosscamp.common_ground([a, b])
    assert cg["stated"]["union_consistent"]["outcome"] == "fails"
    assert cg["stated"]["agreed"] == []
    assert cg["per_system_pair"][0]["agreed"] == []


C1 = "∀x (Human(x) → Mortal(x))"
TEXT_MORTAL_A = ("Socrates is human. Socrates is mortal. Plato is human. Plato is mortal. "
                 "Aristotle is human. Aristotle is mortal.")
TEXT_MORTAL_B = ("Socrates is human. Socrates is mortal. Plato is human. Plato is mortal.")


def camps_mortal():
    a = make_camp("A", "da", TEXT_MORTAL_A,
                  [("e1", "endorsed", "Human(socrates)", "Socrates is human."),
                   ("e2", "endorsed", "Mortal(socrates)", "Socrates is mortal."),
                   ("e3", "endorsed", "Human(plato)", "Plato is human."),
                   ("e4", "endorsed", "Mortal(plato)", "Plato is mortal."),
                   ("e5", "endorsed", "Human(aristotle)", "Aristotle is human."),
                   ("e6", "endorsed", "Mortal(aristotle)", "Aristotle is mortal.")],
                  candidates=[(C1, "Socrates is human.")],
                  plaus={fol.to_text(fol.parse(C1)): 0.9})
    b = make_camp("B", "db", TEXT_MORTAL_B,
                  [("e1", "endorsed", "Human(socrates)", "Socrates is human."),
                   ("e2", "endorsed", "Mortal(socrates)", "Socrates is mortal."),
                   ("e3", "endorsed", "Human(plato)", "Plato is human."),
                   ("e4", "endorsed", "Mortal(plato)", "Plato is mortal.")],
                  candidates=[(C1, "Plato is human.")],
                  plaus={fol.to_text(fol.parse(C1)): 0.9})
    return [a, b]


def test_reconstructed_tier_agrees_on_the_unstated_axiom_and_shows_derivations():
    cg = crosscamp.common_ground(camps_mortal())
    stated = {e["statement"] for e in cg["stated"]["agreed"]}
    assert stated == {"Human(socrates)", "Mortal(socrates)", "Human(plato)", "Mortal(plato)"}
    assert len(cg["per_system_pair"]) == 1
    pair = cg["per_system_pair"][0]
    agreed2 = {e["statement"] for e in pair["agreed"]}
    c1_text = fol.to_text(fol.parse(C1))
    assert c1_text in agreed2                    # both selected systems contain it as an axiom
    assert "Mortal(aristotle)" not in agreed2    # only camp A's record states it
    assert c1_text not in stated                 # tier 1 only ever covers stated claims
    by_text = {e["statement"]: e for e in pair["agreed"]}
    derivs = by_text["Mortal(socrates)"]["derivations"]
    assert derivs and all(set(d) <= set(pair["systems"][0]) | set(pair["systems"][1]) for d in derivs)
    assert any(c1_text in d and "Human(socrates)" in d for d in derivs)


@needs_lean
def test_common_ground_can_be_kernel_checked():
    cg = crosscamp.common_ground(camps_shared_q(), lean_bin=LEAN)
    badges = {c["badge"] for e in cg["stated"]["agreed"] for c in e["checks"]}
    assert abduce.BADGE_KERNEL in badges
