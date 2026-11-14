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
    assert set(report) == {"camps", "search_incomplete", "common_ground", "fault_lines"}
    assert report["search_incomplete"] == []
    json.dumps(report)
    md = crosscamp.render_markdown(report)
    assert "Search incomplete" not in md
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


# --- soundness review 2026-11-14: one regression test per hole that was found ----------

from commonground import verdict

NO_VERDICT = verdict.SatAnswer("unknown", note="forced")


def inconsistent_and_other():
    # camp A contradicts itself and firmly rejects Q(a); camp B endorses Q(a)
    a = make_camp("A", "da", "A says: P(a) holds. A says: not P(a). A says: Z(a) is false.",
                  [("e1", "endorsed", "P(a)", "P(a) holds."),
                   ("e2", "endorsed", "¬P(a)", "not P(a)."),
                   ("r1", "rejected_firm", "Q(a)", "Z(a) is false.")])
    b = make_camp("B", "db", "B says: Q(a) holds.", [("e1", "endorsed", "Q(a)", "Q(a) holds.")])
    return [a, b]


def test_an_inconsistent_camp_gives_no_vacuous_common_ground():
    camps = inconsistent_and_other()
    cg = crosscamp.common_ground(camps)
    # everything follows from A's contradiction, Q(a) included — which A firmly rejects
    assert cg["stated"]["agreed"] == []
    assert cg["stated"]["vacuous_camps"] == ["A"] and cg["stated"]["pending_camps"] == []
    assert [c["outcome"] for c in cg["stated"]["camp_consistency"]] == ["fails", "holds"]
    md = crosscamp.render_markdown(crosscamp.analyze(camps))
    assert "vacuously" in md and "| agreed statement |" not in md


@needs_lean
def test_the_kernel_does_not_turn_a_vacuous_agreement_into_common_ground():
    # Lean proves Q(a) from P(a) and ¬P(a) without complaint: the consistency gate is what refuses it
    cg = crosscamp.common_ground(inconsistent_and_other(), lean_bin=LEAN)
    assert cg["stated"]["agreed"] == []


def test_the_stated_tier_lists_reviewed_statements_only():
    a = make_camp("A", "da", "A says: P(a) holds.", [("e1", "endorsed", "P(a)", "P(a) holds.")],
                  candidates=[("P(a) ∨ Z(a)", "P(a) holds.")])
    b = make_camp("B", "db", "B says: P(a) holds as well.", [("e1", "endorsed", "P(a)", "P(a) holds as well.")])
    cg = crosscamp.common_ground([a, b])
    # both E⁺ entail the candidate, but it is nobody's stated claim: tier 2 is where it belongs
    assert [e["statement"] for e in cg["stated"]["agreed"]] == ["P(a)"]
    assert cg["stated"]["pool"] == ["P(a)"]
    assert "(P(a) ∨ Z(a))" in {e["statement"] for e in cg["per_system_pair"][0]["agreed"]}


def camps_partly_formalized():
    a = make_camp("A", "da", "A says: P(a) holds. A also says something not yet formalized.",
                  [("e1", "endorsed", "P(a)", "P(a) holds."),
                   ("e2", "endorsed", None, "A also says something not yet formalized.")])
    b = make_camp("B", "db", "B says: not P(a), in words only. B says: R(a) holds.",
                  [("e1", "endorsed", None, "not P(a), in words only."),
                   ("e2", "endorsed", "R(a)", "R(a) holds.")])
    return [a, b]


def test_unformalized_statements_leave_consistency_and_fault_lines_pending():
    report = crosscamp.analyze(camps_partly_formalized())
    stated = report["common_ground"]["stated"]
    assert stated["union_consistent"]["outcome"] == "pending"
    assert stated["union_consistent"]["badge"] == abduce.BADGE_PENDING
    assert {(u["camp"], u["id"]) for u in stated["unformalized"]} == {("A", "e2"), ("B", "e1")}
    fl = report["fault_lines"]["stated"]
    assert fl["consistent"]["outcome"] == "pending" and fl["complete"] is False and fl["mus"] == []
    md = crosscamp.render_markdown(report)
    assert "The stated claims are jointly consistent" not in md
    assert "No conflict among the formalized stated claims. PENDING" in md
    assert "Union of the camps' stated E⁺ is consistent: **pending**" in md


def test_a_conflict_among_formalized_statements_stands_whatever_is_unformalized():
    a = make_camp("A", "da", "A says: P(a) holds. A also says more.",
                  [("e1", "endorsed", "P(a)", "P(a) holds."), ("e2", "endorsed", None, "A also says more.")])
    b = make_camp("B", "db", "B says: not P(a).", [("e1", "rejected_firm", "P(a)", "not P(a).")])
    report = crosscamp.analyze([a, b])
    fl = report["fault_lines"]["stated"]
    assert fl["consistent"]["outcome"] == "fails"          # adding statements cannot remove it
    assert [set(m) for m in fl["mus"]] == [{"P(a)", "¬P(a)"}] and fl["complete"] is False
    assert "the list may be incomplete" in crosscamp.render_markdown(report)


