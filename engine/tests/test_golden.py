"""CG7-3: the pipeline on the CO2 golden corpus (examples/co2-2021/).

The golden ships statement texts, not whole booklet pages, so the test document is
the camp's statements joined by newline with spans located in it — the verbatim-span
discipline still holds. Asserted: every golden FOL parses; each camp's golden
candidate set is a certified axiom system under the pipeline's checks (CG7-2's
hand-check, now through check_system); the computed load vector matches the recorded
pipeline numbers; the divergence from the hand-worked expected_load_ranking is real
and audited in AUDIT.md (AUDIT-1/AUDIT-2); crosscamp.analyze runs on the two camps.
"""

import json
from pathlib import Path

import pytest

from commonground import abduce, crosscamp, fol, load

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "examples" / "co2-2021"
STATEMENTS = json.loads((EX / "statements.json").read_text(encoding="utf-8"))["statements"]
GOLDEN = json.loads((EX / "golden.json").read_text(encoding="utf-8"))


def build_camp(camp):
    g = GOLDEN["camps"][camp]
    texts = {s["id"]: s["text"] for s in STATEMENTS if s["camp"] == camp}
    fol_by_id = {s["id"]: s["fol"] for s in g["statements"]}
    doc_id = f"doc-{camp}"
    parts, spans = [], {}
    offset = 0
    for s in g["statements"]:
        t = texts[s["id"]]
        parts.append(t)
        spans[s["id"]] = (offset, offset + len(t))
        offset += len(t) + 1
    record = abduce.Record(camp, [abduce.Document(doc_id, "\n".join(parts))],
                           [abduce.RecordStatement(s["id"], "endorsed", fol_by_id[s["id"]],
                                                   doc_id, texts[s["id"]], spans[s["id"]])
                            for s in g["statements"]])
    cands = [(c, abduce.Candidate(c["fol"], [(doc_id, texts[ev], spans[ev]) for ev in c["evidence"]]))
             for c in g["candidate_axioms"]]
    id_by_text = {fol.to_text(fol.parse(c["fol"])): c["id"] for c, _ in cands}
    plaus = {fol.to_text(fol.parse(c["fol"])): c["plausibility"] for c, _ in cands}
    return record, cands, id_by_text, plaus, g


def test_golden_formulas_parse_and_ids_match():
    for camp, g in GOLDEN["camps"].items():
        for s in g["statements"]:
            assert fol.parse(s["fol"]) is not None
        for c in g["candidate_axioms"]:
            assert fol.parse(c["fol"]) is not None
        ids = {s["id"] for s in STATEMENTS if s["camp"] == camp}
        assert {s["id"] for s in g["statements"]} == ids


@pytest.mark.parametrize("camp", ["yes", "no"])
def test_golden_candidate_set_is_a_certified_axiom_system(camp):
    record, cands, _, _, _ = build_camp(camp)
    axioms = [fol.parse(c["fol"]) for c, _ in cands]
    checks = abduce.check_system(axioms, record, timeout_ms=5000)
    assert checks.certified
    assert all(c.outcome == "holds" for c in checks.sufficiency)


# Loads computed by the pipeline (deterministic solver); the divergence from
# golden.json's hand-worked expected_load_ranking is AUDIT-1 / AUDIT-2 in AUDIT.md.
COMPUTED_LOADS = {
    "yes": {"YAF": 3, "YA1": 3, "YA3": 2,
            "YA2a": 1, "YA2b": 1, "YA2c": 1, "YA4": 1, "YA5": 1, "YA6": 1, "YA7": 1},
    "no": {"NA1": 5, "NA2": 2, "NA3": 2, "NA4": 1, "NA5": 1, "NA6": 1},
}


@pytest.mark.parametrize("camp", ["yes", "no"])
def test_pipeline_load_vector_and_audit_entries(camp):
    record, cands, id_by_text, _, g = build_camp(camp)
    axioms = [fol.parse(c["fol"]) for c, _ in cands]
    lv = load.load_vector(axioms, abduce._targets(record), timeout_ms=5000)
    computed = {id_by_text[r["axiom"]]: r["load"] for r in lv}
    assert computed == COMPUTED_LOADS[camp]
    audit = (ROOT / "AUDIT.md").read_text(encoding="utf-8")
    assert f"AUDIT-{1 if camp == 'yes' else 2}" in audit
    computed_order = [k for k, _ in sorted(computed.items(), key=lambda kv: (-kv[1], kv[0]))]
    assert computed_order != g["expected_load_ranking"]   # the divergence is real, and audited


