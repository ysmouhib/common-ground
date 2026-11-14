# Design: cross-camp analysis (`engine/commonground/crosscamp.py`)

**Status: plan for owner approval before any code (CG5-1).** Implements
[`../research/THEORY.md`](../research/THEORY.md) (owner-approved 2026-11-14, CGR-5) —
F2 (the stated claims are the invariant), H4 (fault lines), amendment A7 (two tiers) —
and brief §4/§6; the evidence is in [`../research/RESEARCH.md`](../research/RESEARCH.md)
§1–§2, §8.4–§8.5 with per-source tags. Builds on `abduce.py` (CG4-2 per-camp report) and
`argmap.py` (MARCO). Nothing here changes the v1 engine or `abduce.py`.

## 1. What it reports, and never claims

For two or more camps, each with its per-camp report (selected systems with badges),
`crosscamp.py` reports the **provable common ground** and the **exact fault lines**, in
two tiers (amendment A7; RESEARCH.md §2.4): among *stated* claims (invariant — holds
for every reconstruction, F2) and among *reconstructed* axioms (selection-relative —
reported per combination of selected systems, ties included, never silently picked).
It does **not** promise that showing common ground reduces disagreement (Lord, Ross &
Lepper 1979, abstract; RESEARCH.md): the product shows the provable common ground and
the fault lines. Same verdict table and vocabulary as `abduction.md` §6: badges
SUFFICIENT (kernel-checked) / SOLVER-CHECKED / PENDING, "verified sufficient", never
"probability" or any judgment of persons.

## 2. Input and output

**Input.** Per camp: the same record JSON + candidates file as the `camp` command
(record with verbatim spans, candidate pool), plus plausibilities and λ — the inputs of
`report_camp`. **Output.** `crosscamp.json` + `crosscamp.md` next to the per-camp
`report.json`/`report.md`. Fault-line output schema (CG5-1 deliverable):

```
{
  "camps": ["A", "B"],
  "common_ground": {
    "stated":   [{"statement", "badge", "certificate"|"model"}],        # tier 1
    "per_system_pair": [{"systems": ["A1", "B1"], "agreed": [...]}]     # tier 2
  },
  "conflicts": {
    "stated":   {"mus": [[...], ...], "mcs": [...]},                     # tier 1
    "per_system_pair": [{"systems": [...], "mus": [...], "mcs": [...],
                         "root_divergence": [{"a1", "a2", "models", "rank"}]}]
  }
}
```

Every entry carries its badge and evidence (certificate hash + Lean source, or the
explicit finite model re-evaluated by `model.py`). A MUS entry is a set of axiom texts;
an MCS is its complement in the union (smallest concession, Liffiton & Sakallah 2008
Theorem 1).

## 3. Common ground, two tiers (CG5-2)

- **Tier 1, stated (invariant).** For each statement s in the union of the camps'
  reviewed statements (E, R_firm, R_soft formulas): check E⁺₁ ⊨ s and E⁺₂ ⊨ s with
  the certified entailment check; s is provable common ground iff both hold. Also
  check satisfiability of E⁺₁ ∪ E⁺₂: if inconsistent, the stated tier conflicts (F2:
  then every A₁ ∪ A₂ is inconsistent).
- **Tier 2, reconstructed (selection-relative).** For every combination of selected
  systems (all ties reported): for each s in the union pool, A₁ ⊨ s and A₂ ⊨ s.
  RESEARCH.md §2.3(c) mapping: s is entailed by both exactly when it is a necessary
  condition of A₁ ∨ A₂; because Lin's existence results are propositional
  (§2.3(d)), we enumerate over the finite pool only and never claim a single-formula
  weakest-sufficient / strongest-necessary condition in first order.
- **Per-claim cross-camp derivation viewer** (brief §6): for each agreed statement,
  `argmap.justifications(A₁ ∪ A₂, s)` — every minimal premise set that entails it,
  each with its certificate badge.

## 4. Fault lines: reduced disagreement (CG5-3)

