import json

import pytest

from commonground import abduce, fol
from commonground.__main__ import main

DOCX = "Socrates is human. Socrates is mortal. Plato is human. Plato is mortal. Socrates does not fly."


def span_of(sub):
    i = DOCX.index(sub)
    return [i, i + len(sub)]


def write_record(path, statements):
    record = {"camp": "campX",
              "documents": [{"id": "dx", "text": DOCX}],
              "statements": statements}
    path.write_text(json.dumps(record), encoding="utf-8")


def good_statements():
    def st(sid, stance, fol_text, quote):
        return {"id": sid, "stance": stance, "fol": fol_text, "document": "dx",
                "quote": quote, "span": span_of(quote)}
    return [st("e1", "endorsed", "Human(socrates)", "Socrates is human."),
            st("e2", "endorsed", "Mortal(socrates)", "Socrates is mortal."),
            st("e3", "endorsed", "Human(plato)", "Plato is human."),
            st("e4", "endorsed", "Mortal(plato)", "Plato is mortal."),
            st("s1", "rejected_soft", "Flies(socrates)", "Socrates does not fly.")]


C1 = "∀x (Human(x) → Mortal(x))"


def candidates_file(path, fols=None):
    fols = fols if fols is not None else [(C1, "Socrates is human.")]
    cands = [{"fol": f, "quotes": [{"document": "dx", "text": q, "span": span_of(q)}]}
             for f, q in fols]
    path.write_text(json.dumps({"candidates": cands}), encoding="utf-8")


def test_report_camp_selects_the_unstated_system_and_reports_load():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmp:
        rp = pathlib.Path(tmp) / "record.json"
        write_record(rp, good_statements())
        record = abduce.load_record(str(rp))
    src = abduce.ScriptedSource([abduce.Candidate(C1, [("dx", "Socrates is human.", tuple(span_of("Socrates is human.")))])])
    plaus = {fol.to_text(fol.parse(C1)): 0.9}
    report = abduce.report_camp(record, src, plaus, lam=0.3)
    assert len(report["systems"]) == 1
    system = report["systems"][0]
    assert system["certified"]
    assert fol.to_text(fol.parse(C1)) in system["axioms"]
    loads = {row["axiom"]: row["load"] for row in system["load"]}
    assert loads[fol.to_text(fol.parse(C1))] == 2
    assert report["hull"] and report["margin_to_runner_up"] is not None
    assert report["baseline"]["stated_certified"]
    assert report["abstention"] is False
    assert report["coverage"] is None
    assert report["systems"][0]["negative_controls"]["all_passed"]
    md = abduce.render_markdown(report)
    assert "verified sufficient" in md and "SOLVER-CHECKED" in md
    for forbidden in ("probability", "central", "core belief", "warrant"):
        assert forbidden not in md.lower()


def test_report_drops_a_candidate_that_duplicates_a_stated_claim():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmp:
        rp = pathlib.Path(tmp) / "record.json"
        write_record(rp, good_statements())
        record = abduce.load_record(str(rp))
    dup = abduce.Candidate("Human(socrates)",
                           [("dx", "Socrates is human.", tuple(span_of("Socrates is human.")))])
    report = abduce.report_camp(record, abduce.ScriptedSource([dup]), {}, lam=0.3)
    assert report["pool"]["candidates"] == []
    assert any(d["reason"] == "duplicate of a stated claim" for d in report["pool"]["dropped"])
    assert report["abstention"] is True  # selection unchanged: the stated copy has p = 1


def test_report_abstention_when_no_candidate_is_proposed():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmp:
        rp = pathlib.Path(tmp) / "record.json"
        write_record(rp, good_statements())
        record = abduce.load_record(str(rp))
    report = abduce.report_camp(record, abduce.ScriptedSource([]), {}, lam=0.3)
    assert report["abstention"] is True
    assert len(report["systems"]) == 1  # the stated system A0
    assert "Abstention" in abduce.render_markdown(report)


