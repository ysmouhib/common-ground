# Design: the abduction engine (`engine/commonground/abduce.py`)

**Status: plan for owner approval before any code (CG3-1).** Implements
[`../research/THEORY.md`](../research/THEORY.md) (owner-approved 2026-11-14, CGR-5); the
evidence behind every claim is in [`../research/RESEARCH.md`](../research/RESEARCH.md) with
per-source tags. Architecture per the owner's decision of 2026-11-13 (PLAN.md CG3-1): a
logic-backed argument graph represents the discourse and locates candidate foundations; Lean
certifies the selected deductive steps, the solver certifies the rest. Nothing here changes
the v1 engine; `abduce.py` builds on `fol.py`, `verdict.py`, `smt.py`, `ground.py`,
`model.py`, `lean.py`, `argmap.py`, `extract.py`.

## 1. What the engine does, and never does

Given reviewed input for one or more camps, `abduce.py` reports, per camp, the sets of FOL
formulas that are **verified sufficient** to generate the camp's claims, selected from a
named pool by a declared cost (THEORY.md §1–§2). It certifies deductions, not truth and not
belief. It never calls a plausibility estimate a probability, never uses "central", "core
belief", "warrant", "implicit premise" or "bias" in output (RESEARCH.md §14.1, §15.3).

## 2. Input and output

**Input (the record, THEORY.md §2).** Per camp: `endorsed: [statement]`, `rejected_firm:`,
`rejected_soft:`, each statement = FOL formula + verbatim text + span (document, start, end),
as produced by `extract.py` (`Statement.text/start/end`, validated so `text[start:end]`
equals the quote). Relations from extraction (`Relation.kind` ∈ {supports, attacks}) come
along as discourse edges. The pool K ⊇ E⁺ is the reviewed statements plus reviewed unstated
candidates, each candidate with at least one verbatim quote.

**Output.** A report (JSON + Markdown) per camp and, for two or more camps, the cross-camp
section (CG5): per selected system — the axioms with badges, the load vector, coverage κ
and derived share δ, the hull of (size, implausibility) with each system's λ-interval and
the margin to the runner-up, results under both the linear and the logarithmic charge, the
selection recomputed at the minimum and maximum of each plausibility range, the agreement of
the selected system with the discourse graph, and — if no unstated candidate pays for itself —
the abstention result with the stated system A₀ reported. Conflicts and common ground are
reported in two tiers: among stated claims (invariant, F2) and among reconstructed axioms
(selection-relative).

## 3. The argument graph locates candidates; it does not score them

Nodes: every reviewed statement and every unstated candidate. Edges:

- **discourse edges** supports/attacks from `extract.py`;
- **entailment edges** from `argmap.justifications`: a minimal premise set for a claim gives
  "these jointly entail that" edges;
- **conflict membership**: MUSes of the record (from `argmap.enumerate_mus_mss`).

Three signals locate candidate foundations: **load/justifications** (an axiom that appears in
justifications of many claims), **graph position** (uncontested nodes, sources of attacks),
**MUS membership** (axioms inside minimal conflicts are where records break). All three are
reported as agreement with the selected system (RESEARCH.md §8.5 item 2: the graph is a
*check*, never a term of cost(A)).

## 4. Candidate generation: an LLM-independent interface (CG3-2)

```python
class CandidateSource(Protocol):
    def propose(self, record: Record) -> list[Candidate]: ...   # Candidate: fol text + quote(s) + span
```

Scripted sources for tests; the live source wraps `formalize.OpenAICompatible` (same
provenance, outage and flag handling as `folio`/`extract`). Whatever the model returns is
validated like `extract._validate`: formula must parse in `fol.parse`, every quote must exist
verbatim at its span in the source document. Unvalidated candidates are dropped before any
plausibility score exists (RESEARCH.md §15.3 item 1).

## 5. Plausibility (RESEARCH.md §15.3)

Anchored five-level scale with fixed values (0.1, 0.3, 0.5, 0.7, 0.9), prompt blind to camp
identity, k = 5 samples reported as median/min/max, model + host + settings + prompt hash in
the run's `config.json` (never the key), reviewer can replace any estimate with a note,
stated claims have p = 1 (amendment A4). The interface says "plausibility estimate (model,
k samples, range)" — never "probability" or "confidence" (H8).

## 6. The certified layer (CG3-3)

Every verdict follows THEORY.md's verdict table:

| Claim | Engine call | Badge |
|---|---|---|
| A ⊨ φ | `lean.certify` (kernel proof) preferred; `verdict.decide`/`smt.check` refutation as fallback | SUFFICIENT (kernel-checked) or SOLVER-CHECKED (not kernel-certified) |
| A ⊭ r | `verdict.decide` with `model_false` structure, re-evaluated by the solver-free checker in `model.py` | SOLVER-CHECKED |
| A consistent | explicit finite model | SOLVER-CHECKED |
| timeout | — | pending, shown as pending; never "false" |

