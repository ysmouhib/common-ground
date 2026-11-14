import json
import pathlib

import pytest

from commonground import abduce, argmap, crosscamp, fol, lean
from commonground.__main__ import main

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


# --- CG5-3: fault lines (reduced disagreement) + CLI ---


def camps_conflict():
    a = make_camp("A", "da", "A says: P(a) holds.", [("e1", "endorsed", "P(a)", "P(a) holds.")])
    b = make_camp("B", "db", "B says: not P(a).", [("e1", "rejected_firm", "P(a)", "not P(a).")])
    return [a, b]


def test_stated_fault_line_on_firm_rejection_conflict():
    fl = crosscamp.fault_lines(camps_conflict())
    assert fl["stated"]["consistent"]["outcome"] == "fails"
    mus = fl["stated"]["mus"]
    assert len(mus) == 1 and set(mus[0]) == {"P(a)", "¬P(a)"}
    # MCSes are the complements of the maximal consistent subsets: give up one side
    assert any(set(m) == {"¬P(a)"} for m in fl["stated"]["mcs"])
    assert any(set(m) == {"P(a)"} for m in fl["stated"]["mcs"])
    pair = fl["per_system_pair"][0]
    assert pair["consistent"] is False
    assert any(set(m) == {"P(a)", "¬P(a)"} for m in pair["mus"])
    assert pair["root_divergence"] == []


def camps_disjoint():
    a = make_camp("A", "da", "A says: P(a) holds.", [("e1", "endorsed", "P(a)", "P(a) holds.")])
    b = make_camp("B", "db", "B says: R(a) holds.", [("e1", "endorsed", "R(a)", "R(a) holds.")])
    return [a, b]


def test_root_divergence_when_the_union_is_consistent():
    camps = camps_disjoint()
    cg = crosscamp.common_ground(camps)
    assert cg["stated"]["agreed"] == []          # neither camp entails the other's claim
    fl = crosscamp.fault_lines(camps)
    assert fl["stated"]["consistent"]["outcome"] == "holds"
    assert fl["stated"]["mus"] == []
    pair = fl["per_system_pair"][0]
    assert pair["consistent"] is True
    assert pair["mus"] == []
    roots = pair["root_divergence"]
    assert len(roots) == 1
    r = roots[0]
    assert {r["a1"], r["a2"]} == {"P(a)", "R(a)"}
    assert r["rank"] == 2                          # load 1 in each camp
    assert all(c["outcome"] == "holds" and c["model_where_claim_fails"] for c in r["checks"])


def test_analyze_combines_and_renders_json_and_markdown():
    report = crosscamp.analyze(camps_shared_q())
    assert set(report) == {"camps", "common_ground", "fault_lines"}
    json.dumps(report)
    md = crosscamp.render_markdown(report)
    assert "Common ground among stated claims" in md
    assert "`Q(a)`" in md
    assert "Fault lines" in md


def test_combination_cap_raises_too_many(monkeypatch):
    monkeypatch.setattr(crosscamp, "MAX_COMBINATIONS", 0)
    with pytest.raises(argmap.TooMany):
        crosscamp.common_ground(camps_shared_q())


def write_record_file(path, camp, doc_id, text, statements):
    def span_of(sub):
        i = text.index(sub)
        return [i, i + len(sub)]
    record = {"camp": camp, "documents": [{"id": doc_id, "text": text}],
              "statements": [{"id": sid, "stance": stance, "fol": f, "document": doc_id,
                              "quote": q, "span": span_of(q)}
                             for sid, stance, f, q in statements]}
    path.write_text(json.dumps(record), encoding="utf-8")


def test_cli_crosscamp_end_to_end(tmp_path):
    ra = tmp_path / "a.json"
    rb = tmp_path / "b.json"
    ca = tmp_path / "ca.json"
    cb = tmp_path / "cb.json"
    write_record_file(ra, "A", "da", TEXT_A,
                      [("e1", "endorsed", "P(a)", "P(a) holds."),
                       ("e2", "endorsed", "Q(a)", "Q(a) holds too.")])
    write_record_file(rb, "B", "db", TEXT_B,
                      [("e1", "endorsed", "Q(a)", "Q(a) holds."),
                       ("e2", "endorsed", "R(a)", "R(a) holds.")])
    ca.write_text(json.dumps({"candidates": []}), encoding="utf-8")
    cb.write_text(json.dumps({"candidates": []}), encoding="utf-8")
    out = tmp_path / "out"
    code = main(["crosscamp", str(ra), str(rb), "--candidates", str(ca), str(cb),
                 "--out", str(out)])
    assert code == 0
    result = json.loads((out / "crosscamp.json").read_text(encoding="utf-8"))
    assert result["camps"] == ["A", "B"]
    assert [e["statement"] for e in result["common_ground"]["stated"]["agreed"]] == ["Q(a)"]
    assert (out / "A" / "report.json").exists() and (out / "B" / "report.md").exists()
    assert "crosscamp.md" in [p.name for p in out.iterdir()]
    assert pathlib.Path(out / "crosscamp.md").read_text(encoding="utf-8").startswith("# Cross-camp")
