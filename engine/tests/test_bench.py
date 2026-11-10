"""The language-model benchmark path, driven by scripted clients. No live model is involved."""
import json
import os
from pathlib import Path

import pytest

from commonground import bench, folio, formalize
from commonground.__main__ import main
from commonground.fol import ParseError, to_text
from commonground.verdict import decide

ROWS = [
    {"premises": ["All humans are mortal.", "Socrates is a human."], "premises-FOL": ["-", "-"],
     "conclusion": "Socrates is mortal.", "conclusion-FOL": "-", "label": "True"},
    {"premises": ["No bird is a fish.", "Tweety is a bird."], "premises-FOL": ["-", "-"],
     "conclusion": "Tweety is a fish.", "conclusion-FOL": "-", "label": "False"},
    {"premises": ["Some cats are black."], "premises-FOL": ["-"],
     "conclusion": "Tom is black.", "conclusion-FOL": "-", "label": "Unknown"},
]
FORMULAS = [
    {"premises": ["∀x (Human(x) → Mortal(x))", "Human(socrates)"], "conclusion": "Mortal(socrates)"},
    {"premises": ["∀x (Bird(x) → ¬Fish(x))", "Bird(tweety)"], "conclusion": "Fish(tweety)"},
    {"premises": ["∃x (Cat(x) ∧ Black(x))"], "conclusion": "Black(tom)"},
]


@pytest.fixture
def dataset(tmp_path):
    """A three-example file laid out like the dataset repository, so nothing is downloaded."""
    path = tmp_path / "repo" / folio.VALIDATION
    path.parent.mkdir(parents=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in ROWS), encoding="utf-8")
    return path


class Replay:
    """Answers each request from a table keyed by the conclusion sentence."""

    def __init__(self, table, usage=None):
        self.table, self.calls, self.usage = table, 0, usage or {"prompt_tokens": 7, "completion_tokens": 3}

    def describe(self):
        return {"model": "replay", "host": "none"}

    def complete(self, system, user):
        self.calls += 1
        reply = self.table[json.loads(user.split("\n\nYour previous reply")[0])["conclusion"]]
        if isinstance(reply, Exception):
            raise reply
        return reply, dict(self.usage)


def formalizer():
    return Replay({row["conclusion"]: json.dumps(f, ensure_ascii=False) for row, f in zip(ROWS, FORMULAS)})


# ------------------------------------------------------------------------------ statistics


def test_wilson_interval_reproduces_published_values():
    # Newcombe (1998), Statistics in Medicine 17:857-872, Table I, method 3 (score, no continuity correction).
    for successes, n, low, high in [(81, 263, 0.2553, 0.3662), (15, 148, 0.0624, 0.1605),
                                    (0, 20, 0.0, 0.1611), (1, 29, 0.0061, 0.1718)]:
        got = bench.wilson_interval(successes, n)
        assert (round(got[0], 4), round(got[1], 4)) == (low, high)
    assert bench.wilson_interval(0, 0) is None


def test_mcnemar_exact_is_the_two_sided_binomial_test_on_discordant_pairs():
    assert bench.mcnemar_exact(1, 9) == pytest.approx(2 * (1 + 10) / 2 ** 10)
    assert bench.mcnemar_exact(9, 1) == bench.mcnemar_exact(1, 9)
    assert bench.mcnemar_exact(0, 6) == pytest.approx(2 / 2 ** 6)
    assert bench.mcnemar_exact(5, 5) == 1.0 and bench.mcnemar_exact(0, 0) == 1.0


# ------------------------------------------------------------------------------ runs


