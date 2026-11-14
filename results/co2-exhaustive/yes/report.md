# Camp `yes` — reconstructed axiom systems

λ = 0.3; source: `scripted`. These axioms are **verified sufficient** to generate this camp's claims — a certified deduction, not a claim about what anyone believes.

## Statements (reviewed)

| id | stance | FOL |
|---|---|---|
| yes-1 | endorsed | `StronglyAffected(switzerland, climate)` |
| yes-2 | endorsed | `(GlacierMelting ∨ LandslideDamage) → HighCosts(pop, econ)` |
| yes-3 | endorsed | `NotAnOption(doingNothing)` |
| yes-4 | endorsed | `Responsible(switzerland, climate)` |
| yes-5 | endorsed | `SupportsGreenInvestment(law) ∧ CreatesFutureJobs(law)` |
| yes-6 | endorsed | `Fair(law) ∧ Social(law)` |
| yes-7 | endorsed | `ReducesDependency(law, foreignOil) ∧ InvestsLocally(law)` |

## Unstated candidates proposed

| FOL | supporting quotes | plausibility estimate |
|---|---|---|
| `GlacierMelting ↔ ClimateDamageEvent(glacierMelting)` | 1 | 0.7 |
| `LandslideDamage ↔ ClimateDamageEvent(landslideDamage)` | 1 | 0.7 |
| `∀e (ClimateDamageEvent(e) → HighCosts(pop, econ))` | 1 | 0.8 |
| `∀x (StronglyAffected(x, climate) → Responsible(x, climate))` | 2 | 0.9 |
| `∀x (Responsible(x, climate) → NotAnOption(doingNothing))` | 2 | 0.85 |
| `GreenInvestmentLaw(law)` | 3 | 0.8 |
| `∀l (GreenInvestmentLaw(l) → (SupportsGreenInvestment(l) ∧ CreatesFutureJobs(l)))` | 1 | 0.75 |
| `∀l (GreenInvestmentLaw(l) → (Fair(l) ∧ Social(l)))` | 1 | 0.7 |
| `∀l (GreenInvestmentLaw(l) → (ReducesDependency(l, foreignOil) ∧ InvestsLocally(l)))` | 1 | 0.75 |

Dropped before scoring (no parse or no verbatim quote):
- `StronglyAffected(switzerland, climate)` — duplicate of a stated claim

Plausibility estimates given for stated claims are not applied (a stated claim counts as plausibility 1): `StronglyAffected(switzerland, climate)`.

## Selected systems (cost-minimal, ties reported)

### System 1 — cost 3.0000 — SOLVER-CHECKED (not kernel-certified)

Axioms:

- `((GlacierMelting ∨ LandslideDamage) → HighCosts(pop, econ))`
- `(Fair(law) ∧ Social(law))`
- `(ReducesDependency(law, foreignOil) ∧ InvestsLocally(law))`
- `(SupportsGreenInvestment(law) ∧ CreatesFutureJobs(law))`
- `NotAnOption(doingNothing)`
- `Responsible(switzerland, climate)`
- `StronglyAffected(switzerland, climate)`

Load ranking:

| axiom | load |
|---|---|
| `((GlacierMelting ∨ LandslideDamage) → HighCosts(pop, econ))` | 1 |
| `(Fair(law) ∧ Social(law))` | 1 |
| `(ReducesDependency(law, foreignOil) ∧ InvestsLocally(law))` | 1 |
| `(SupportsGreenInvestment(law) ∧ CreatesFutureJobs(law))` | 1 |
| `NotAnOption(doingNothing)` | 1 |
| `Responsible(switzerland, climate)` | 1 |
| `StronglyAffected(switzerland, climate)` | 1 |

Negative controls: all passed.

## Hull over λ — PARTIAL

Only the systems the search certified are on this hull (branch-and-bound does not check systems that cost more at this λ), so the intervals are not established: at another λ a system that was not checked may win.

| size | implausibility | λ-interval |
|---|---|---|
| 10 | 0.0000 | [0.0000, ∞] |

## Symbolic baseline (A = E(C), same certified checks)

Stated system certified: True; minimal stated system certified: True.

## Abstention

No proposed unstated axiom pays for itself: the selected system is the stated one (A₀), reported as such.
