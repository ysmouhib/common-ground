# Camp `no` — reconstructed axiom systems

λ = 0.3; source: `scripted`. These axioms are **verified sufficient** to generate this camp's claims — a certified deduction, not a claim about what anyone believes.

## Statements (reviewed)

| id | stance | FOL |
|---|---|---|
| no-1 | endorsed | `PriceRise(petrol) ∧ PriceRise(diesel)` |
| no-2 | endorsed | `CostsRise(averageFamily, high)` |
| no-3 | endorsed | `NoEffectOnClimate(law)` |
| no-4 | endorsed | `TinyShareOfEmissions(switzerland)` |
| no-5 | endorsed | `MainlyHitsLowIncome(law) ∧ Unjust(law)` |
| no-6 | endorsed | `Radical(law) ∧ OnlyBansAndRules(law)` |

## Unstated candidates proposed

| FOL | supporting quotes | plausibility estimate |
|---|---|---|
| `CO2Law(law) ∧ AppliesTo(law, switzerland)` | 1 | 0.95 |
| `∀l (CO2Law(l) → (PriceRise(petrol) ∧ PriceRise(diesel) ∧ CostsRise(averageFamily, high)))` | 2 | 0.8 |
| `∀l ∀c (CO2Law(l) ∧ AppliesTo(l, c) ∧ TinyShareOfEmissions(c) → NoEffectOnClimate(l))` | 2 | 0.85 |
| `∀l (CO2Law(l) → (MainlyHitsLowIncome(l) ∧ Unjust(l)))` | 1 | 0.75 |
| `∀l (CO2Law(l) → (Radical(l) ∧ OnlyBansAndRules(l)))` | 1 | 0.7 |

Dropped before scoring (no parse or no verbatim quote):
- `TinyShareOfEmissions(switzerland)` — duplicate of a stated claim

Plausibility estimates given for stated claims are not applied (a stated claim counts as plausibility 1): `TinyShareOfEmissions(switzerland)`.

## Selected systems (cost-minimal, ties reported)

### System 1 — cost 2.7000 — SOLVER-CHECKED (not kernel-certified)

Axioms:

- `(MainlyHitsLowIncome(law) ∧ Unjust(law))`
- `(PriceRise(petrol) ∧ PriceRise(diesel))`
- `(Radical(law) ∧ OnlyBansAndRules(law))`
- `CostsRise(averageFamily, high)`
- `NoEffectOnClimate(law)`
- `TinyShareOfEmissions(switzerland)`

Load ranking:

| axiom | load |
|---|---|
| `(MainlyHitsLowIncome(law) ∧ Unjust(law))` | 1 |
| `(PriceRise(petrol) ∧ PriceRise(diesel))` | 1 |
| `(Radical(law) ∧ OnlyBansAndRules(law))` | 1 |
| `CostsRise(averageFamily, high)` | 1 |
| `NoEffectOnClimate(law)` | 1 |
| `TinyShareOfEmissions(switzerland)` | 1 |

Negative controls: all passed.

## Hull over λ (each system optimal on its interval)

| size | implausibility | λ-interval |
|---|---|---|
| 7 | 0.8000 | [0.4000, ∞] |
| 9 | 0.0000 | [0.0000, 0.4000] |

Margin to the runner-up at λ = 0.3: 0.2000

## Symbolic baseline (A = E(C), same certified checks)

Stated system certified: True; minimal stated system certified: True.

## Abstention

No proposed unstated axiom pays for itself: the selected system is the stated one (A₀), reported as such.