def test_report_coverage_when_no_axiom_system_exists():
    import tempfile, pathlib
    stmts = good_statements() + [
        {"id": "bad", "stance": "endorsed", "fol": "P(a) ∧ ¬P(a)", "document": "dx",
         "quote": "Socrates is human.", "span": span_of("Socrates is human.")}]
    with tempfile.TemporaryDirectory() as tmp:
        rp = pathlib.Path(tmp) / "record.json"
        write_record(rp, stmts)
        record = abduce.load_record(str(rp))
    report = abduce.report_camp(record, abduce.ScriptedSource([]), {}, lam=0.3)
    assert report["systems"] == []
    assert report["coverage"] is not None and report["coverage"]["kappa"] < 1.0
    assert "cannot all hold together" in abduce.render_markdown(report)


def test_cli_camp_writes_report_json_and_md(tmp_path, capsys):
    rp = tmp_path / "record.json"
    write_record(rp, good_statements())
    cp = tmp_path / "candidates.json"
    candidates_file(cp)
    out = tmp_path / "out"
    code = main(["camp", str(rp), "--candidates", str(cp), "--lam", "0.3", "--out", str(out)])
    assert code == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["camp"] == "campX" and len(report["systems"]) == 1
    assert (out / "report.md").read_text(encoding="utf-8").startswith("# Camp `campX`")


# --- soundness review 2026-11-14: what the report may and may not say ----------

from commonground import lean

LEAN = lean.find_lean()
needs_lean = pytest.mark.skipif(LEAN is None, reason="no Lean 4.35.0 (set LEAN_BIN)")
C1T = fol.to_text(fol.parse(C1))


def record_of(statements):
    return abduce.record_from_json({"camp": "campX", "documents": [{"id": "dx", "text": DOCX}],
                                    "statements": statements})


def st(sid, stance, fol_text, quote):
    return {"id": sid, "stance": stance, "fol": fol_text, "document": "dx", "quote": quote, "span": span_of(quote)}


def c1_source():
    return abduce.ScriptedSource([abduce.Candidate(C1, [("dx", "Socrates is human.", tuple(span_of("Socrates is human.")))])])


def test_a_search_stopped_by_the_budget_is_reported_incomplete_never_as_abstention():
    record = record_of(good_statements())
    full = abduce.report_camp(record, c1_source(), {C1T: 0.9}, lam=0.3)
    assert full["search_complete"] and full["hull_complete"] and full["abstention"] is False
    capped = abduce.report_camp(record, c1_source(), {C1T: 0.9}, lam=0.3, max_checks=1)
    # one check: the stated system is certified, but nothing shows it is the cheapest
    assert capped["selection"]["exhausted"] and capped["search_complete"] is False
    assert capped["systems"] and capped["systems"][0]["certified"]
    assert capped["abstention"] is None and capped["hull_complete"] is False
    md = abduce.render_markdown(capped)
    assert "SEARCH INCOMPLETE" in md and "PARTIAL" in md
    assert "cost-minimal, ties reported" not in md
    assert "No proposed unstated axiom pays for itself" not in md
    assert "each system optimal on its interval" not in md
    # the complete report still says what it said
    full_md = abduce.render_markdown(full)
    assert "cost-minimal, ties reported" in full_md and "SEARCH INCOMPLETE" not in full_md


def test_branch_and_bound_hull_is_labelled_partial():
    # 13 pool items: report_camp switches to branch-and-bound, whose pruning skips systems that
    # cost more at this λ — so its hull cannot claim intervals for other values of λ
    people = ["socrates", "plato", "aristotle", "zeno", "thales", "solon"]
    text = " ".join(f"{p} is human. {p} is mortal." for p in people)
    statements = []
    for p in people:
        for pred, word in (("Human", "human"), ("Mortal", "mortal")):
            quote = f"{p} is {word}."
            i = text.index(quote)
            statements.append({"id": f"{pred}-{p}", "stance": "endorsed", "fol": f"{pred}({p})",
                               "document": "dp", "quote": quote, "span": [i, i + len(quote)]})
    record = abduce.record_from_json({"camp": "campP", "documents": [{"id": "dp", "text": text}],
                                      "statements": statements})
    quote = "socrates is human."
    everyone = "∀x (Human(x) ∧ Mortal(x))"   # one axiom that entails all twelve claims
    source = abduce.ScriptedSource([abduce.Candidate(everyone, [("dp", quote, (text.index(quote), text.index(quote) + len(quote)))])])
    report = abduce.report_camp(record, source, {everyone: 0.9}, lam=0.3)
    assert report["search"] == "branch-and-bound" and report["search_complete"]
    assert report["selection"]["systems"] == [[fol.to_text(fol.parse(everyone))]] and report["abstention"] is False
    assert report["hull_complete"] is False
    md = abduce.render_markdown(report)
    assert "Hull over λ — PARTIAL" in md and "each system optimal on its interval" not in md
    assert "cost-minimal, ties reported" in md   # the selection itself is established


