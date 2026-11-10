# Common Ground

[![ci](https://github.com/ysmouhib/common-ground/actions/workflows/ci.yml/badge.svg)](https://github.com/ysmouhib/common-ground/actions/workflows/ci.yml)

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
| The path a language model's reply takes (JSON, validation, solver) adds no error of its own: fed the dataset's formulas, it returns the reference verdict on all 203 examples whose formulas parse, and no answer on the malformed one | `engine/tests/test_bench.py` | `FOLIO_DIR=… python -m pytest tests/test_bench.py` |
| In 10 of the 204 examples the dataset has a different number of sentences and formulas, so "one formula per sentence" cannot be met on them | [`AUDIT.md`](results/folio-validation/AUDIT.md) | same as the first row |
| In the worked debate the two positions are compatible, and each proof's premise list is exactly the one minimal set that entails its conclusion | `contracts/analysis.generated.ts`, `contracts/analysis.test.ts` | `npm test` |
| The web app does what this page says for a visitor and for a reviewer: 33 checks over real HTTP, MySQL, Lean and a browser, and 8 more on a deployment with no reviewer token | `e2e/run.mjs` | `npm run e2e` (below) |

The CI workflow (`.github/workflows/ci.yml`) re-runs all of it on every pull
request and on every push to `main`: the test suites, the benchmark (it fails if
a published number changes), and the end-to-end checks against the container
image built from the `Dockerfile`. The badge above shows the last run on `main`.

### What has not been shown

* **No language model was run for these numbers.** The benchmark starts from the
  dataset's formulas. It measures the logic back end and audits the annotations;
  it is a ceiling for any formalizer scored against those labels, not a result
  about formalization.
* **The language-model formalizer (`engine/commonground/formalize.py`) has never
  called a live model.** It is tested with scripted clients, a local HTTP stub and
  a replay of the dataset's own formulas. The rows it would fill are empty:

  | Mode | Accuracy on FOLIO validation | Accuracy when it answers |
  |---|---|---|
  | model answers directly | not run | not run |
  | model formalizes, solver decides | not run | not run |

  ```bash
  export LLM_API_KEY=...   # any endpoint that implements POST {base-url}/chat/completions
  python -m commonground folio --mode direct --base-url https://… --model … --out results/direct
  python -m commonground folio --mode llm    --base-url https://… --model … --out results/llm
  python -m commonground report results/direct results/llm
  ```

  `report` prints both accuracies with 95 % Wilson intervals and an exact McNemar
  test on the examples where exactly one of the two runs is right. With 204
  examples an interval reaches 3 to 7 points to each side, so a small difference
  between two runs is not evidence of anything, and the report shows that in
  numbers. A run is resumable, names its
  model and settings in `config.json`, and stops instead of scoring a provider
  outage as wrong answers. Providers differ: add `--no-json-mode` or
  `--no-temperature` for one that rejects `response_format=json_object` or any
  temperature but its default.

  The same three commands run from the repository's Actions tab: workflow
  `model-benchmark`, "Run workflow". It needs a repository secret `LLM_API_KEY`
  and uploads every reply and verdict.
* **Faithfulness is not certified by anything here.** A formula can be provably
  entailed and still not say what the sentence meant.
* **The container image has been built only by CI**, not on a developer machine.
  The hosted copy on the original platform has not been redeployed from this
  version.

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

Without `REVIEWER_TOKEN` the app is read-only, and its first log lines say so. Without a Lean executable
(`LEAN_BIN`, Lean 4.35.0) it shows the stored certificates and reports live
verification as unavailable; it never simulates a compiler result. A Lean run that
does not finish in time (`LEAN_TIMEOUT_MS`, 60 s by default) is reported as "no
verdict" and leaves the stored certificate as it was.

### End-to-end checks

```bash
npm run build && npm start &                       # the production build, with .env as above
E2E_REVIEWER_TOKEN=<the same token> npm run e2e    # add E2E_BASE_URL=… if not http://127.0.0.1:3000
```

They go through the real server, database and a Chromium browser
(`npx playwright install chromium` once): what an anonymous visitor can and cannot
do, a dispute suspending exactly the certificates that depend on the premise, a live
Lean batch, the response headers, the limits, and the page on a phone-sized screen.
The last check locks the address the checks ran from out for 15 minutes, to read
the message a locked-out reviewer gets, so restart the server before repeating
them. `E2E_READ_ONLY=1 npm run e2e` checks a server started without a token.

### Container

```bash
docker build -t common-ground .
docker run --env-file .env -p 3000:3000 common-ground
```

The image is built from source, holds no configuration and runs as an
unprivileged user. It contains no Lean, so it serves the stored certificates.

## Security

Reading is public. Review decisions, AI drafts and Lean runs need a reviewer
token; ten wrong tokens lock a client out; there are rate limits, a strict
Content-Security-Policy, and no secret in the default container image. No text
from a visitor or a model is ever passed to Lean. Each control, the test that
covers it and the known limits: [`SECURITY.md`](SECURITY.md).

## Repository map

```
engine/commonground/   fol.py parser · verdict.py · smt.py (Z3) · ground.py (SAT) · model.py (evaluator)
                       lean.py (certificates) · argmap.py (conflicts) · formalize.py (model, not run) · bench.py
engine/tests/          122 tests: properties, differential checks between engines, Lean soundness probes,
                       the model path with scripted clients
engine/examples/       two debates as formulas
results/               benchmark output and the annotation audit
api/                   Hono + tRPC server, access control, Lean runner, AI drafts
contracts/             Lean sources, certificate hashes, generated analysis (with api/: 43 tests)
db/                    schema, worked-example data, stored Lean outputs
proofs/                the worked example's Lean files
src/                   React interface
e2e/                   end-to-end checks against a running build
.github/workflows/     ci.yml (tests, benchmark, container, end-to-end) · model-benchmark.yml (manual)
```

## How this was built

* The web app was scaffolded with Kimi's site builder; `api/ai-client.ts` and the
  build setup are that platform's template code.
* The logic engine, the access-control layer, the tests and this README were
  written with Claude (Anthropic) in working sessions on 9–10 November 2026,
  following a review of the first version. I directed the work and decide what is
  claimed here.
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
  in the app. Each excerpt, date and author line was compared with the source
  page or PDF on 9–10 November 2026 and changed where it differed: one excerpt
  was not the source's wording, one stops before its sentence ends and is now
  marked as cut, one date was a day off, and one record's author, publisher and
  date lines now follow what the report prints.
* This repository has no licence file yet.