def test_no_verdict_stays_pending_in_fault_lines_and_common_ground(monkeypatch):
    camps = camps_disjoint()            # built with the real solver, then the solver stops answering
    monkeypatch.setattr(verdict, "satisfiable", lambda *a, **k: NO_VERDICT)
    fl = crosscamp.fault_lines(camps)
    assert fl["stated"]["mus"] is None and fl["stated"]["mcs"] is None and "pending" in fl["stated"]
    assert fl["stated"]["consistent"]["outcome"] == "pending" and fl["stated"]["complete"] is False
    pair = fl["per_system_pair"][0]
    assert pair["mus"] is None and pair["consistent"] is None and "pending" in pair
    assert pair["root_divergence"] == []                    # nothing published without a verdict
    cg = crosscamp.common_ground(camps)
    assert cg["stated"]["agreed"] == [] and cg["stated"]["pending_camps"] == ["A", "B"]
    assert cg["stated"]["union_consistent"]["outcome"] == "pending"
    assert cg["per_system_pair"][0]["agreed"] == []
    md = crosscamp.render_markdown({"camps": ["A", "B"], "common_ground": cg, "fault_lines": fl})
    assert "jointly consistent" not in md and "Pending: no verdict" in md
    assert "Stated common ground is PENDING" in md


def test_a_root_divergence_pair_without_verdict_is_listed_as_pending(monkeypatch):
    camps = camps_disjoint()
    undecided = verdict.Verdict("Undecided", None, notes=["forced"])
    monkeypatch.setattr(verdict, "decide", lambda *a, **k: undecided)   # satisfiability still answers
    pair = crosscamp.fault_lines(camps)["per_system_pair"][0]
    assert pair["consistent"] is True and pair["root_divergence"] == []
    assert [(p["a1"], p["a2"], p["pending"]) for p in pair["root_divergence_pending"]] == [
        ("P(a)", "R(a)", "non-entailment undecided")]


def test_an_axiom_whose_load_has_no_verdict_is_not_dropped_from_root_divergence():
    camps = camps_disjoint()
    camps[0].report["systems"][0]["load"] = [{"axiom": "P(a)", "load": 0, "pending": 1}]
    pair = crosscamp.fault_lines(camps)["per_system_pair"][0]
    assert pair["root_divergence"] == []
    assert [p["pending"] for p in pair["root_divergence_pending"]] == ["load not established"]
    md = crosscamp.render_markdown({"camps": ["A", "B"], "common_ground": crosscamp.common_ground(camps),
                                    "fault_lines": crosscamp.fault_lines(camps)})
    assert "1 further axiom pair(s) are PENDING" in md


def test_two_camps_with_the_same_name_are_refused():
    a, b = camps_shared_q()
    b.record.camp = "A"
    with pytest.raises(ValueError, match="unique"):
        crosscamp.common_ground([a, b])
    with pytest.raises(ValueError, match="unique"):
        crosscamp.fault_lines([a, b])


def cli_two_camps(tmp_path, camp_a="A", camp_b="B", extra=()):
    ra, rb, ca = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "c.json"
    write_record_file(ra, camp_a, "da", TEXT_A, [("e1", "endorsed", "P(a)", "P(a) holds.")])
    write_record_file(rb, camp_b, "db", TEXT_B, [("e1", "endorsed", "Q(a)", "Q(a) holds.")])
    ca.write_text(json.dumps({"candidates": []}), encoding="utf-8")
    out = tmp_path / "deep" / "out"
    return main(["crosscamp", str(ra), str(rb), "--candidates", str(ca), str(ca), "--out", str(out), *extra]), out


@pytest.mark.parametrize("name", ["../escaped", "..", "sub/dir", "C:\\elsewhere", "a:b", " padded", "dot."])
def test_cli_refuses_a_camp_name_that_is_not_a_plain_directory_name(tmp_path, capsys, name):
    code, out = cli_two_camps(tmp_path, camp_a=name)
    assert code == 2 and "cannot be used as a directory name" in capsys.readouterr().err
    # nothing was written, inside the output directory or beside it
    assert not out.exists() and not (tmp_path / "deep").exists() and not (tmp_path / "escaped").exists()


def test_cli_refuses_two_records_of_the_same_camp(tmp_path, capsys):
    code, out = cli_two_camps(tmp_path, camp_a="A", camp_b="A")
    assert code == 2 and "unique" in capsys.readouterr().err and not out.exists()


def test_cli_crosscamp_summary_reports_each_search(tmp_path, capsys):
    code, out = cli_two_camps(tmp_path, extra=("--max-checks", "1"))
    assert code == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["search_complete"] == {"A": False, "B": False}
    assert "SEARCH INCOMPLETE" in (out / "A" / "report.md").read_text(encoding="utf-8")
    # the comparison of systems that are not shown to be cost-minimal is labelled provisional
    result = json.loads((out / "crosscamp.json").read_text(encoding="utf-8"))
    assert result["search_incomplete"] == ["A", "B"]
    md = (out / "crosscamp.md").read_text(encoding="utf-8")
    assert "Search incomplete for `A`, `B`" in md and "provisional" in md