def test_brute_force_is_chosen_exactly_when_the_budget_covers_every_subset():
    # the hull is complete only after a full enumeration, so the strategy follows the check
    # budget, not a fixed pool size: this pool has 5 items = 32 subsets
    record = record_of(good_statements())
    full = abduce.report_camp(record, c1_source(), {C1T: 0.9}, lam=0.3, max_checks=32)
    assert full["search"] == "bruteforce" and full["search_complete"] and full["hull_complete"]
    capped = abduce.report_camp(record, c1_source(), {C1T: 0.9}, lam=0.3, max_checks=31)
    assert capped["search"] == "branch-and-bound"


def test_pending_is_not_reported_as_no_axiom_system():
    statements = good_statements()
    statements[1]["fol"] = None   # e2 has no reviewed formalization yet
    report = abduce.report_camp(record_of(statements), abduce.ScriptedSource([]), {}, lam=0.3)
    assert report["systems"] == []
    assert report["existence"]["status"] == "pending" and report["existence"]["unformalized"] == ["e2"]
    md = abduce.render_markdown(report)
    assert "PENDING, not a finding that none exists" in md
    assert "No axiom system exists" not in md and "cannot all hold together" not in md


def test_no_axiom_system_because_a_soft_rejection_is_entailed():
    statements = good_statements() + [st("s2", "rejected_soft", "Mortal(plato)", "Plato is mortal.")]
    report = abduce.report_camp(record_of(statements), abduce.ScriptedSource([]), {}, lam=0.3)
    assert report["systems"] == []
    assert report["existence"]["status"] == "none"
    assert report["existence"]["reason"] == "soft_rejection_entailed"
    assert report["existence"]["soft_rejections"] == ["s2"]
    md = abduce.render_markdown(report)
    assert "No axiom system exists" in md
    assert "cannot all hold together" not in md   # the stated claims are consistent: κ = 1
    assert report["coverage"]["kappa"] == 1.0 and report["coverage"]["minimal_conflicts"] == []


def test_inconsistent_record_names_its_reason():
    statements = good_statements() + [st("bad", "endorsed", "P(a) ∧ ¬P(a)", "Socrates is human.")]
    report = abduce.report_camp(record_of(statements), abduce.ScriptedSource([]), {}, lam=0.3)
    assert report["existence"]["status"] == "none" and report["existence"]["reason"] == "inconsistent"
    assert "No axiom system exists" in abduce.render_markdown(report)


def test_no_verdict_during_the_search_is_pending_and_does_not_crash(monkeypatch):
    # the solver (the dependency) answers nothing: no system, no "none exists", no exception
    monkeypatch.setattr(abduce._verdict, "satisfiable",
                        lambda *a, **k: abduce._verdict.SatAnswer("unknown", note="forced"))
    report = abduce.report_camp(record_of(good_statements()), abduce.ScriptedSource([]), {}, lam=0.3)
    assert report["systems"] == [] and report["existence"]["status"] == "pending"
    assert "pending" in report["coverage"]
    md = abduce.render_markdown(report)
    assert "No axiom system exists" not in md and "PENDING" in md


def test_a_record_of_valid_claims_has_the_empty_system():
    # the drinker formula holds in every structure: nothing is needed to entail it (THEORY.md §2,
    # condition 4), which is an axiom system — not "no axiom system exists"
    statements = [st("e1", "endorsed", "∃x (D(x) → ∀y D(y))", "Socrates is human.")]
    report = abduce.report_camp(record_of(statements), abduce.ScriptedSource([]), {}, lam=0.3)
    assert report["selection"]["systems"] == [[]] and report["selection"]["best_cost"] == 0
    assert report["systems"][0]["certified"] and report["existence"]["status"] == "certified"
    assert report["systems"][0]["negative_controls"]["all_passed"]
    assert "every stated claim is valid on its own" in abduce.render_markdown(report)


