# Common Ground

Does a conclusion follow from the premises someone gave for it? And when two
positions disagree, where exactly, and what could both still hold?

Common Ground answers those two questions for arguments written as first-order
formulas, and says what backs each answer: an explicit model, a refutation, or a
proof checked by the Lean 4 kernel. It certifies **deductions, not truth**. Whether
a premise is true, and whether a formula says what a sentence meant, stay separate
questions with separate evidence.

It has two parts:

* `engine/`: a Python logic engine (parser, two solvers, Lean certificates,
  conflict analysis, a benchmark);
* a web app that walks through one sourced policy debate using the engine's output.

## What has been shown, and by what

| Claim | Evidence | Reproduce |
|---|---|---|
| Given FOLIO's own formulas, the engine's verdict equals FOLIO's label on **195 of 204** validation examples (95.6 %) | run recorded in `results/folio-validation/` | `python -m commonground folio --out out --lean` |
| The other 9 are places where the dataset's formulas do not yield the dataset's label | two re-checked models or a kernel-checked proof per example: [`AUDIT.md`](results/folio-validation/AUDIT.md) | same |
| Every "follows" / "contradicts" verdict of that run is **certified by the Lean kernel: 128 of 128**, in about 2 s | `summary.json` → `lean` | same |
| Lean accepted **0 of 278** false statements offered to it (the opposite of each verdict, both directions for the open ones) | `summary.json` → `lean` | same |
| Every "does not follow either way" verdict (75) comes with two finite models, re-checked by an evaluator that imports no solver | `engine/commonground/model.py`, `per_example.csv` | same |
| A second, independent engine (grounding to SAT) agrees on **201 of 201** examples where it is definite | `summary.json` → `second_engine` | same |
| In the worked debate the two positions are compatible, and each proof's premise list is exactly the one minimal set that entails its conclusion | `contracts/analysis.generated.ts`, `contracts/analysis.test.ts` | `npm test` |

The CI workflow re-runs all of it on every push, including the benchmark, and
fails if a published number changes (`.github/workflows/ci.yml`).

### What has not been shown

* **No language model was run for these numbers.** The benchmark starts from the
  dataset's formulas. It measures the logic back end and audits the annotations;
  it is a ceiling for any formalizer scored against those labels, not a result
  about formalization.
* **The language-model formalizer (`engine/commonground/formalize.py`) has never
  called a live model.** It is unit-tested against a scripted client and a local
  HTTP stub. The row it would fill is empty:

  | Mode | Accuracy on FOLIO validation | Accuracy when it answers |
  |---|---|---|
  | model answers directly | not run | not run |
  | model formalizes, solver decides | not run | not run |

  ```bash
  export LLM_API_KEY=...   # any OpenAI-compatible endpoint
  python -m commonground folio --mode direct --base-url https://… --model … --out results/direct
  python -m commonground folio --mode llm    --base-url https://… --model … --out results/llm
  ```
* **Faithfulness is not certified by anything here.** A formula can be provably
  entailed and still not say what the sentence meant.
* The interface changes in this version were type-checked and built, not viewed in
  a browser. The default `Dockerfile` has not been built, and the CI workflow has
  not yet run on GitHub: until it has, "re-run by CI" below describes its
  configuration, not an observed result.

## How a verdict is produced

```
text (dataset / model / reviewer)
   │  fol.py        strict grammar → syntax tree; anything else is rejected
   ▼
premises, conclusion
   │  verdict.py    is "premises ∧ ¬conclusion" satisfiable? is "premises ∧ conclusion"?
   │                 Z3, with grounding to SAT (PySAT) as second engine and fallback
   ▼
True / False / Uncertain / Inconsistent / Undecided
   │  model.py      every "satisfiable" claim → explicit finite structure, re-evaluated
   │  lean.py       every "unsatisfiable" claim → Lean 4 theorem, kernel-checked, axioms audited
   ▼
verdict with evidence
```

Grounding is a decision procedure for sentences with no existential under a
universal (the Bernays–Schönfinkel class): 200 of the 203 parsed FOLIO examples.
Outside it, an "unsatisfiable" from grounding is reported as bounded, never as a
proof (`engine/commonground/ground.py`).