No text from a visitor or a model reaches Lean: `lean.certify` takes parsed `Formula`s,
generates the source from the syntax tree, and `lean.assert_generated` refuses anything
outside the generated vocabulary (existing `lean.py` machinery; the app never sends visitor
text to Lean either). Soundness note: a solver refutation is sound for ⊨ in any fragment here — Z3 runs on an
uninterpreted sort with a plain solver (`smt.py`), so its "unsat" is a sound refutation
regardless of class. The Bernays–Schönfinkel boundary in `ground.py` is where grounding (the
second engine) *decides* — a boundary of termination, not of soundness. Outside the class the
check still reads SOLVER-CHECKED and its `detail` says the refutation rests on Z3 alone
(THEORY.md limit 6: outside the class, "no verdict" remains possible in general) — owner
decision 2026-11-14, recorded in PLAN.md.

**Checks on a candidate system A** (all certified): consistency; sufficiency A ⊨ φ for every
φ ∈ E⁺; firm rejections A ⊨ ¬r; soft rejections A ⊭ r (each separately, amendment A6 —
joint failure is reported); minimality (S4): for every a ∈ A, A ∖ {a} does not satisfy
condition 2. Named checks (RESEARCH.md §8.5): *premise dependence* = S4; *claim selectivity* =
soft rejections plus the excess report — the pool statements A entails that the camp never
endorsed are listed (over-generation, §3.4 item 5).

## 7. Cost and cost-minimal search (CG3-4)

Size is counted on a normal form that splits conjunctions (top level and under ∀, after
negation normal form — amendment A3), so a conjunction of the claims cannot win by hiding.
cost(A) = Σ(1−p(a)) + λ·|A| (THEORY.md §2). Search: branch-and-bound over subsets of the pool,
pruning a branch when its certified lower bound (cost of the chosen axioms so far plus λ per
remaining required claim) exceeds the best certified system; the search is cross-checked
against brute force over all subsets in the tests, exactly as `argmap.py` is tested against
brute force. Hull (F5): the selected systems over a grid of λ are the lower convex hull of
(|A|, u(A)); each hull system's λ-interval and the margin to the runner-up are computed and
reported (amendment A5) — one λ is never silently chosen. Termination: finite pool, each
check bounded by `timeout_ms`, enumeration capped (`limit`, `TooMany` like `argmap.py`);
scope is "tens of statements" (brief §10). Soundness: a system is reported only if every
check above returned its positive verdict; any "no verdict" leaves the system pending, never
published as certified.

## 8. Load (CG4-1)

load(a) = |{ e ∈ E⁺ : every minimal premise set for e inside A contains a }|, computed
directly as A ∖ {a} ⊭ e — |A|·|E⁺| entailment checks, no enumeration (RESEARCH.md §2.4,
§14.1). Every removal check is a real certified counterfactual. The load vector is part of
every report. Load is never called centrality (limit 9).

## 9. No axiom system, coverage, abstention

Whether any axiom system exists depends on the reviewed statements alone (F1): E⁺ consistent
and entailing no soft rejection. Tested by brute force on small pools in the tests. When κ < 1
(κ = 1 − m/|E⁺|, m a smallest correction set), the report lists the minimal conflicts and
every maximal consistent subset, gives κ, and presents one system per maximal consistent
subset — none chosen silently (RESEARCH.md §14.3). When no unstated candidate lowers the
cost, the report says so and shows the stated system A₀: abstention is a result
(RESEARCH.md §8.5 item 3).

## 10. Negative controls (CG3-5)

For a certified system A, the engine also builds the Lean problems for the *negations* of
its sufficiency claims and requires the kernel to reject them; a "certificate" that Lean
accepts for a non-theorem fails the test. Tests include: a claim A does not entail is not
reported as entailed; a smuggled contradiction is caught by the consistency model; a
redundant axiom is caught by S4; a violated rejection is caught by the rejection checks
(brief §12: try to break it before declaring it certified).

## 11. Testing plan

- Brute-force cross-check of the search and of the hull on small pools (mirrors
  `test_argmap.py`).
- Scripted `CandidateSource`s: deterministic, resumable, outage ≠ wrong answer.
- Property tests: every quote span exists in its document; every output formula parses;
  determinism at temperature 0.
- Negative controls of §10 as pytest cases, with and without `LEAN_BIN` (solver-only mode
  reads SOLVER-CHECKED).
- Regression: `examples/plastic_bags.json` and `examples/co2-2021/golden.json`
  (machine-checked target; the pipeline must reproduce it — CG7-3, divergences to AUDIT.md).

## 12. Task mapping

CG3-2 = §4 interface + scripted sources. CG3-3 = §6 checks + Lean certificates. CG3-4 = §7
search + hull, brute-force cross-checks. CG3-5 = §10. CG3-6 = symbolic baseline control:
A = E(C) (the stated system) always computed and reported alongside, per the owner's decision
of 2026-11-13. CG4 = §8 + per-camp report. CG5 = cross-camp section (§2), design in
`docs/design/cross-camp.md`.

## 13. Open questions (carried from THEORY.md §6)

Normal form details; linear vs logarithmic charge (both reported); joint soft rejections; a
shared background theory; load vector as tie-breaker. None blocks the plan above; each is
reported, not silently decided.