def test_headline_badge_needs_every_entailment_kernel_checked():
    K, S = abduce.BADGE_KERNEL, abduce.BADGE_SOLVER

    def checks(sufficiency, firm=()):
        return {"sufficiency": [{"badge": b} for b in sufficiency],
                "firm_rejections": [{"badge": b} for b in firm]}

    assert abduce.system_badge(checks([K, K], [K]), True) == K
    assert abduce.system_badge(checks([K, S]), True) == "SOLVER-CHECKED (1 of 2 entailments kernel-checked)"
    assert abduce.system_badge(checks([K, K], [S]), True) == "SOLVER-CHECKED (2 of 3 entailments kernel-checked)"
    assert abduce.system_badge(checks([S, S]), True) == S
    assert abduce.system_badge(checks([]), True) == S
    assert abduce.system_badge(checks([K, K]), False) == "NOT CERTIFIED"


def test_markdown_headline_of_an_uncertified_system_says_so():
    report = abduce.report_camp(record_of(good_statements()), c1_source(), {C1T: 0.9}, lam=0.3)
    system = report["systems"][0]
    assert system["badge"] == abduce.BADGE_SOLVER and f"— {abduce.BADGE_SOLVER}" in abduce.render_markdown(report)
    system.update(certified=False, badge=abduce.system_badge(system["checks"], False))
    md = abduce.render_markdown(report)
    assert "— NOT CERTIFIED" in md and "It is not certified." in md
    # a report written before the badge field existed is rendered by the same rule
    del system["badge"]
    system["checks"]["sufficiency"][0]["badge"] = abduce.BADGE_KERNEL
    system["certified"] = True
    headline = [line for line in abduce.render_markdown(report).splitlines() if line.startswith("### System")]
    assert headline == [f"### System 1 — cost {system['cost']:.4f} — "
                        f"SOLVER-CHECKED (1 of {len(system['checks']['sufficiency'])} entailments kernel-checked)"]


@needs_lean
def test_kernel_headline_only_when_every_claim_is_kernel_checked():
    # Z3 refutes the negation of the drinker formula; whether Lean's tactic proves it is up to
    # the toolchain — either way the headline must follow the per-check badges
    statements = [st("e1", "endorsed", "Human(socrates)", "Socrates is human."),
                  st("e2", "endorsed", "∃x (D(x) → ∀y D(y))", "Socrates is mortal.")]
    report = abduce.report_camp(record_of(statements), abduce.ScriptedSource([]), {}, lam=0.3, lean_bin=LEAN)
    system = report["systems"][0]
    badges = [c["badge"] for c in system["checks"]["sufficiency"]]
    assert system["certified"] and abduce.BADGE_KERNEL in badges
    all_kernel = all(b == abduce.BADGE_KERNEL for b in badges)
    assert (system["badge"] == abduce.BADGE_KERNEL) == all_kernel
    headline = [line for line in abduce.render_markdown(report).splitlines() if line.startswith("### System")][0]
    assert ("SUFFICIENT (kernel-checked)" in headline) == all_kernel
    kernel_checks = [c for c in system["checks"]["sufficiency"] if c["badge"] == abduce.BADGE_KERNEL]
    assert all(c["certificate"]["lean_source"] for c in kernel_checks)


def test_a_stated_claim_is_never_charged_and_defaults_are_reported():
    dup = abduce.Candidate("Human(socrates)", [("dx", "Socrates is human.", tuple(span_of("Socrates is human.")))])
    source = abduce.ScriptedSource([dup] + c1_source().candidates)
    report = abduce.report_camp(record_of(good_statements()), source, {"Human(socrates)": 0.6}, lam=0.3)
    # the estimate that came with the duplicate is not applied to the stated copy (p = 1) ...
    assert report["plausibility"]["ignored_for_stated"] == {"Human(socrates)": 0.6}
    # ... and the unscored candidate's 0.5 is a default the report names
    assert report["plausibility"]["defaulted"] == [C1T]
    assert [(c["plausibility"], c["plausibility_source"]) for c in report["pool"]["candidates"]] == [(0.5, "default")]
    # four stated claims at λ = 0.3 cost 1.2; with the default the candidate system costs 1.4
    assert report["selection"]["best_cost"] == pytest.approx(1.2) and report["abstention"] is True
    md = abduce.render_markdown(report)
    assert "default: nobody scored it" in md and "are not applied" in md


