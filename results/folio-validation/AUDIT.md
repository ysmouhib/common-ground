# Where FOLIO's formulas do not support FOLIO's labels

FOLIO validation, 204 examples, dataset revision `5d7bb84`. For each example the
engine decided the conclusion from the dataset's own first-order formulas
(`python -m commonground folio --out results/folio-validation --lean`). In 195
examples the verdict equals the dataset's label. This file is about the other nine,
and about one property of the data that matters to anyone who formalizes it sentence
by sentence.

Nothing here says which side is "right" about the English sentences. The claim is
narrower and checkable: **under classical first-order semantics, the formulas
published with these examples do not yield the label published with them.** Each
row says what kind of evidence backs that.

| Example (0-based line) | Dataset label | Verdict from the dataset's formulas | Evidence | What the formulas do |
|---|---|---|---|---|
| 5 | True | Uncertain | two finite models, re-checked | One premise uses the predicate `Meeting`, another `Meetings`. The spelling breaks the chain of implications the label relies on. |
| 27 | False | Uncertain | two finite models, re-checked | A sentence saying two things cannot both hold is formalized as "neither holds". With that formula the conclusion is left open. |
| 29 | Uncertain | False | proof checked by the Lean kernel | Same premises as 27. The formulas entail the negation of the conclusion, so "Uncertain" cannot be what they give. |
| 47 | False | Uncertain | two finite models, re-checked | The label needs a fact that no formula states (that a person has a single favourite season). |
| 87 | True | not a formula | parser | Premise 5 has a comma where a connective is required. Its conclusion formula also states something other than the conclusion sentence. |
| 112 | True | Uncertain | two finite models, re-checked | Premise 1 mixes ∧ and ∨ without brackets. The label follows only if ∨ is read as binding tighter than ∧. |
| 114 | False | Uncertain | two finite models, re-checked | Same premise as 112, same dependence on the reading. |
| 138 | True | Uncertain | two finite models, re-checked | A list of three things that are all said to be of one kind is formalized with ∨ instead of ∧. |
| 139 | False | Uncertain | two finite models, re-checked | Same premise as 138. |

## How to read the evidence

* **Two finite models, re-checked.** The solver produced one structure in which all
  premises and the conclusion hold, and one in which all premises hold and the
  conclusion fails. Both were then evaluated by `commonground/model.py`, which
  imports no solver. Model sizes are in `per_example.csv`. This is a complete
  proof that the formulas settle the conclusion neither way.
* **Proof checked by the Lean kernel.** The statement "premises entail ¬conclusion"
  was generated as a Lean 4 theorem, closed by Lean's `grind`, and passed the axiom
  audit (`propext`, `Classical.choice`, `Quot.sound` only).

## Sensitivity to how unbracketed ∧/∨ is read

Three examples contain a formula that mixes ∧ and ∨ without brackets. Reading those
with ∧ and ∨ on one level, grouping to the right, changes two verdicts (112 and 114)
and brings agreement to 197 of 204. No other example is affected, and the choice of
quantifier-scope convention affects none. `summary.json` has all six combinations.

## Sentences and formulas are not always aligned

In ten examples, from four stories, the number of premise sentences differs from
the number of premise formulas:

| Examples | Sentences | Formulas | What happens |
|---|---|---|---|
| 9, 10, 11 | 6 | 5 | One sentence is broken across two lines. |
| 87 | 8 | 7 | The last sentence has no formula. |
| 105, 106, 107 | 5 | 6 | One formula states background knowledge that no sentence gives. |
| 173, 174, 175 | 7 | 6 | One sentence has no formula. |

This does not touch the verdicts above, which use only the formulas. It matters
for anything that formalizes sentence by sentence: a rule of "exactly one formula
per line" cannot be met on these rows for reasons that have nothing to do with the
model. The model path in `engine/commonground/formalize.py` therefore accepts
several formulas, or none, for one line, and records which line each formula came
from.

## What this is not

Annotation noise in FOLIO has been reported by others. This file adds
machine-checked evidence for nine specific validation examples at one revision. It
is not a claim of novelty and not a re-annotation. The dataset is not
redistributed here; rows are identified by line number only.
