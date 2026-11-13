# Common Ground v2 — Build Brief for Claude


---

## 1. Context: what Common Ground is today

You are extending **Common Ground**, a project built around one philosophy: **certify deductions, not truth**. Read the repository before writing anything: `README.md`, `SECURITY.md`, everything under `engine/commonground/`, `engine/tests/`, and the `api/` access-control layer. Then run the test suites.

Pinned facts about the current state (verified against the repo, do not re-litigate them):

- `engine/commonground/` contains: `fol.py` (strict first-order-logic parser, anything off-grammar is rejected), `verdict.py`, `smt.py` (Z3), `ground.py` (grounding to SAT, sound only in the Bernays–Schönfinkel class), `model.py` (explicit finite models re-evaluated by a solver-free checker), `lean.py` (Lean 4.35 kernel certificates), `argmap.py` (minimal conflicts / minimal correction sets / minimal premise entailment, enumerated with MARCO), `formalize.py` (LLM harness, **never run against a live model**), `bench.py`.
- The web app (Hono + tRPC, React, MySQL) walks through one hand-entered debate (plastic-bag policy): 15 statements, 5 sourced evidence records, 4 Lean proofs, 1 negative control Lean must reject. Reviewer-token access; disputing a premise suspends dependent certificates; strict CSP; rate limits; lockout; and **no text from a visitor or a model is ever passed to Lean**.
- Evidence discipline is the project's signature: README tables "What has been shown" and "What has not been shown"; every number reproducible by a command; CI fails if a published number changes; the FOLIO validation run (195/204, with a 9-example audit of the dataset's annotations) has every "follows"/"contradicts" verdict kernel-certified (128/128) and 0/278 false statements accepted by Lean.
- `formalize.py` already supports `python -m commonground folio --mode direct` and `--mode llm` benchmarking on FOLIO with 95% Wilson intervals and an exact McNemar test, resumable runs, `config.json` provenance, and a GitHub Actions workflow (`model-benchmark.yml`). Those README rows are **empty and waiting**.
- There is no LICENSE file yet. The owner has decided: **MIT** (see Phase 9).

## 2. Mission

Version 1 answers: *given premises, does this conclusion follow?*

Version 2 answers a deeper question: **given a body of text — a debate between two or more camps, or a monologue by one author — what are the foundational premises, the axioms, on which its claims are built? Which axioms are load-bearing? And where, exactly, do two thought systems diverge?**

The mechanism is reverse logic: the camp's endorsed claims are the theorems; you reconstruct minimal sufficient axiom systems, certify every step with a solver or the Lean kernel, rank candidate axioms by plausibility using textual evidence, and compute the reduced disagreement between camps.

Two success criteria, equally important:

1. **Scientifically plausible**: the reconstruction method is grounded in argumentation theory, logic, and belief-systems research, and documented as such.
2. **Actually usable**: anyone who clones the repo can analyze their own debate or monologue texts in minutes, on their own machine, with honest degradation when optional components (LLM key, Lean) are missing.