def test_plausibility_keys_match_in_any_spelling_and_must_be_formulas():
    record = record_of(good_statements())
    report = abduce.report_camp(record, c1_source(), {"∀x (Human(x) -> Mortal(x))": 0.9}, lam=0.3)
    assert C1T in report["selection"]["systems"][0] and report["plausibility"]["defaulted"] == []
    with pytest.raises(ValueError, match="not a formula"):
        abduce.report_camp(record, c1_source(), {"Human((x": 0.9}, lam=0.3)
    with pytest.raises(ValueError, match=r"in \[0, 1\]"):
        abduce.report_camp(record, c1_source(), {C1T: 7.5}, lam=0.3)
    with pytest.raises(ValueError, match="positive"):
        abduce.report_camp(record, c1_source(), {C1T: 0.9}, lam=-1)


def test_two_statements_with_the_same_formula_are_one_claim():
    statements = good_statements() + [st("e5", "endorsed", "Human(socrates)", "Socrates is human.")]
    report = abduce.report_camp(record_of(statements), abduce.ScriptedSource([]), {}, lam=0.3)
    assert len(report["selection"]["systems"]) == 1          # not the same system twice as a "tie"
    assert len(report["selection"]["systems"][0]) == len(set(report["selection"]["systems"][0])) == 4
    assert report["margin_to_runner_up"] is None             # one certified system: no runner-up
    assert [h["size"] for h in report["hull"]] == [4]


def test_a_name_no_quantifier_binds_is_reported_as_a_warning():
    statements = good_statements() + [st("e5", "endorsed", "∀x Human(x) → Mortal(x)", "Plato is human.")]
    report = abduce.report_camp(record_of(statements), abduce.ScriptedSource([]), {}, lam=0.3, max_checks=1)
    assert any("statement e5" in w and "read as a constant" in w for w in report["warnings"])
    assert "## Warnings" in abduce.render_markdown(report)
    clean = abduce.report_camp(record_of(good_statements()), abduce.ScriptedSource([]), {}, lam=0.3, max_checks=1)
    assert clean["warnings"] == []


def run_camp_cli(tmp_path, record=None, candidates=None, extra=()):
    rp, cp = tmp_path / "record.json", tmp_path / "candidates.json"
    rp.write_text(json.dumps(record if record is not None else
                             {"camp": "campX", "documents": [{"id": "dx", "text": DOCX}],
                              "statements": good_statements()}), encoding="utf-8")
    cp.write_text(json.dumps(candidates if candidates is not None else {"candidates": []}), encoding="utf-8")
    return main(["camp", str(rp), "--candidates", str(cp), "--out", str(tmp_path / "out"), *extra])


def bad_record(**changes):
    statement = {**good_statements()[0], **changes}
    return {"camp": "campX", "documents": [{"id": "dx", "text": DOCX}], "statements": [statement]}


