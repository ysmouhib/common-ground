"""Dataset handling, on synthetic rows. The dataset itself is fetched only by the benchmark."""
import json
import os
from pathlib import Path

import pytest

from commonground import bench, folio
from commonground.fol import ParseError
from commonground.verdict import decide


def example(premises, conclusion, label="True"):
    return folio.Example(0, ["-"] * len(premises), "-", premises, conclusion, label)


def test_surplus_closing_brackets_are_repaired_and_counted():
    assert folio.repair_brackets("P(a) ∧ Q(a))") == ("P(a) ∧ Q(a)", True)
    assert folio.repair_brackets("P(a) ∧ Q(a)") == ("P(a) ∧ Q(a)", False)
    assert folio.repair_brackets("P(a)) ∧ Q(a)")[1] is False  # not at the end: left alone, will fail to parse
    parsed = folio.parse_example(example(["P(a))"], "P(a)"))
    assert parsed.repaired_brackets == 1
    with pytest.raises(ParseError):
        folio.parse_example(example(["P(a))"], "P(a)"), repair=False)


def test_a_malformed_formula_is_reported_with_its_position():
    with pytest.raises(ParseError, match="premise 2"):
        folio.parse_example(example(["P(a)", "∀x (P(x), Q(x))"], "P(a)"))


def test_auto_scope_only_widens_when_a_variable_would_be_left_unbound():
    parsed = folio.parse_example(example(["∃x P(x) ∧ Q(x)", "∀x (P(x) → Q(x))"], "Q(a)"))
    assert parsed.wide_scope_used == 1 and parsed.closed_variables == 0


def test_unbound_variables_are_closed_universally():
    parsed = folio.parse_example(example(["P(x) → Q(x)", "P(a)"], "Q(a)"))
    assert parsed.closed_variables == 1
    assert decide(parsed.premises, parsed.conclusion).label == "True"


def test_labels_are_normalised(tmp_path):
    row = {"premises": ["a", "b"], "premises-FOL": ["P(a)", "Q(a)"], "conclusion": "c", "conclusion-FOL": "P(a)",
           "label": "Unknown"}
    path = tmp_path / "rows.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert folio.load(path)[0].label == "Uncertain"


def test_bracketing_ambiguity_ignores_pure_regrouping():
    assert bench.bracketing_ambiguous("A ∧ B ∨ C")
    assert not bench.bracketing_ambiguous("A ∧ B ∧ C")
    assert not bench.bracketing_ambiguous("(A ∧ B) ∨ C")


# --- CG8-1: hide-premise abduction benchmark (bench.abduction) ---


def dataset(tmp_path, rows):
    """A minimal fake FOLIO clone: <root>/data/v0.0/folio-validation.jsonl."""
    data = tmp_path / "data" / "v0.0"
    data.mkdir(parents=True)
    path = data / "folio-validation.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return tmp_path


def folio_row(premises_fol, conclusion_fol, label="True"):
    return {"premises": ["-"] * len(premises_fol), "premises-FOL": premises_fol,
            "conclusion": "-", "conclusion-FOL": conclusion_fol, "label": label}


def test_abduction_recovers_a_sufficient_premise_subset(tmp_path):
    root = dataset(tmp_path, [folio_row(["P(a)", "P(a) → Q(a)"], "Q(a)")])
    summary = bench.abduction(root / "data" / "v0.0" / "folio-validation.jsonl",
                              tmp_path / "out", timeout_ms=3000)
    assert summary["parsed"] == 1 and summary["recovered"] == 1
    assert summary["recovery_rate"] == 1.0 and summary["recovery_interval_95"]
    assert summary["search_incomplete"] == 0 and summary["pool_too_large"] == 0
    row = json.loads((tmp_path / "out" / "runs.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["recovered"] is True and row["min_recovered_size"] == 2
    assert row["reference_premises"] == 2 and row["search_complete"] is True
    assert row["badge"]  # every published verdict carries one


def test_abduction_marks_a_definite_negative_when_premises_do_not_entail(tmp_path):
    root = dataset(tmp_path, [folio_row(["P(a)"], "Q(a)", label="False")])
    summary = bench.abduction(root / "data" / "v0.0" / "folio-validation.jsonl",
                              tmp_path / "out", timeout_ms=3000)
    assert summary["recovered"] == 0 and summary["definite"] == 1
    assert summary["recovery_rate"] == 0.0


def test_abduction_parse_error_and_pool_cap_are_counted_not_crashed(tmp_path):
    rows = [folio_row(["P(a"], "Q(a)"),  # malformed
            folio_row([f"P(c{i})" for i in range(17)], "Q(c0)")]  # pool 18 > MAX_POOL
    root = dataset(tmp_path, rows)
    summary = bench.abduction(root / "data" / "v0.0" / "folio-validation.jsonl",
                              tmp_path / "out", timeout_ms=3000)
    assert summary["parsed"] == 1 and summary["pool_too_large"] == 1
    assert summary["definite"] == 0 and summary["recovery_rate"] is None


def test_abduction_cli_mode_end_to_end(tmp_path):
    from commonground.__main__ import main
    root = dataset(tmp_path, [folio_row(["P(a)", "P(a) → Q(a)"], "Q(a)")])
    out = tmp_path / "cli-out"
    code = main(["--timeout-ms", "3000", "folio", "--mode", "abduction", "--data", str(root),
                 "--out", str(out)])
    assert code == 0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["mode"] == "abduction" and summary["recovered"] == 1
    assert (out / "runs.jsonl").exists() and (out / "config.json").exists()


RESULTS = Path(__file__).resolve().parents[2] / "results" / "folio-validation" / "summary.json"
DATA = os.environ.get("FOLIO_DIR")


@pytest.mark.skipif(not DATA, reason="set FOLIO_DIR to a clone of the dataset to re-run the benchmark")
def test_published_results_are_reproduced(tmp_path):
    """Re-run the reference benchmark and compare with the committed summary, field by field."""
    from commonground import lean
    lean_bin = lean.find_lean()
    fresh = bench.reference(folio.fetch(Path(DATA)), tmp_path, lean_bin)
    published = json.loads(RESULTS.read_text(encoding="utf-8"))
    for key in ("parsing", "agreement_with_labels", "confusion_gold_then_verdict", "verdict_counts",
                "agreement_by_reading_convention", "disagreements"):
        assert fresh[key] == published[key], key
    assert fresh["second_engine"] == published["second_engine"]
    if lean_bin and published["lean"]:
        for key in ("entailment_verdicts", "certified_by_kernel", "false_statements_offered",
                    "false_statements_accepted"):
            assert fresh["lean"][key] == published["lean"][key], key