Product sentence: *Paste the texts of a debate (or one author's texts). Common Ground extracts the statements, reconstructs the unstated axioms that generate them, certifies every deduction with a kernel-checked proof or an explicit countermodel, and shows the provable common ground and the exact fault lines.*

## 3. Scientific grounding first (Phase R — research before product code)

Before implementing the reconstruction, make the central idea defensible to a reviewer, a journalist, and an academic. Produce two living documents:

- `docs/RESEARCH.md` — an annotated bibliography. Every entry: citation, one-paragraph summary, and **one line: "implication for the design"**.
- `docs/THEORY.md` — at most two pages, in the repo's plain voice: the epistemic model, the formal definitions of section 4, and the honest boundary. Code and UI cite it.

Starting map — refine it, do not blindly follow it:

**Argumentation and logic:**

- Toulmin's model (claim / data / warrant / backing / qualifier / rebuttal): the *warrant* is the unstated premise — candidate axioms are warrants. Decide the UI terminology: "axiom" vs "warrant" vs "implicit premise", with rationale.
- Enthymemes and implicit-premise reconstruction; argument mining corpora and warrant-identification literature (e.g., args.me-style corpora); documented failure modes of LLM-based implicit-premise extraction.
- Abduction: Peirce; weighted abduction (Hobbs et al.); abductive logic programming; formal characterizations of weakest sufficient / strongest necessary conditions. Justify the cost function of section 4 as weighted-abduction parsimony; connect to minimum description length if the literature supports it.
- Belief base revision (AGM and base-revision literature): what it means to remove an axiom and remain a coherent theory.
- Ontology debugging and axiom pinpointing / justification extraction: the closest engineering precedent for MUS-based explanation; cite how those systems present justifications to users.
- Prior art in argument formalization (legal argumentation AI, debate analysis): state explicitly what we do differently — axiom *extraction* from a corpus of positions, with kernel certificates.

**Psychology and political science:**

- Converse (1964) on belief-system constraint and centrality: justifies the load score as an operationalization of "centrality", and sets a falsifiable expectation (constraint) that the holdout test measures.
- Moral foundations theory, Schwartz's basic human values, sacred values (Tetlock): value dimensions as typological priors for candidate axioms, and the prediction that cross-camp divergence roots in value-level axioms rather than facts.
- Motivated reasoning and myside bias: predicts systematic formalization pitfalls; design mitigations for the review UI.
- Cognitive dissonance and strategic ambiguity: predicts internal inconsistencies in a camp's texts; interpret MUS findings carefully — never call a camp "irrational" in the UI; report, don't judge.
- Epistemic cognition: how people justify beliefs — informs how axiom cards are presented to lay users.

**Evaluation methodology precedents:** how comparable systems (argument mining, belief prediction from values, authorship analysis) validated their reconstructions; position our holdout test among them.

`RESEARCH.md` must answer, each with citations: (1) terminology decision; (2) is weighted parsimony the accepted formalization of plausible premise recovery?; (3) is load a defensible operationalization of centrality?; (4) closest prior art and our differentiation; (5) known failure modes of LLM implicit-premise extraction; (6) evaluation designs used by comparable systems.

Rules: every citation must be verified (title, authors, venue, year) against the actual source; if a source cannot be checked, mark it "unverified" or drop it. **Never invent a citation.** If working in an environment without web access, ask the owner to supply abstracts.

## 4. The formal core (implement exactly these definitions)

A **camp** C is a set of documents by one author or one coordinated campaign. From its texts, after human review:

- **Endorsed claims E(C)**: statements the camp asserts.
- **Rejected claims R(C)**: statements the camp denies, at two strengths: *firm* (the camp's theory must entail the negation) and *soft* (the theory must merely not entail them).

An **axiom system** A for camp C is a set of FOL formulas such that:

1. A is consistent;
2. A ⊨ e for every e ∈ E(C);
3. for firm rejections r: A ⊨ ¬r; for soft: A ⊭ r;
4. minimality: no axiom in A is entailed by the others.

**Selection criterion (weighted parsimony).** Among certified candidate systems, minimize:

> cost(A) = Σ\_{a ∈ A} (1 − plausibility(a)) + λ · |A|

with λ ≈ 0.3 initially, exposed as configuration. Plausibility(a) ∈ \[0,1\] is estimated by the proposing LLM and **must** come with at least one verbatim quote (document + span) supporting it. Report ties, never silently pick one. Phase R grounds this criterion; adjust the definition only with a written rationale in `THEORY.md`.

**Load score.** load(a) = |{ e ∈ E : every minimal premise set for e inside A contains a }|, computed from `argmap.py`'s minimal premise entailment. Every removal check is a certified counterfactual: removing a and re-deriving is a real entailment check, kernel- or solver-backed.

**Common ground** between camps: the set of statements entailed by both certified axiom systems.

**Reduced disagreement:** if A₁ ∪ A₂ is inconsistent, its minimal unsatisfiable subsets are the fault lines, each with its certificate. If consistent, the camps do not contradict — they diverge at the root: report the pairs (a₁, a₂) of load-bearing axioms such that neither system entails the other's axiom, ranked by how many downstream claims the pair explains. Craig interpolation (Z3 supports fragments) is an optional exploration; treat it as research, not a Phase requirement.

## 5. The two layers, and the mandatory language

- **Layer 1, probable (LLM).** Proposes candidate axioms and plausibility estimates, always grounded in textual evidence. The LLM is an untrusted generator everywhere.
- **Layer 2, certified (solvers + Lean kernel).** Decides sufficiency, consistency, negations, load. Nothing enters a published result without a certificate or an explicit model.

Never blur the layers. Use this vocabulary verbatim in UI, docs, and README:

- "These axioms are **verified sufficient** to generate this camp's claims." Never "these are their beliefs", never "the author thinks".
- "Certifies deductions, not truth" remains the motto.
- Every axiom card carries two independent badges: **SUFFICIENT (kernel-checked)** and **PLAUSIBLE (textual evidence)**, each clickable through to its evidence: certificate hash + Lean source, or the exact quotes with document and span.
- If an axiom is sufficient but implausible, or plausible but redundant, say exactly that in the card.
- Reports describe, never diagnose: no "irrational", no "wrong", no judgment of persons.

## 6. Product spec: clone, run, analyze

Two analysis modes:

1. **Monologue analysis** (one camp): statement list, certified axiom system with load ranking, internal consistency report (MUSes if the texts contradict each other), and the "what you would have to accept" view.
2. **Debate analysis** (two or more camps): everything above per camp, plus provable common ground, the reduced disagreement, and a per-claim cross-camp derivation viewer.

**Clone-and-run requirements (non-negotiable):**

- Fresh clone → first analysis in under 10 minutes, following only the README: `git clone`, `docker compose up` (app with a bundled demo analysis preloaded), or engine-only `uv pip install -e ./engine` + CLI.
- **Headless CLI**: `python -m commonground analyze <paths> --camp "NameA:file1,file2" --camp "NameB:file3" --out report/` produces a Markdown + JSON report with no server, no database, no browser. The CLI and the web app share one engine core.
- **Honest degradation matrix**, all modes first-class, no silent failures:
  - no LLM key → manual statement entry works; bundled precomputed analyses (plastic-bag, CO2) run fully;
  - no Lean install → solver-only verdicts, badges read **SOLVER-CHECKED (not kernel-certified)**, pending certificates shown as pending;
  - provider outage → shown as outage, never scored as a wrong answer.
- **Local-first privacy**: texts never leave the machine except calls to the LLM endpoint the user configures; document exactly what is sent; no telemetry or analytics.
- Seed data committed under `examples/`: the plastic-bag debate and the CO2 golden corpus.

## 7. Website and interface plan

The existing Hono/tRPC + React app grows into the user-facing product:

- **Pages**: landing (honest copy, quickstart, demo GIF or short clip), analysis wizard (paste text or URLs, server-side fetch, name camps, choose mode), review queue (statement + quote + FOL drafts, approve / edit / reject, dispute mechanism reused so disputing a premise suspends dependent certificates), results (camp tabs, axiom cards, common ground, reduced disagreement, derivation viewer: minimal premise set, certificate, model or countermodel, per-claim), public read-only share links, an "about / theory" page rendering `THEORY.md`, and a docs page.
- **Copy** follows section 5 verbatim. The landing page states the boundary ("certifies deductions, not truth") prominently.
- **Exports**: JSON and printable report.
- **Deployment**: one container image published to GHCR by CI; `docker compose` for local; a hosted demo instance is owner-deployed, rate-limited, preloaded analyses only for anonymous visitors. Private texts: local instance.
- **Quality bar**: mobile-readable reports, keyboard navigation, contrast, honest empty/error states.

## 8. Build plan: phases, each PR-sized with tests and docs

**Phase 0 — Baseline.** Read everything; run the engine tests, app tests, and e2e (with and without reviewer token); confirm the README numbers reproduce. Write `docs/PLAN.md`. No code changes.

**Phase R — Scientific grounding.** Section 3, in full: `docs/RESEARCH.md` + `docs/THEORY.md`. No product code. Runs on the lighter model (see CLAUDE.md); the owner supplies paper access if browsing is unavailable. Acceptance: every research question answered with verified citations; THEORY.md reviewed by the owner before any abduction code.

**Phase 1 — The formalizer goes live.** Fill the README's empty table: run `folio --mode direct` and `--mode llm` against a real endpoint, publish both rows with Wilson intervals and the McNemar test. Acceptance: numbers in README, `model-benchmark.yml` works, "What has not been shown" updated.

**Phase 2 — Text to statements.** Statement extraction with verbatim quotes and spans, schema-validated, resumable, provider-agnostic (reuse the `formalize.py` harness patterns: config provenance, outage ≠ wrong answer, `--no-json-mode` / `--no-temperature` flags). Property tests: every span exists in the source text, atomicity heuristics, determinism at temperature 0.

**Phase 3 — The abduction engine** (new `engine/commonground/abduce.py`): write the design doc first (`docs/design/abduction.md`), citing `THEORY.md`; design review on the strongest model. Then: an LLM-independent candidate-generation interface (scripted clients for tests), sufficiency / consistency / negation checking via the existing solvers, Lean certificates for sufficiency proofs, cost-minimal search over certified subsets (branch-and-bound; cross-checked against brute force in tests, mirroring how `argmap.py` is tested), and negative controls: for a certified axiom set, Lean must reject the negations.

**Phase 4 — Load analysis and per-camp reports.**

**Phase 5 — Cross-camp analysis**: common ground, reduced disagreement.

**Phase 6 — Web app**: the full flow of sections 6–7, reusing reviewer tokens, dispute suspension, rate limits; extend the e2e suite (currently 33 + 8 checks).

**Phase 7 — Golden dataset.** The Swiss CO2-law votation of 13 June 2021 (rejected 51.6%): campaign materials archived at swissvotes.ch (vote 644). Camp No (the referendum committee of the auto, building and oil industries): costs about CHF 1,000 per household per year, unfairness, and the effectiveness argument "Switzerland emits only \~0.1% of global GHG, so the law cannot help the climate". Camp Yes (scientists, cities, business associations): glacier loss, responsibility, early action cheaper than repair. Hand-work the golden reconstruction first — statements, formalizations, candidate axioms, expected load ranking — then make the pipeline reproduce it; every divergence becomes an entry in the error taxonomy. Also in this phase: the CLI runs both bundled examples headless, end to end.

**Phase 8 — Evaluation.** Abduction benchmark on FOLIO: hide premises, check whether the system recovers *sufficient* premises (sufficiency is the graded criterion). Holdout test on the CO2 corpus: remove some published statements of a camp, extract axioms from the rest, check whether the extracted system still derives the withheld statements. Publish all numbers in README style with reproduce commands.

**Phase 9 — Release readiness.** MIT `LICENSE` (file lands here at the latest; earlier at the owner's discretion). README: badges (CI, MIT, Python/Node versions), quickstart, demo media, links to `THEORY.md` and `RESEARCH.md`. `CONTRIBUTING.md` (dev setup, test commands, PR checklist, the rule that merged numbers must be reproducible), `CODE_OF_CONDUCT.md` (Contributor Covenant), `CHANGELOG.md` (Keep a Changelog; tag `v2.0.0`), issue templates (bug / feature / research question), PR template, engine packaging (PyPI, name decision recorded in the plan), CI publishing the container to GHCR, `SECURITY.md` refresh, `examples/` index. Acceptance: a person outside the project clones on a clean machine and completes an analysis in under 10 minutes following only the README; every badge and claim in the README is true.

## 9. Evidence plan: keep the repo's signature discipline

- Every new capability gets a "What has been shown, and by what" row with a reproduce command; extend `ci.yml` so CI fails if a published number changes.
- Update "What has not been shown" in every phase. It is the honesty ledger.
- Never fabricate a number. If no LLM endpoint is available, write "not run". The same rule applies to citations (section 3).
- Maintain `AUDIT.md` for the error taxonomy: formalization error / insufficiency / misattributed axiom / spurious minimality — with counts and examples, like the FOLIO annotation audit.

## 10. Non-negotiable engineering standards

- Untrusted LLM everywhere it appears: schema validation, timeouts, provider outage is never scored as a wrong answer, and no LLM output reaches Lean without human approval.
- FOL only. Document the Bernays–Schönfinkel boundary the way `ground.py` does. Numeric thresholds ("1.5 °C", "net zero by 2050") are atomic predicates; there is no arithmetic.
- Conflict enumeration stays exponential: cap input sizes, document the "tens of statements" scope.
- Do not break the plastic-bag debate; it is the regression anchor.
- Same stack: Python 3.13 engine, Hono/tRPC + React app. Argue in `docs/PLAN.md` before adding any framework or dependency.
- Security posture unchanged: public reads, reviewer token for mutations, CSP, rate limits, lockouts, no secrets in the container.
- No telemetry, analytics, or tracking of any kind.

## 11. Non-goals

- No arithmetic, modality, or temporal logic.
- No claim of reading minds or recovering "true beliefs". The product claim is verified sufficiency, always.
- No removal of the human review layer; you may only build assistance for it.
- No new hand-entered debates except the golden CO2 corpus.

## 12. How you (Claude) should work

- Follow the model strategy in `CLAUDE.md`: routine work stays on the lighter model; the strong model is reserved for the escalation list (abduction design, cross-camp algorithm, Lean edge cases, grammar edge cases, stubborn bugs, final THEORY review).
- Phase R before Phase 3 code: the abduction engine implements `THEORY.md`, not the other way round.
- Plan first, then phase by phase, each a small reviewable change. No big-bang rewrite of the existing engine or app.
- Use your deepest reasoning mode for the abduction search, the cost minimization, and the definitions of section 4; write short soundness and termination notes in docstrings; in tests prefer brute-force cross-checks over cleverness.
- Be adversarial with your own output: before declaring an axiom system certified, try to break it — a claim it does not entail, a contradiction smuggled in, a redundant axiom, a rejection it violates.
- Write documentation in the repo's existing voice: plain sentences, owner claims backed by commands, no marketing language.
- When a number matters, run the command; when you cannot, write "not run". When a citation matters, verify it; when you cannot, mark it or drop it.
- At the end of each phase, update both README tables, `SECURITY.md` if the surface changed, and `docs/PLAN.md` with what remains.

## 13. First-session checklist

1. Read `README.md`, `SECURITY.md`, `engine/`, `api/`, `contracts/`, `e2e/`; run the engine tests, `npm test`, and the e2e suite with and without `REVIEWER_TOKEN`.
2. Write `docs/PLAN.md` mapping the phases (0, R, 1–9) to PR-sized steps, with what each phase changes, how it is tested, and which steps need the strong model.
3. Start Phase R (research and theory docs) before Phase 1; if an LLM endpoint is available in parallel, Phase 1 may run alongside.
4. Deliver the CO2 golden corpus skeleton: `examples/co2-2021/` with the source list, camp definitions, and the first hand-worked statement lists as the target output.