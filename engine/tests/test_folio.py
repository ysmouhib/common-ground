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