@pytest.mark.parametrize("kwargs, message", [
    ({"record": bad_record(quote="Socrates is humans")}, "does not match"),
    ({"record": bad_record(fol="Human((socrates)")}, "does not parse"),
    ({"record": bad_record(span=["0", "18"])}, "two integers"),
    ({"record": bad_record(span=[0.0, 18.0])}, "two integers"),
    ({"record": bad_record(fol=5)}, "must be a formula"),
    ({"record": bad_record(fol="")}, "must be a formula"),
    ({"record": {"camp": "campX", "documents": [], "statements": "oops"}}, "must be lists"),
    ({"record": ["not", "an", "object"]}, "JSON object"),
    ({"candidates": {"candidates": ["P(a)"]}}, "must be an object"),
    ({"candidates": {"candidates": [{"fol": f"P{i}(a)", "quotes": []} for i in range(41)]}}, "at most 40"),
    ({"extra": ("--lam", "-1")}, "positive"),
    ({"extra": ("--lam", "0")}, "positive"),
])
def test_cli_refuses_bad_input_with_a_message_not_a_traceback(tmp_path, capsys, kwargs, message):
    assert run_camp_cli(tmp_path, **kwargs) == 2
    assert message in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_cli_refuses_plausibilities_outside_the_unit_interval(tmp_path, capsys):
    pp = tmp_path / "plaus.json"
    pp.write_text(json.dumps({C1: 7.5}), encoding="utf-8")
    assert run_camp_cli(tmp_path, extra=("--plausibilities", str(pp))) == 2
    assert "in [0, 1]" in capsys.readouterr().err
    pp.write_text(json.dumps([0.5]), encoding="utf-8")
    assert run_camp_cli(tmp_path, extra=("--plausibilities", str(pp))) == 2


def test_cli_lean_requested_but_absent_is_an_error_not_a_silent_downgrade(tmp_path, capsys, monkeypatch):
    import commonground.__main__ as cli
    monkeypatch.setattr(cli.lean, "find_lean", lambda: None)
    assert run_camp_cli(tmp_path, extra=("--lean",)) == 2
    assert "no Lean" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_cli_summary_line_says_whether_the_search_finished(tmp_path, capsys):
    cands = {"candidates": [{"fol": C1, "quotes": [{"document": "dx", "text": "Socrates is human.",
                                                     "span": span_of("Socrates is human.")}]}]}
    assert run_camp_cli(tmp_path, candidates=cands, extra=("--max-checks", "1")) == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["search_complete"] is False and summary["abstention"] is None


# --- CG8-4: plausibility ranges and selection sensitivity ---


def camp_with_candidate():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmp:
        rp = pathlib.Path(tmp) / "record.json"
        write_record(rp, good_statements())
        record = abduce.load_record(str(rp))
    src = abduce.ScriptedSource([abduce.Candidate(C1, [("dx", "Socrates is human.",
                                                         tuple(span_of("Socrates is human.")))])])
    return record, src


def test_plausibility_range_that_changes_the_selection_is_reported():
    # C1 replaces 2 stated claims: preferred when p > 1 − λ = 0.7 at λ = 0.3, so the range
    # [0.4, 0.9] straddles the threshold — the selection must change between min and max
    record, src = camp_with_candidate()
    report = abduce.report_camp(record, src, {C1T: [0.4, 0.9]}, lam=0.3)
    sens = report["plausibility_sensitivity"]
    assert sens and sens["ranges"] == {C1T: [0.4, 0.9]}
    assert sens["at_min"]["search_complete"] and sens["at_max"]["search_complete"]
    assert C1T not in {a for s in sens["at_min"]["systems"] for a in s}
    assert any(C1T in s for s in sens["at_max"]["systems"])
    assert sens["stable"] is False
    md = abduce.render_markdown(report)
    assert "Plausibility sensitivity" in md and "changes" in md


def test_plausibility_range_that_keeps_the_selection_is_stable():
    record, src = camp_with_candidate()
    report = abduce.report_camp(record, src, {C1T: [0.8, 0.95]}, lam=0.3)
    sens = report["plausibility_sensitivity"]
    assert sens["stable"] is True
    assert "stable" in abduce.render_markdown(report)


def test_point_estimates_have_no_sensitivity_section():
    record, src = camp_with_candidate()
    report = abduce.report_camp(record, src, {C1T: 0.9}, lam=0.3)
    assert report["plausibility_sensitivity"] is None


def test_invalid_plausibility_ranges_are_errors():
    record, src = camp_with_candidate()
    with pytest.raises(ValueError, match="min > max"):
        abduce.report_camp(record, src, {C1T: [0.9, 0.4]}, lam=0.3)
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        abduce.report_camp(record, src, {C1T: [-0.1, 0.5]}, lam=0.3)
    with pytest.raises(ValueError, match="not a formula"):
        abduce.report_camp(record, src, {"not a formula": 0.5}, lam=0.3)