## Where two positions disagree

`engine/commonground/argmap.py` treats a debate as a set of formal statements owned
by positions and computes, by search:

* whether the positions are **compatible** (all premises together have a model);
* the **minimal conflicts** (minimal unsatisfiable subsets) when they are not;
* the **smallest concessions** that restore consistency (minimal correction sets);
* for each conclusion, every **minimal set of premises that entails it**.

Enumeration is MARCO with a SAT solver proposing subsets. It is tested against
brute force and against the hitting-set duality between conflicts and concessions.

```bash
cd engine
python -m commonground analyze examples/plastic_bags.json   # the sourced worked example: compatible
python -m commonground analyze examples/remote_work.json    # a constructed contradiction: 2 conflicts, 8 ways out
python -m commonground check --premise "∀x (Human(x) → Mortal(x))" --premise "Human(socrates)" \
                             --conclusion "Mortal(socrates)" --lean
```

## The web app

One debate (should a city adopt a well-designed single-use plastic bag policy?)
reconstructed as 15 statements with five sourced evidence records, four Lean
proofs and one negative control that Lean must reject. A certificate is active only
while Lean accepted the exact current source, the stored hash matches and every
premise it uses is approved; disputing a premise suspends the conclusions that
depend on it.

"A priority dispute, not a contradiction" used to be a sentence in the interface.
It is now computed: the engine finds a model of all premises of both positions and
the page says so, or lists the conflicts if there are any.

```bash
npm ci
cp .env.example .env          # DATABASE_URL (MySQL); REVIEWER_TOKEN to enable review
npm run db:push
npm run dev                   # http://localhost:3000
npm run lint && npm run check && npm test && npm run build
```

Without `REVIEWER_TOKEN` the app is read-only. Without a Lean executable
(`LEAN_BIN`, Lean 4.35.0) it shows the stored certificates and reports live
verification as unavailable; it never simulates a compiler result. CI runs Lean on
`proofs/` on every push.

## Security

Reading is public. Review decisions, AI drafts and Lean runs need a reviewer
token; there are rate limits, a strict Content-Security-Policy, and no secret in
the default container image. No text from a visitor or a model is ever passed to
Lean. Details, tests and known limits: [`SECURITY.md`](SECURITY.md).

## Repository map

```
engine/commonground/   fol.py parser · verdict.py · smt.py (Z3) · ground.py (SAT) · model.py (evaluator)
                       lean.py (certificates) · argmap.py (conflicts) · formalize.py (model, not run) · bench.py
engine/tests/          104 tests: properties, differential checks between engines, Lean soundness probes
engine/examples/       two debates as formulas
results/               benchmark output and the annotation audit
api/                   Hono + tRPC server, access control, Lean runner, AI drafts
contracts/             Lean sources, certificate hashes, generated analysis
db/                    schema, worked-example data, stored Lean outputs
proofs/                the worked example's Lean files
src/                   React interface
```

## How this was built

* The web app was scaffolded with Kimi's site builder; `api/ai-client.ts` and the
  build setup are that platform's template code.
* The logic engine, the access-control layer, the tests and this README were
  written with Claude (Anthropic) in one working session on 9–10 November 2026,
  following a review of the first version.
* Every number above was produced by the commands shown, with Python 3.13, Z3
  5.3.3, PySAT 1.9.dev21 and Lean 4.35.0. The CI workflow repeats the run.

## Limits

* One debate, entered by hand. There is no pipeline from prose to statements in
  the web app.
* First-order logic over one kind of object, without arithmetic or modality. Most
  real arguments are not deductive; this tool only sees the part that is.
* The conflict analysis enumerates all minimal conflicts, which is exponential in
  the worst case. It is meant for tens of statements.
* Limits and review state assume a single server process.

## Data and licence

* FOLIO (Han et al., *FOLIO: Natural Language Reasoning with First-Order Logic*)
  is licensed CC BY-SA 4.0. It is downloaded on demand and not redistributed;
  `results/` refers to examples by line number.
* The five evidence records quote short excerpts from their sources, each linked
  in the app.
* This repository has no licence file yet.
