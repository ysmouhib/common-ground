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
        report = {"camp": camp,
                  "pool": {"candidates": [{"fol": c["fol"], "quotes": []} for c, _ in cands],
                           "dropped": []},
                  "systems": [{"axioms": [fol.to_text(a) for a in axioms],
                               "certified": True, "load": lv}]}
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
