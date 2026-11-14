# AUDIT.md — divergences between the pipeline and the hand-worked golden

CG7-3: `engine/tests/test_golden.py` runs the pipeline on `examples/co2-2021/` and
every divergence from `golden.json` is recorded here with an error-taxonomy class.
The golden file itself is kept as the hand-worked target; pipeline numbers are
reported alongside, never silently substituted.

## Taxonomy

- **DUP** — duplicate stated/candidate axiom: the same FOL appears as a stated claim
  (p = 1) and as a candidate, so load counts it twice in minimal premise sets.
- **CONJ** — conjunction axiom accumulates load: counted as one axiom by the load
  vector, but it is the entry point of every minimal premise set that uses either part.
- **SENS** — cost/λ (or plausibility) sensitivity: the selected system depends on the
  declared cost, per CG8-4; not an error.
- **SCOPE** — outside the documented scope ("tens of statements", check cap); recorded,
  never silently wrong.

## Entries

- **AUDIT-1** (2026-11-14, class DUP, camp `yes`, load ranking). Pipeline computes
  loads YAF=3, YA1=3, YA3=2, and YA2a/YA2b/YA2c/YA4/YA5/YA6/YA7=1;
  `golden.json → camps.yes.expected_load_ranking` puts YA3 first. Cause: YA1's FOL is
  identical to stated yes-1, so the responsibility chain's minimal premise sets contain
  both the stated copy and YA1, while the hand-worked ranking counted YA3 as driving
  yes-1/yes-4/yes-3. The certified definition (THEORY.md §2.4 load) is the pipeline's;
  status: recorded, golden kept as target.
- **AUDIT-2** (2026-11-14, class CONJ, camp `no`, load ranking). Pipeline computes
  NA1=5, NA2=2, NA3=2, NA4=NA5=NA6=1; `expected_load_ranking` puts NA4 (efficacy)
  first. Cause: NA1 = `CO2Law(law) ∧ AppliesTo(law, switzerland)` is in every
  no-claim's minimal premise set, so it accumulates the highest certified load.
  Status: recorded, golden kept as target.
- **AUDIT-3** (2026-11-14, class SENS, cross-camp selection). At λ=0.3 the stated
  system A₀ is cheaper than the full golden candidate set, so selection reports
  abstention rather than the candidate set; the hull report (CG3-4) gives the
  λ-intervals on which candidate systems win. Status: recorded; quantified under
  CG8-4. **Checked in the soundness review of 2026-11-14.** Camp `no`: established by
  an exhaustive search (`report_camp` on the `no` record built by
  `__main__._camp_from_corpus`, λ=0.3, `timeout_ms=3000`, `max_checks=4000`; brute
  force over the 11-item pool, 2,048 subsets checked, search complete, 16 certified
  systems): the stated system (9 conjuncts, cost 2.7) is the only cost-minimal one,
  margin 0.2 to the runner-up; on the hull it is cost-minimal for λ ≤ 0.4, and above
  that the 7-conjunct system with NA1, NA2, NA5, NA6 (implausibility 0.8) is.
  Camp `yes`: **not established** — its search does not finish (AUDIT-4), and a
  capped run shows only that the stated system is certified, not that it is the
  cheapest. Until the review the capped CLI run printed "abstention" for both camps;
  it now prints "SEARCH INCOMPLETE" with abstention pending.
- **AUDIT-4** (2026-11-14, class SCOPE, performance). `report_camp` on the 16-item
  yes-camp pool (7 stated + 10 candidates, one duplicate dropped) did not finish within
  a 250 s probe window; the search is bounded by MAX_CHECKS/MAX_POOL (TooMany /
  exhausted, design §7), never wrong — pending entries are shown as pending. The
  certified checks, load vector and cross-camp analysis on the same data complete in
  seconds and are what `test_golden.py` asserts. Status: recorded; revisit if the CLI
  run (CG7-4) needs the full search on this pool. Since 2026-11-14 a search the cap
  stopped is labelled in the report itself (`search_complete: false`, `abstention:
  null`, "SEARCH INCOMPLETE" and a partial hull in `report.md`), and `test_golden.py`
  asserts that for the 150-check CLI run.
- **AUDIT-5** (2026-11-14, class DUP, both camps, cost). Found in the soundness
  review: the plausibility estimate of a candidate identical to a stated claim (YA1,
  0.85, = yes-1; NA3, 0.9, = no-4) stayed keyed by the formula after the candidate was
  dropped as a duplicate, so the *stated* claim was charged 1 − p: the stated systems
  cost 3.15 and 2.8 instead of 3.0 and 2.7. A stated claim has p = 1 (THEORY.md §2).
  Status: fixed in `report_camp`; such an estimate is not applied and is listed under
  `plausibility.ignored_for_stated`; `test_golden.py` pins 3.0 and 2.7.

## Cross-camp result on the golden camps (2026-11-14, not a divergence)

`crosscamp.analyze` on the two golden systems: the stated claims are jointly
consistent (no stated MUS, no stated common-ground claim), so the camps diverge at
the root — root-divergence axiom pairs ranked by combined load, top rank 8
(`StronglyAffected(switzerland, climate)` vs `CO2Law(law) ∧ AppliesTo(law, switzerland)`).