def test_crosscamp_on_the_golden_camps():
    camps = []
    for camp in ("yes", "no"):
        record, cands, _, _, _ = build_camp(camp)
        axioms = [fol.parse(c["fol"]) for c, _ in cands]
        lv = load.load_vector(axioms, abduce._targets(record), timeout_ms=5000)
        # the certified flag comes from the engine's own checks, not from this test
        certified = abduce.check_system(axioms, record, timeout_ms=5000).certified
        assert certified
        report = {"camp": camp,
                  "pool": {"candidates": [{"fol": c["fol"], "quotes": []} for c, _ in cands],
                           "dropped": []},
                  "systems": [{"axioms": [fol.to_text(a) for a in axioms],
                               "certified": certified, "load": lv}]}
        camps.append(crosscamp.Camp(record, report))
    result = crosscamp.analyze(camps, timeout_ms=5000)
    json.dumps(result)
    assert result["camps"] == ["yes", "no"]
    # the golden camps' stated claims are jointly consistent and share no stated claim:
    # they diverge at the root, reported as ranked axiom pairs (AUDIT.md, cross-camp note)
    fl = result["fault_lines"]
    assert fl["stated"]["consistent"]["outcome"] == "holds"
    assert fl["stated"]["mus"] == []
    assert result["common_ground"]["stated"]["agreed"] == []
    pair = fl["per_system_pair"][0]
    assert pair["consistent"] is True and pair["mus"] == []
    assert pair["root_divergence"]
    ranks = [r["rank"] for r in pair["root_divergence"]]
    assert ranks == sorted(ranks, reverse=True)
    assert max(ranks) == 8


def test_cli_co2_runs_the_bundled_example_headless(tmp_path):
    from commonground.__main__ import main
    out = tmp_path / "co2out"
    # small check cap keeps the test fast; the seed (stated system A₀, F1) is checked first,
    # so a certified selection exists regardless (AUDIT-4 records the full-search timing)
    code = main(["co2", "--dir", str(EX), "--max-checks", "150", "--timeout-ms", "3000",
                 "--out", str(out)])
    assert code == 0
    result = json.loads((out / "crosscamp.json").read_text(encoding="utf-8"))
    assert result["camps"] == ["yes", "no"]
    # stated systems on the conjunction-splitting normal form: 10 and 9 conjuncts at λ = 0.3.
    # Each camp has a candidate identical to a stated claim (YA1, NA3); its plausibility
    # estimate must not be charged to the stated copy.
    stated_cost = {"yes": 3.0, "no": 2.7}
    for camp in ("yes", "no"):
        report = json.loads((out / camp / "report.json").read_text(encoding="utf-8"))
        assert report["systems"] and all(s["certified"] for s in report["systems"])
        assert report["systems"][0]["cost"] == pytest.approx(stated_cost[camp])
        assert len(report["plausibility"]["ignored_for_stated"]) == 1
        # 150 checks do not finish either search: what is reported is certified but not shown
        # to be cost-minimal, and the report must say so instead of claiming abstention
        assert report["selection"]["exhausted"] and report["search_complete"] is False
        assert report["abstention"] is None and report["hull_complete"] is False
        md = (out / camp / "report.md").read_text(encoding="utf-8")
        assert "SEARCH INCOMPLETE" in md and "No proposed unstated axiom pays for itself" not in md
    assert result["search_incomplete"] == ["yes", "no"]
    cross_md = (out / "crosscamp.md").read_text(encoding="utf-8")
    assert cross_md.startswith("# Cross-camp") and "Search incomplete for `yes`, `no`" in cross_md


# --- CG8-2: CO2 leave-one-out holdout (RESEARCH.md §14.2) ---


def holdout(camp, timeout_ms: int = 3000):
    """Withhold each reviewed statement of the camp, rebuild from the rest — the remaining
    stated claims plus only the candidates whose evidence is not solely the withheld
    statement — and check whether the rebuilt system derives the withheld statement.
    Every derivation is a certified entailment check carrying its badge; a non-derivation
    is a definite non-entailment with its finite model."""
    record, cands, _, _, _ = build_camp(camp)
    rows = []
    for w in record.statements:
        kept = [st for st in record.statements if st.id != w.id]
        rec2 = abduce.Record(record.camp, record.documents, kept)
        avail = [fol.parse(c["fol"]) for c, _ in cands
                 if any(ev != w.id for ev in c["evidence"])]
        stated_rest = [st.formula() for st in kept if st.stance == "endorsed" and st.formula()]
        chk = abduce.entailment_check(avail + stated_rest, w.formula(), kind="holdout",
                                     timeout_ms=timeout_ms)
        rows.append({"withheld": w.id, "derived": chk.outcome == "holds", "badge": chk.badge,
                     "candidates_available": len(avail)})
    return rows


def holdout_summary(camp, rows):
    from commonground import bench
    n = len(rows)
    k = sum(1 for r in rows if r["derived"])
    return {"camp": camp, "withheld": n, "derived": k,
            "proportion": round(k / n, 4) if n else None,
            "interval_95": list(bench.wilson_interval(k, n)) if n else None,
            "rows": rows}


def test_holdout_yes_camp():
    summary = holdout_summary("yes", holdout("yes"))
    assert summary["withheld"] == 7
    assert summary["derived"] == 2                      # recorded 2026-11-14
    assert summary["proportion"] == round(2 / 7, 4)
    assert summary["interval_95"] and 0.08 < summary["interval_95"][0] < 0.65
    assert all(r["badge"] for r in summary["rows"])     # every row certified, none pending


def test_holdout_no_camp():
    summary = holdout_summary("no", holdout("no"))
    assert summary["withheld"] == 6
    assert summary["derived"] == 2                      # recorded 2026-11-14
    assert all(r["badge"] for r in summary["rows"])