- **Tier 1, stated:** MUSes of E⁺₁ ∪ E⁺₂ via `argmap.enumerate_mus_mss` (MARCO) with
  the solver oracle — invariant.
- **Tier 2, per selected pair:** MUSes of A₁ ∪ A₂, same call; the MCSes come out as
  complements. Sources pack C1–C3 (RESEARCH.md §7): pinpointing/MinAs (Baader &
  Suntisrivaraporn 2008; Schlobach & Cornet 2003; Peñaloza 2019) motivates reading a
  MUS as the minimal set whose consequence breaks; Reiter 1987 reads MUSes as
  diagnoses; Liffiton & Sakallah 2008 (definitions + hitting-set duality, checked in
  `test_argmap.py`) and Liffiton et al. 2016 (MARCO, implemented in `argmap.py`) do the
  enumeration. Each MUS is certified by a solver refutation (badge SOLVER-CHECKED; sound in any
  fragment — Z3 runs on an uninterpreted sort with a plain solver, `smt.py`, so its "unsat"
  is a sound refutation; `ground.py`'s Bernays–Schönfinkel boundary is where the grounding
  engine decides, i.e. a boundary of termination, not of soundness — outside the class the
  check's `detail` says the refutation rests on Z3 alone. Owner decision 2026-11-14, PLAN.md).
- **Capping.** `limit`/`TooMany` as in `argmap.py`. MARCO outputs MUSes steadily, so a
  capped run reports a certified *partial* MUS list, labelled partial. Never derive
  MUSes from a partial MCS collection — that is the CAMUS phase-1 caveat (RESEARCH.md
  §1); MARCO does not have it.
- **Consistent union — root divergence** (brief §4): if A₁ ∪ A₂ is consistent, report
  the pairs (a₁, a₂) of load-bearing axioms with A₁ ⊭ a₂ and A₂ ⊭ a₁ — each
  non-entailment an explicit finite model (SOLVER-CHECKED) — ranked by
  load₁(a₁) + load₂(a₂), the downstream claims the pair explains. Craig interpolation
  is optional research, not a Phase requirement (brief §4).

## 5. Verdict discipline and soundness

Identical to `abduction.md` §6: entailment by `lean.certify` (kernel) preferred, solver
refutation fallback; non-entailment only with an explicit model re-evaluated by the
solver-free checker in `model.py`; Undecided/outside-BS = PENDING, shown as pending,
never "false". No visitor or model text reaches Lean (`lean.assert_generated`).
Nothing is published without its positive verdict.

## 6. CLI

`python -m commonground crosscamp A.json B.json [C.json ...] --candidates a.json b.json
[...] --plausibilities ... --lam 0.3 --lean --out DIR` — `--candidates` once per camp,
in record order. Runs `report_camp` per camp (writing each camp's report), then the
cross-camp section into `DIR/crosscamp.json` + `crosscamp.md`. `TooMany` exits 2 with
the partial, labelled output still written.

## 7. Testing plan

- Hitting-set duality MUS ↔ MCS cross-checked by brute force on tiny formula sets
  (mirrors `test_argmap.py`).
- Tier-1 invariance: a stated conflict appears in every selected pair's tier-2 report;
  a stated agreement appears in every pair's common ground.
- Certified badges on every MUS/non-entailment; a forced-Undecided entry stays PENDING
  and is not published as a fault line.
- Root-divergence ranking on a consistent two-camp example (explicit models required).
- CLI end-to-end on two tiny records; CO2 golden pair lands with CG7-3.

## 8. Task mapping

CG5-2 = §3 (common ground, both tiers, derivation viewer) + solver checks.
CG5-3 = §4 (fault lines, root divergence) + §6 CLI. Files:
`engine/commonground/crosscamp.py`, `engine/tests/test_crosscamp.py`,
`engine/commonground/__main__.py`.

## 9. Open questions (reported, not silently decided)

- More than two camps: pairwise pairs plus a joint MUS over the union of all selected
  systems, or pairwise only.
- Whether common ground enumerates only the camps' reviewed statements or the whole
  pool (unstated candidates included).
- Craig interpolation for consistent unions: research only (brief §4).
