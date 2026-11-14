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