def test_formalize_then_solve_run_records_every_example(dataset, tmp_path):
    out = tmp_path / "llm"
    summary = bench.with_model(dataset, out, formalizer(), "llm")
    assert summary["correct"] == 3 and summary["accuracy"] == 1.0 and summary["answered"] == 3
    assert summary["mode"] == "llm" and summary["client"] == {"model": "replay", "host": "none"}
    assert summary["tokens"] == {"prompt_tokens": 21, "completion_tokens": 9}
    assert summary["accuracy_interval_95"][0] < 1.0 and summary["accuracy_interval_95"][1] == 1.0
    rows = [json.loads(line) for line in (out / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["verdict"] for r in rows] == ["True", "False", "Uncertain"]
    assert rows[0]["formulas_by_premise"] == [[f] for f in FORMULAS[0]["premises"]]
    assert rows[0]["conclusion_formula"] == FORMULAS[0]["conclusion"]
    assert json.loads((out / "summary.json").read_text(encoding="utf-8"))["correct"] == 3


def test_an_interrupted_run_resumes_without_asking_again(dataset, tmp_path):
    out = tmp_path / "llm"
    outage = formalize.ProviderError("provider unavailable after 3 attempts", 503)
    table = formalizer().table
    with pytest.raises(formalize.ProviderError):  # an outage stops the run: it is not scored as a wrong answer
        bench.with_model(dataset, out, Replay({**table, ROWS[1]["conclusion"]: outage}), "llm")
    assert len((out / "runs.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    client = formalizer()
    summary = bench.with_model(dataset, out, client, "llm")
    assert client.calls == 2 and summary["examples"] == 3 and summary["correct"] == 3
    again = formalizer()
    bench.with_model(dataset, out, again, "llm")
    assert again.calls == 0


def test_a_directory_is_never_shared_by_two_configurations(dataset, tmp_path):
    out = tmp_path / "run"
    bench.with_model(dataset, out, formalizer(), "llm", limit=1)
    with pytest.raises(bench.ConfigurationMismatch):
        bench.with_model(dataset, out, formalizer(), "direct")
    other = formalizer()
    other.describe = lambda: {"model": "another", "host": "none"}
    with pytest.raises(bench.ConfigurationMismatch):
        bench.with_model(dataset, out, other, "llm")


def test_unusable_replies_and_refused_requests_count_as_unanswered(dataset, tmp_path):
    table = {ROWS[0]["conclusion"]: "I would rather not.",
             ROWS[1]["conclusion"]: formalize.ProviderError("HTTP 400: content rejected", 400),
             ROWS[2]["conclusion"]: json.dumps(FORMULAS[2], ensure_ascii=False)}
    summary = bench.with_model(dataset, tmp_path / "llm", Replay(table), "llm")
    assert summary["verdict_counts"] == {"NoFormalization": 1, "ProviderRefused": 1, "Uncertain": 1}
    assert summary["correct"] == 1 and summary["answered"] == 1 and summary["accuracy_when_answered"] == 1.0
    assert summary["accuracy"] == round(1 / 3, 4)


def test_refusals_in_a_row_are_a_configuration_problem_and_are_not_recorded(dataset, tmp_path):
    rejected = formalize.ProviderError("HTTP 400: response_format is not supported", 400)
    out = tmp_path / "direct"
    with pytest.raises(formalize.ProviderError, match="3 requests in a row were refused"):
        bench.with_model(dataset, out, Replay({row["conclusion"]: rejected for row in ROWS}), "direct")
    assert (out / "runs.jsonl").read_text(encoding="utf-8") == ""  # the run can start again from the first example
    assert not (out / "summary.json").exists()


def test_direct_and_formalized_runs_are_compared_on_the_same_examples(dataset, tmp_path):
    direct = Replay({ROWS[0]["conclusion"]: '{"label": "True"}', ROWS[1]["conclusion"]: '{"label": "True"}',
                     ROWS[2]["conclusion"]: "no idea"})
    first = bench.with_model(dataset, tmp_path / "direct", direct, "direct")
    assert first["verdict_counts"] == {"True": 2, "Invalid": 1} and first["correct"] == 1
    bench.with_model(dataset, tmp_path / "llm", formalizer(), "llm")
    report = bench.compare(tmp_path / "direct", tmp_path / "llm")
    assert report["examples_compared"] == 3
    assert (report["both_right"], report["only_first_right"], report["only_second_right"], report["neither_right"]) \
        == (1, 0, 2, 0)
    assert report["first"]["mode"] == "direct" and report["second"]["correct"] == 3
    assert report["mcnemar_exact_p"] == 0.5


def test_report_states_both_runs_and_the_paired_comparison(dataset, tmp_path, capsys):
    direct = Replay({ROWS[0]["conclusion"]: '{"label": "True"}', ROWS[1]["conclusion"]: '{"label": "True"}',
                     ROWS[2]["conclusion"]: "no idea"})
    bench.with_model(dataset, tmp_path / "direct", direct, "direct")
    bench.with_model(dataset, tmp_path / "llm", formalizer(), "llm")
    published = tmp_path / "published"
    published.mkdir()
    (published / "per_example.csv").write_text("index,agrees\n0,True\n1,True\n2,False\n", encoding="utf-8")
    text = bench.report(tmp_path / "direct", tmp_path / "llm", published)
    assert "## FOLIO validation with `replay` (none)" in text
    assert "| The model answers itself | 3 | 1 | 33.33 % | 6.15 % to 79.23 % | 2 | 50.00 % | 30 |" in text
    assert "| The model writes formulas, the solver answers | 3 | 3 | 100.00 % | 43.85 % to 100.00 % | 3 | 100.00 % | 30 |" in text
    assert "both right on 1, only the first on 0, only the second on 2, neither on 0" in text
    assert "p = 0.5." in text
    assert "agree with the label on 2 of these 3 examples" in text
    assert "The model answers itself, verdicts given: Invalid: 1, True: 2." in text
    assert main(["report", str(tmp_path / "direct"), str(tmp_path / "llm")]) == 0
    assert capsys.readouterr().out.startswith("## FOLIO validation")


def test_command_line_reports_configuration_problems(dataset, tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert main(["folio", "--data", str(dataset.parents[2]), "--out", str(tmp_path / "x"), "--mode", "llm"]) == 2
    assert "LLM_API_KEY" in capsys.readouterr().err
    assert main(["compare", str(tmp_path / "missing-a"), str(tmp_path / "missing-b")]) == 2
    assert "cannot compare" in capsys.readouterr().err


# ------------------------------------------------------------------------------ the whole dataset

DATA = os.environ.get("FOLIO_DIR")


class DatasetOracle:
    """A "perfect formalizer": replies with the dataset's own formula for each sentence it is given."""

    def __init__(self, examples):
        self.by_request = {}
        for ex in examples:
            self.by_request.setdefault(self.key(ex.premises_text, ex.conclusion_text), ex)

    @staticmethod
    def key(premises, conclusion):
        return json.dumps([premises, conclusion], ensure_ascii=False)

    def describe(self):
        return {"model": "dataset-oracle", "host": "none"}

    def complete(self, system, user):
        request = json.loads(user.split("\n\nYour previous reply")[0])
        ex = self.by_request[self.key(request["premises"], request["conclusion"])]
        try:
            parsed = folio.parse_example(ex)
        except ParseError:
            return "the dataset's formula for this example is malformed", {}
        formulas = [to_text(f) for f in parsed.premises]
        if len(formulas) != len(ex.premises_text):
            # Ten examples have a different number of sentences and formulas (a sentence broken
            # across two lines, or an extra background formula): attach them all to the first line.
            formulas = [formulas] + [[] for _ in ex.premises_text[1:]]
        return json.dumps({"premises": formulas, "conclusion": to_text(parsed.conclusion)}, ensure_ascii=False), {}


@pytest.mark.skipif(not DATA, reason="set FOLIO_DIR to a clone of the dataset")
def test_with_a_perfect_formalizer_the_model_pipeline_reproduces_the_reference_run(tmp_path):
    """Feeding the dataset's formulas through the model path (JSON reply, validation, solver) must give
    the verdicts of the reference run: the pipeline around the model adds no error of its own."""
    data_file = folio.fetch(Path(DATA))
    examples = folio.load(data_file)
    summary = bench.with_model(data_file, tmp_path / "oracle", DatasetOracle(examples), "llm")
    rows = {r["index"]: r for r in map(json.loads, (tmp_path / "oracle" / "runs.jsonl").read_text("utf-8").splitlines())}

    expected = {}
    for ex in examples:
        try:
            parsed = folio.parse_example(ex)
        except ParseError:
            expected[ex.index] = "NoFormalization"  # the oracle has no formula to give
            continue
        # The model path refuses a vocabulary used inconsistently; the reference run only notes it.
        expected[ex.index] = "NoFormalization" if parsed.issues else decide(parsed.premises, parsed.conclusion).label
    assert {i: r["verdict"] for i, r in rows.items()} == expected

    published = json.loads((Path(__file__).resolve().parents[2] / "results" / "folio-validation" / "summary.json")
                           .read_text(encoding="utf-8"))
    assert summary["examples"] == published["dataset"]["examples"]
    assert summary["verdict_counts"]["NoFormalization"] == published["parsing"]["examples_with_a_malformed_formula"]
    assert summary["correct"] == published["agreement_with_labels"]["agree"]
    assert summary["answered"] == published["parsing"]["examples_parsed"]
