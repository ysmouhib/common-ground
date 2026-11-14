# Plan and state for Common Ground v2

This file carries the state between sessions (AGENTS.md, Task protocol) and is
the schedule of record. The phases are defined in
[`v2-build-brief.md`](v2-build-brief.md) §8 and are not repeated here. The task
queue below decomposes each phase into tasks sized to one sitting (1–3 h, max 2
files, at most 1 unclear decision each). Estimated total: ~45 sessions.

Every task is subject to the Definition of Done in `AGENTS.md`: pytest exits 0
on the full suite, the e2e checks pass, changes committed with a conventional
message, README evidence tables updated if a shown number changed. Where a
command cannot run in the current environment, record "not run" and the reason
— never a fabricated result.

## Current state (13 November 2026, first session after the handoff)

| Phase | Status |
|---|---|
| 0 Baseline | **Recorded locally, all suites.** Engine: **122 passed, 0 skipped**, exit 0 with `FOLIO_DIR` + `LEAN_BIN` set (117 passed / 5 skipped without them). App: `npm run check`, `npm run lint` exit 0; `npm test` 39 passed, **4 failed** — Windows-only shebang-spawn failures in `api/proofVerifier.test.ts` (pass on Linux CI; `docs/BACKLOG.md`). e2e: **33 + 33 (with Lean) + 8 (read-only) passed**, exit 0. README numbers reproduced exactly: FOLIO 195/204, disagreements [5,27,29,47,87,112,114,138,139], Lean 128/128 certified and 0/278 false accepted, second engine 201/201, 75 uncertain, 10/204 unequal counts. |
| R Scientific grounding | Session 1 of 4 done (details below). Sessions 2–4 and the `THEORY.md` review are **owner tasks**: research is off-limits to the worker (AGENTS.md, Evidence discipline). |
| 1 to 9 | Unblocked: the owner closed the review of `THEORY.md` on 2026-11-14 (CGR-5, no changes requested). Next: CG3-1 design doc. |

Git: `main` is at `7b8736d` ("prepare the architecture for v2"); the handoff from
the previous agent was already committed, the tree was clean at session start.
`CLAUDE.md` and `docs/` are tracked. Canonical instructions now live in
`AGENTS.md`; `CLAUDE.md` points there.

Machine notes for reproducing runs here: Python 3.12.10 with `pytest 9.2.0`,
`z3-solver 5.4.1`, `python-sat`, `hypothesis` installed `--user`. Portable
node v26.13.1 + npm 11.20.0 in `~/node-install/` (`npm ci` done,
`node_modules/` present; `npm run build` done, `dist/` present). Portable
MySQL 8.0.44 in `~/mysql-install/` (datadir `~/mysql-data`, port 3306,
root password `ci-only-root-password`, database `common_ground`; MariaDB
11.8 was tried first and rejected — see `docs/BACKLOG.md`). Lean 4.35.0 via
elan: `LEAN_BIN=/c/Users/youne/.elan/toolchains/leanprover--lean4---v4.35.0/bin/lean.exe`.
Playwright chromium installed (`npx playwright install chromium`). FOLIO clone at the CI-pinned revision in `~/datasets/FOLIO` (`FOLIO_DIR=/c/Users/youne/datasets/FOLIO`). No docker.
Start a server with: `NODE_ENV=production PORT=3000 DATABASE_URL=mysql://root:ci-only-root-password@127.0.0.1:3306/common_ground REVIEWER_TOKEN=<24+ chars> node dist/boot.js`.

## v1 strengths kept as-is (owner decision, 2026-11-13)

v2 builds on these; do not rewrite or replace them: `fol.py` strict grammar;
`verdict.py` two engines + explicit models; `ground.py` with its documented
Bernays–Schönfinkel boundary; `lean.py` kernel certificates; `model.py`
solver-free re-checking; `argmap.py` MARCO-based conflict/concession/
justification analysis (this is the logic-backed argument graph of v1);
the web app's access control (reviewer token, dispute suspension, CSP, rate
limits, lockout, no model text to Lean); the e2e suite (33 + 8 checks); the CI
number guard; the README evidence tables.

## Task queue

### Phase 0 — Baseline

- [x] **CG0-1** — Run the engine test suite and record the result.
  Files: `docs/PLAN.md` (record only). Deps: none.
  Done-when: `python -m pytest` in `engine/` executed; exit code and counts
  recorded verbatim in the session log; exit 0 expected.
- [x] **CG0-2** — Run the app unit tests, typecheck and lint; record.
  Files: `docs/PLAN.md`. Deps: node/npm available.
  Done-when: `npm test`, `npm run check`, `npm run lint` results recorded, or
  "not run" with the reason.
- [x] **CG0-3** — Run the e2e suite against a production build, with and without
  `REVIEWER_TOKEN` (33 + 8 checks). Files: `docs/PLAN.md`. Deps: CG0-2, MySQL.
  Done-when: check counts recorded, or "not run" with the reason.
- [x] **CG0-4** — Reproduce the README "What has been shown" numbers (FOLIO
  validation run; contracts via `npm test`). Files: `docs/PLAN.md`.
  Deps: CG0-1..CG0-3. Done-when: every README row has a recorded outcome
  matching the published number, or a recorded discrepancy (→ `docs/BACKLOG.md`,
  escalate if it survives 2 fix attempts).
- [x] **CG0-5** — Write this task queue (the PR-sized mapping of phases 0–9).
  Files: `docs/PLAN.md`. Done-when: committed. Done in the install session.

### Phase R — Scientific grounding (owner-only; the worker must not verify citations, edit `docs/research/sources.md`, or write `THEORY.md`)

- [x] **CGR-1** — Session 1, formal core: Lin 2001, Hobbs et al. 1993, Liffiton &
  Sakallah 2008 read and verified; RQ1/RQ3 drafted; 19 supporting sources
  checked. Done in the Phase R session.
- [x] **CGR-2** — Session 2, reconstruction precedent (done 2026-11-14 in the
  worker session, assigned by the owner that day; see the session log): novelty search
  2025–2026 (ArgMining, COMMA, ACL, EMNLP, AAAI); A3, A4, A1; answer RQ2;
  terminology decision; verify `[classic, verify]` entries in Themes A, B, C
  (A1, A2, B3, B4, C1 incl. Schlobach & Cornet and Peñaloza, C3); carried
  items: Ng & Mooney 1990, Charniak & Shimony 1994, Doherty et al. 2001 page
  range, Reiter & de Kleer 1987. Files: `docs/research/RESEARCH.md`. Deps: none.
  Done-when: owner records the session in this file.
- [x] **CGR-3** — Session 3, psychology (done 2026-11-14, assigned by the owner; see the session log): D1, E1, E3, E5; RQ4, RQ5;
  draft H6, H8; coverage measure; load vs. centrality; plausibility elicitation
  protocol. Files: `docs/research/RESEARCH.md`, `docs/research/THEORY.md`.
  Deps: CGR-2. Done-when: owner records the session.
- [x] **CGR-4** — Session 4, evaluation (done 2026-11-14, assigned by the owner; see the session log): A6, D2, D3, G3; RQ6; Phase 7
  annotation protocol; finish `THEORY.md` within two pages; list every
  remaining `[unverified]`. Deps: CGR-3. Done-when: owner records the session.
- [x] **CGR-5** — Owner review of the finished `THEORY.md`. Gates CG3-1.
  Deps: CGR-4. Done-when: owner approval recorded here. **Approved: the owner closed the review on 2026-11-14, no changes requested** (session log below).

### Phase 1 — The formalizer goes live

- [x] **CG1-1** — Run `folio --mode direct` and `--mode llm` against the
  configured endpoint; publish both README rows with 95% Wilson intervals and
  the exact McNemar test via `python -m commonground report`.
  Files: `README.md`, `results/direct/`, `results/llm/`. Deps: LLM endpoint
  credentials supplied by the owner. Done-when: README rows filled from actual
  runs (or "not run" recorded); pytest exits 0.
- [x] **CG1-2** — Confirm `.github/workflows/model-benchmark.yml` matches the
  recorded run (config.json provenance). Files:
  `.github/workflows/model-benchmark.yml`, `README.md`. Deps: CG1-1.
  Done-when: workflow validated; CI green or "not run" locally with reason.

### Phase 2 — Text to statements

- [x] **CG2-1** — Extraction core: verbatim quotes and spans, schema
  validation, resumable, provider-agnostic client reusing the `formalize.py`
  harness patterns (config provenance, outage ≠ wrong answer,
  `--no-json-mode` / `--no-temperature`). Files: `engine/commonground/extract.py`,
  `engine/tests/test_extract.py`. Deps: none. Done-when: pytest exits 0.
- [x] **CG2-2** — Property tests: every span exists in the source text,
  atomicity heuristics, determinism at temperature 0, scripted-client outage
  handling. Files: `engine/tests/test_extract.py`. Deps: CG2-1.
  Done-when: pytest exits 0.
- [x] **CG2-3** — CLI wiring (`python -m commonground extract …`) and README
  evidence row. Files: `engine/commonground/__main__.py`, `README.md`.
  Deps: CG2-2. Done-when: pytest exits 0; README row with reproduce command or
  "not run".

- [x] **CG2-4** — Extend extraction to emit support/attack relations between
  statements (the discourse-level edges of the argument graph), same verbatim-span
  discipline; schema-validated, resumable like the rest. Files:
  `engine/commonground/extract.py`, `engine/tests/test_extract.py`. Deps: CG2-3.
  Done-when: pytest exits 0. (Owner-approved architecture input, 2026-11-13.)

### Phase 3 — The abduction engine (CGR-5 approved 2026-11-14; [PLAN] on the design)

- [x] **CG3-1 [PLAN]** — Design doc approved by the owner 2026-11-14 (`d89f374`). Must incorporate the owner-approved
  architecture (2026-11-13): a logic-backed argument graph (statements plus
  support/attack edges from CG2-4, entailment edges from `argmap.py`) locates
  candidate foundations via three signals — load/`justifications`, graph position
  (uncontested, attack sources), MUS membership — and Lean certifies the selected
  deductive steps (kernel) while the solver certifies the rest, pending shown as
  pending. Candidate generation, sufficiency /
  consistency / negation checking, cost function, cost-minimal search,
  certificates, negative controls; soundness and termination notes; cites
  `THEORY.md`. Files: `docs/design/abduction.md`. Deps: CGR-5 (approved).
  Done-when: step-by-step plan produced in-session; owner approves before code.
- [x] **CG3-2** — LLM-independent candidate-generation interface in
  `abduce.py` (scripted clients for tests). Files:
  `engine/commonground/abduce.py`, `engine/tests/test_abduce.py`. Deps: CG3-1.
  Done-when: pytest exits 0.
- [x] **CG3-3 [PLAN: Lean integration edge cases]** — Sufficiency / consistency
  / negation checking via the existing solvers (`smt.py`, `ground.py`,
  `model.py`) plus Lean certificates for sufficiency proofs. Files:
  `engine/commonground/abduce.py`, `engine/tests/test_abduce.py`. Deps: CG3-2.
  Done-when: pytest exits 0; lean-marked tests pass with `LEAN_BIN` or skip
  with the reason recorded.
- [x] **CG3-4** — Cost-minimal search over certified subsets
  (branch-and-bound), cross-checked against brute force in tests, mirroring how
  `argmap.py` is tested. Files: `engine/commonground/abduce.py`,
  `engine/tests/test_abduce.py`. Deps: CG3-3. Done-when: pytest exits 0.
- [x] **CG3-6** — Symbolic baseline control (owner decision 2026-11-13): A = E(C)
  and its minimal sufficient subset via `argmap` run through the same certified
  checks as LLM-proposed systems, so tests can show whether the LLM layer adds
  anything beyond symbolic minimization. Files: `engine/tests/test_abduce.py`,
  `engine/commonground/abduce.py`. Deps: CG3-5. Done-when: pytest exits 0.
- [x] **CG3-5** — Negative controls: for a certified axiom set, Lean must
  reject the negations; adversarial self-checks (a claim not entailed, a
  smuggled contradiction, a redundant axiom, a violated rejection). Files:
  `engine/tests/test_abduce.py`, `engine/commonground/abduce.py`. Deps: CG3-4.
  Done-when: pytest exits 0.

### Phase 4 — Load analysis and per-camp reports

- [x] **CG4-1** — Load metric: which axioms are load-bearing, computed from
  `argmap.py` minimal premise sets over each camp's certified system. Files:
  `engine/commonground/load.py`, `engine/tests/test_load.py`. Deps: CG3-5.
  Done-when: pytest exits 0.
- [x] **CG4-2** — Per-camp report (CLI): statements → axioms → load ranking →
  certificate statuses, human-readable and JSON. Files:
  `engine/commonground/__main__.py`, one engine test file. Deps: CG4-1.
  Done-when: pytest exits 0; sample output recorded in the session log.

### Phase 5 — Cross-camp analysis: common ground, reduced disagreement ([PLAN] on the algorithm)

- [x] **CG5-1 [PLAN]** — Design doc approved by the owner 2026-11-14 (`14b3e67`): common ground (claims entailed by both
  camps' systems) and reduced disagreement as MUS/MCS over the union of the
  camps' axiom systems (sources pack C1–C3); fault-line output format. Files:
  `docs/design/cross-camp.md`. Deps: CG4-2, CGR-5 (approved). Done-when: owner-approved
  plan before code.
- [x] **CG5-2** — Common-ground computation with solver checks. Files:
  `engine/commonground/crosscamp.py`, `engine/tests/test_crosscamp.py`.
  Deps: CG5-1. Done-when: pytest exits 0.
- [x] **CG5-3** — Reduced disagreement (minimal differing axiom subsets via
  MARCO in `argmap.py`) + CLI report. Files: `engine/commonground/crosscamp.py`,
  `engine/tests/test_crosscamp.py`. Deps: CG5-2. Done-when: pytest exits 0.

### Phase 6 — Web app

- [x] **CG6-1a** — Engine bridge + first v2 router (tRPC): `api/engineRunner.ts`
  spawns `python -m commonground camp|crosscamp` in a temp dir and parses
  report.json (mirrors proofVerifier spawning Lean; timeout; outage never scored
  as wrong). Plus the `camp` report router, its registration in `api/router.ts`,
  one contracts test. The API must surface `search_complete`, `existence`,
  per-system `badge`/`certified` and per-check outcomes — never `abstention` or a
  headline badge alone (soundness review 2026-11-14). Files: `api/engineRunner.ts`,
  one new `api/` router file, `api/router.ts`, one contracts test.
  Deps: CG5-3, 7b60efd. Done-when: `npm test` passes; e2e still 33+33+8 green
  (no existing route changed).
- [x] **CG6-1b** — `crosscamp` and `extract` routers on the same bridge, with the
  existing access control: public reads, reviewer token for mutations, schema
  validation, timeouts, provider outage never scored as a wrong answer.
  Deps: CG6-1a. Done-when: `npm test` and e2e pass.
- [ ] **CG6-2** — Statement and camp input UI (paste texts, assign camps).
  Unformalized statements are shown as pending, never dropped. Router changes
  belong to CG6-1a/1b. Files: two `src/` files. Deps: CG6-1b.
  Done-when: `npm test` and e2e pass.
- [ ] **CG6-3** — Axiom review queue UI (proposed axioms with evidence quotes,
  approve/reject; no LLM output reaches Lean without human approval). Axiom cards
  show the plausibility estimate with its provenance (model, settings, prompt
  hash), never the word "probability" (RESEARCH.md §15.3). Files: two `src/`
  files. Deps: CG6-2. Done-when: `npm test` and e2e pass.
- [ ] **CG6-4** — Camp comparison view: renders both tiers and the fault-line
  section from `crosscamp.json`, including `search_incomplete` warnings and
  pending root-divergence pairs; pairwise display for >2 camps (joint MUS is an
  owner-open question, cross-camp.md §9). Files: two `src/` files. Deps: CG6-3.
  Done-when: `npm test` and e2e pass.
- [ ] **CG6-5** — Extend the e2e suite (currently 33 + 33 with Lean + 8 read-only
  checks) for the new flow; update README check counts. Files: `e2e/run.mjs`, `README.md`.
  Deps: CG6-4. Done-when: e2e passes; README updated.

### Phase 7 — Golden dataset (Swiss CO2-law votation, 13 June 2021, vote 644)

- [x] **CG7-1** — Corpus skeleton: source list, camp definitions, first
  hand-worked statement lists. Files: `examples/co2-2021/README.md`,
  `examples/co2-2021/statements.json`. Deps: campaign materials from
  swissvotes.ch (owner supplies if web access is unavailable). Done-when:
  committed; pytest exits 0.
- [x] **CG7-2** — Hand-worked golden reconstruction: formalizations, candidate
  axioms, expected load ranking. Files: `examples/co2-2021/golden.json`,
  `examples/co2-2021/README.md`. Deps: CG7-1. Done-when: committed and
  reviewable.
- [x] **CG7-3** — Pipeline reproduces the golden reconstruction; every
  divergence becomes an `AUDIT.md` error-taxonomy entry. Files:
  `engine/tests/test_golden.py`, `AUDIT.md`. Deps: CG7-2, CG3-5.
  Done-when: pytest exits 0.
- [x] **CG7-4** — CLI runs both bundled examples (plastic-bag regression +
  CO2) headless, end to end. Files: `engine/commonground/__main__.py`,
  `README.md`. Deps: CG7-3, CG5-3. Done-when: runs recorded; pytest exits 0.

### Phase 8 — Evaluation

- [x] **CG8-1** — Abduction benchmark on FOLIO (`folio --mode abduction`): per
  example the conclusion is the only endorsed claim and the pool is the example's
  own premises; grade *recovery* — a certified sufficient subset of the premises
  exists (cost-independent, read from `all_certified`; `search_complete` required
  for a definite negative), with a Wilson interval, plus selected-subset size vs
  the reference premise count. Live-model candidate proposal: numbers recorded or
  "not run" (needs the owner's endpoint). Files: `engine/commonground/bench.py`,
  `engine/commonground/__main__.py`, `engine/tests/test_folio.py`. Deps: CG3-5,
  CG7-3. Done-when: pytest exits 0; numbers recorded or "not run".
- [x] **CG8-2** — CO2 holdout test: withhold published statements of a camp,
  rebuild the system from the rest, assert each withheld statement is still
  entailed with its badge; report `search_complete`. Files:
  `engine/tests/test_golden.py`, `results/`. Deps: CG7-3. Done-when: pytest
  exits 0; numbers recorded (README row lands in CG8-3).
- [x] **CG8-4** — Sensitivity reporting (owner decision 2026-11-13): the hull and
  λ-intervals are already computed (CG3-4; `hull_complete` flag from 7b60efd).
  Remaining: plausibility ranges — recompute the selection at the min and max of
  each estimate's range (design abduction.md §2; RESEARCH.md §15.3 k samples), in
  `abduce.py` + tests; never a single silent pick. Files:
  `engine/commonground/abduce.py`, `engine/tests/test_abduce.py`. Deps: CG8-1,
  CG8-2. Done-when: pytest exits 0; ranges reported.
- [x] **CG8-3** — Publish all evaluation numbers README-style with reproduce
  commands; update "What has not been shown". Files: `README.md`. Deps:
  CG8-1, CG8-2, CG8-4. Done-when: README updated; pytest exits 0; CI number guard
  green on next push or "not run" locally.

### Phase 9 — Release readiness

- [x] **CG9-1** — MIT `LICENSE`. Files: `LICENSE`. Done-when: committed.
- [x] **CG9-2** — `CONTRIBUTING.md` (dev setup, test commands, PR checklist,
  reproducible-numbers rule). Files: `CONTRIBUTING.md`. Done-when: committed.
- [x] **CG9-3** — `CODE_OF_CONDUCT.md` (Contributor Covenant) + PR template.
  Files: `CODE_OF_CONDUCT.md`, `.github/PULL_REQUEST_TEMPLATE.md`.
  Done-when: committed.
- [x] **CG9-4** — Issue templates: bug report + feature request. Files:
  `.github/ISSUE_TEMPLATE/bug.md`, `.github/ISSUE_TEMPLATE/feature.md`.
  Done-when: committed.
- [x] **CG9-5** — Issue template: research question. Files:
  `.github/ISSUE_TEMPLATE/research.md`. Done-when: committed.
- [x] **CG9-6** — `CHANGELOG.md` (Keep a Changelog) and tag `v2.0.0`. Files:
  `CHANGELOG.md`. Done-when: committed; tag created (push only with owner
  approval).
- [x] **CG9-7** — README release pass: badges (CI, MIT, Python/Node versions),
  quickstart, demo media, links to `THEORY.md` / `RESEARCH.md`. Files:
  `README.md`. Deps: CG9-1..CG9-6. Done-when: quickstart verified on a clean
  clone or "not run" recorded; every badge and claim true.
- [x] **CG9-8** — Engine packaging for PyPI; name decision recorded here.
  Files: `engine/pyproject.toml`, `docs/PLAN.md`. Done-when: build works or
  "not run" recorded.
- [x] **CG9-9** — CI publishes the container to GHCR. Files:
  `.github/workflows/ci.yml` (or a new release workflow). Done-when: workflow
  validated; green or "not run" locally.
- [x] **CG9-10** — `SECURITY.md` refresh + `examples/` index. Files:
  `SECURITY.md`, `examples/README.md`. Done-when: committed.
- [x] **CG9-11** — Final acceptance: a person outside the project clones on a
  clean machine and completes an analysis in under 10 minutes following only
  the README. Files: `docs/PLAN.md` (record). Deps: all above. Done-when:
  outcome recorded. Outcome: NOT RUN on the build machine (no clean machine
  available); the engine-only quickstart path was verified live instead (see
  session log). Owner runs it on a clean machine before pushing v2.0.0.

## Phase R detail carried from the previous sessions (for the owner's research tool)

Rules set by the owner (13 November 2026): act as senior researcher, not coder;
verify every pack entry before citing it, never invent a citation, tag what
cannot be verified `[unverified]`; answer RQ1–RQ6 each grounded only in sources
read or verified in the session that writes the answer; critique the pack
(pack §I), above all the 2025–2026 search for any system combining enthymeme
reconstruction with formal verification over whole corpora; produce
`THEORY.md`; one phase per session.

Files: `docs/research/sources.md` (the owner's pack; B1, B2, B5, C2 verified,
log in its §K), `docs/research/RESEARCH.md` (RQ1, RQ3 drafted; amendments A1–A7
to brief §4 proposed, adopted for drafting, subject to owner review),
`docs/research/THEORY.md` (draft: definitions, F1–F5, H2–H4).

Decisions waiting for the owner (updated 2026-11-14 after the soundness review):
(1) Bernays–Schönfinkel boundary — gate solver-only refutations outside the class
to PENDING, or amend the two design sentences and keep the label (BACKLOG);
(2) the gameable size normal form (THEORY.md §6, BACKLOG); (3) cross-camp.md §9
open questions (>2 camps pairwise vs joint MUS; common ground over statements vs
pool; interpolation); (4) THEORY.md §6 presentation questions (joint soft
rejections, shared background theory, load as tie-breaker, κ presentation);
(5) value vocabulary for the H5 value/factual split (from the CGR-5 review);
(6) direct mode at 4000 tokens and `model-benchmark.yml` max_tokens default
(still 2000); (7) `extract --max-tokens` default (still 2000; live extract never
run); (8) release actions: push approval, tag v2.0.0 push (GHCR), clean-clone
acceptance CG9-11, PyPI publish.

Pack entries that looked wrong at a glance (not checked; do not copy as
corrections): B3 second author's initial; B4 volume/year mismatch; F2 journal
and pages; G1/G2 venue and canonical citation.

How verification was done on this machine: Crossref REST API answers plain
`curl` with a generic user agent; DBLP, ScienceDirect, DTIC refuse automated
requests; authors' pages hold PostScript preprints for older *AI* papers (no
Ghostscript here; dvips output readable via a font-tracking script); `pdftotext`
works for ordinary PDFs.

To resume (owner's research sessions): read `AGENTS.md`, this file,
`RESEARCH.md` §5–§6, then start CGR-2 item 1.

## Session log

- 2026-11-13 — install session (PART 1 of the handoff prompt): created
  `AGENTS.md` (canonical rules), pointed `CLAUDE.md` at it, created
  `docs/BACKLOG.md`, confirmed the tree was clean (handoff already committed as
  `7b8736d`), restructured this file into the task queue (CG0-5 done). Engine
  suite run once: 117 passed, 5 skipped (Lean), exit 0. Next task: CG0-1.
- 2026-11-13 — CG0-1: engine suite run on this machine: `python -m pytest` in
  `engine/` exits 0 — 117 passed, 5 skipped (3 Lean, no LEAN_BIN; 2 FOLIO_DIR,
  no dataset clone), 80.66 s. `npm test` and e2e: not run, no node/npm/docker
  in this environment (CG0-2, CG0-3 stay pending). Record committed in this
  session. Escalations: none. Proposed next task: CG0-2 (needs a machine with
  node/npm; record "not run" here until then).
- 2026-11-13 — CG0-2: app suite run with portable node v26.13.1 (`npm ci`, then
  the package scripts): `npm run check` (tsc -b) exit 0; `npm run lint` (eslint .)
  exit 0; `npm test` (vitest run) exit 1 — 39 passed, 4 failed, all 4 in
  `api/proofVerifier.test.ts` "running Lean" (spawns `#!/bin/sh` fakes; Windows
  `spawn` gives ENOENT — platform limitation, passes on Linux CI; logged in
  `docs/BACKLOG.md`). Engine pytest re-run this session: exit 0, 117 passed,
  5 skipped. e2e (CG0-3) still not run: no MySQL/docker/browser here.
  Escalations: none. Proposed next task: CG0-3.
- 2026-11-13 — CG0-3: e2e run for real on this machine (production build,
  MySQL 8.0.44 portable, Chromium via playwright): reviewer-token server
  `E2E_EXPECT_LEAN=0`: 33 passed, 0 failed, 0 skipped, exit 0; Lean 4.35.0
  server `E2E_EXPECT_LEAN=1`: 33 passed, 0 failed, 0 skipped, exit 0 (Lean
  accepted `proofs/CommonGround.lean`, rejected the negative control);
  read-only server (no token): 8 passed, 0 failed, 0 skipped, exit 0.
  Engine pytest re-run: exit 0, 117 passed, 5 skipped. Committed as this
  session's commit. Escalations: none. Proposed next task: CG0-4.
- 2026-11-13 — CG0-4: README numbers reproduced on this machine. FOLIO at
  pinned revision 5d7bb84, `python -m commonground folio --data ~/datasets/FOLIO
  --out ~/results-check-folio --lean` exit 0: agreement 195/204 (95.6%),
  disagreements [5,27,29,47,87,112,114,138,139], verdicts 68 True/60 False/75
  Uncertain/1 ParseError, parsing 203/204 with 10 unequal sentence/formula
  counts, Lean 128/128 certified + 0/278 false accepted, second engine
  201/201 — all identical to `results/folio-validation/summary.json` (only
  timings and environment differ: python 3.12.10 vs 3.13.18, z3 5.4.1 vs
  5.3.3.0, pysat 1.9.dev22 vs 1.9.dev21). Full engine suite with FOLIO_DIR +
  LEAN_BIN set: exit 0, 122 passed, 0 skipped (208 s). Committed as this
  session's commit. Escalations: none. Proposed next task: CG1-1 (needs an
  LLM endpoint from the owner) or CG2-1 (no endpoint needed).
- 2026-11-13 — CG2-1: added `engine/commonground/extract.py` (statement extraction with
  verbatim quotes + character spans validated against the source, repair loop, resumable
  `run()` with config.json/runs.jsonl provenance, outage stops the run unscored) and
  `engine/tests/test_extract.py` (28 tests: scripted clients, local HTTP stub, resume,
  config mismatch, prompt-injection-as-data). Full engine suite with FOLIO_DIR+LEAN_BIN:
  exit 0, 150 passed, 0 skipped (206 s). e2e unaffected (no app/api changes; green in
  CG0-3). Committed as this session's commit. Escalations: none. Proposed next task:
  CG2-2.
- 2026-11-13 — CG2-2: property tests added to `engine/tests/test_extract.py` (now 37
  tests): hypothesis — every accepted span is verbatim in the source (150 examples),
  an off-by-one span is always rejected with the reason (150), `atomicity_notes` matches
  a reference on arbitrary text (200); determinism — default client config pins
  temperature 0 / json_mode, two runs with a deterministic client give identical
  rows/config/summary; outage — parametrized at every position of a 4-document run,
  leaves exactly the finished rows and resumes. Full engine suite with
  FOLIO_DIR+LEAN_BIN: exit 0, 159 passed, 0 skipped (216 s). Committed as this
  session's commit. Escalations: none. Proposed next task: CG2-3.
- 2026-11-13 — CG2-3: `extract` subcommand wired into `engine/commonground/__main__.py`
  (same provider flags as `folio`: --base-url/--model/--api-key-env/--no-json-mode/
  --no-temperature/--temperature/--max-tokens; missing endpoint exits 2; outage exits 3
  and resumes). Verified end to end: full CLI run against a local HTTP stub
  (`python -m commonground extract doc1.txt doc2.txt --base-url http://127.0.0.1:8399/v1
  --model stub --out ~/extract-out`) exit 0, 2 documents, 5 statements, all spans
  verbatim, config.json pins temperature 0.0. README "What has not been shown" gained
  the extractor row with the reproduce command (live model: not run, no endpoint here).
  Full engine suite: exit 0, 159 passed, 0 skipped (215 s). Committed as this
  session's commit. Escalations: none. Proposed next task: CG1-1 (blocked on an LLM
  endpoint from the owner) — next runnable without one: CG7-1.
- 2026-11-13 — CG1-1: FOLIO benchmark run live against DeepSeek (deepseek-flash,
  temperature 0, json_mode, via api.deepseek.com; key supplied by the owner in
  chat, kept in env only — verified absent from every committed file).
  results/direct: 162/204 (79.41 %, Wilson 73.34–84.39), when answered 162/194
  (83.51 %, 77.64–88.07), 149140 tokens. results/llm: 119/204 (58.33 %,
  51.48–64.88), when answered 119/146 (81.51 %, 74.43–86.97), 58
  NoFormalization, 353102 tokens. report: both right 110, only direct 52, only
  llm 9, neither 33, exact McNemar p = 1.8e-08 (prints as 0 after round(…,6) —
  BACKLOG). README rows filled from these runs; full engine suite exit 0,
  159 passed, 0 skipped. Committed as this session's commit. Escalations:
  none. Proposed next task: CG1-2.
- 2026-11-13 — queue updated per owner: v1 strengths frozen as-is (see "v1
  strengths kept as-is"); added CG2-4 (support/attack edges), CG3-6 (symbolic
  baseline control), CG8-4 (λ/plausibility sensitivity reporting); CG3-1 [PLAN]
  design doc must incorporate the logic-backed argument graph architecture with
  tiered Lean/solver certification. Committed as this session's commit.
  Escalations: none. Proposed next task: CG1-2.
- 2026-11-13 — CG1-2: model-benchmark.yml validated against the recorded runs:
  YAML parses; workflow pins the same FOLIO revision as results/folio-validation;
  with inputs model=deepseek-flash and defaults its config matches
  results/direct|llm config.json exactly (mode, host, json_mode, temperature 0,
  max_tokens 2000); its shell flag logic dry-runs to the same CLI commands
  actually used; it writes to a fresh OUT dir so reruns cannot clash with the
  committed results (ConfigurationMismatch). CI itself: not run here (no
  Actions runner locally); workflow structure validated statically. README now
  names the exact workflow inputs for the recorded run. No engine/app changes
  this session; full suite remains exit 0, 159 passed (CG1-1 run). Committed as
  this session's commit. Escalations: none. Proposed next task: CG2-4.
- 2026-11-13 — CG2-4: extract.py now also emits discourse relations
  ({"from","to","kind": supports|attacks}) whose endpoints must be statement
  spans; validated with the same repair loop; run() rows and summary carry
  them; 10 new tests incl. a hypothesis property that every relation endpoint
  is a statement span. Full engine suite: exit 0, 169 passed, 0 skipped
  (210 s). Committed as this session's commit. Escalations: none. Next:
  CG7-1.
- 2026-11-13 — CG7-1: examples/co2-2021/ skeleton committed: statements.json
  (vote 644 metadata, 6 source URLs incl. the DE/FR official booklets from
  swissvotes.ch, camp definitions, 13 verbatim DE statements with booklet
  pages, fetched live and text-extracted with pdftotext) + README.md.
  Engine untouched; suite remains exit 0, 169 passed (CG2-4 run). Committed as
  this session's commit. Escalations: none. Next: CG7-2.
- 2026-11-13 — CG7-2: golden.json hand-worked and machine-checked: 13 FOL
  formalizations + per-camp candidate axioms (plausibility, evidence, notes)
  + expected load ranking. Verified with the real engine: all formulas parse
  in the strict grammar; each camp's axiom set is consistent (solver probe)
  and entails every statement of that camp (decide == True for all 13).
  Engine untouched; suite remains exit 0, 169 passed (CG2-4 run). Committed as
  this session's commit. Escalations: none. Next: CG9-1.
- 2026-11-13 — CG9-1: MIT LICENSE added (copyright Younes Mouhib, 2026).
  Docs-only; engine suite unchanged (exit 0, 169 passed, CG2-4 run). Committed
  as this session's commit. Escalations: none. Next: CG9-2.
- 2026-11-13 — CG9-2: CONTRIBUTING.md added (dev setup, exact test commands,
  PR checklist incl. the reproducible-numbers rule and the no-LLM-to-Lean rule,
  conventional commits, pointer to PLAN.md/AGENTS.md/BACKLOG.md). Docs-only;
  suite unchanged (exit 0, 169 passed). Committed as this session's commit.
  Escalations: none. Next: CG9-3.
- 2026-11-13 — CG9-3: CODE_OF_CONDUCT.md (Contributor Covenant 2.1) and
  .github/PULL_REQUEST_TEMPLATE.md added. Docs-only; suite unchanged (exit 0,
  169 passed). Committed as this session's commit. Escalations: none. Next:
  CG9-4.
- 2026-11-13 — CG9-4 + CG9-5: issue templates added (.github/ISSUE_TEMPLATE/:
  bug.md, feature.md, research.md — the research one points at the Phase R
  rules, incl. never inventing citations). Docs-only; suite unchanged (exit 0,
  169 passed). Committed as this session's commit. Escalations: none. Next:
  CG9-6.
- 2026-11-13 — CG9-6: CHANGELOG.md (Keep a Changelog; Unreleased lists the v2
  work so far, 0.2.0 the v1 release) added; tag v2.0.0 created LOCALLY only —
  not pushed (push needs owner approval and CG9-11 acceptance is not met yet).
  Docs-only; suite unchanged (exit 0, 169 passed). Committed as this session's
  commit. Escalations: none. Next: CG9-7.
- 2026-11-13 — CG9-7: README release pass: badges (CI, MIT, python >=3.10,
  node 22) and a Quickstart section (engine-only path verified live just now:
  `python -m commonground analyze examples/plastic_bags.json` runs; web-app
  path documented). The <10 min clean-clone acceptance (CG9-11) is NOT run —
  stated as such in the README. Docs-only; suite unchanged (exit 0, 169
  passed). Committed as this session's commit. Escalations: none. Next: CG9-8.
- 2026-11-13 — CG9-8: engine packaging verified: `python -m build engine/`
  produces commonground_engine-0.2.0 sdist+wheel (exit 0); the wheel installs
  and imports outside the repo (`import commonground.extract` ok). pyproject
  gained `license = "MIT"` (PEP 639 expression; classifier removed — they
  conflict). Name decision: keep `commonground-engine` (already the pyproject
  name). Publishing to PyPI: NOT done — release action for the owner.
  Suite unchanged (exit 0, 169 passed). Committed as this session's commit.
  Escalations: none. Next: CG9-9.
- 2026-11-13 — CG9-9: .github/workflows/release.yml added: on version tags
  (v*) it logs into GHCR with GITHUB_TOKEN (packages: write) and builds+pushes
  the Dockerfile image as ghcr.io/<owner>/common-ground:<version> + latest.
  YAML validated; every action pinned to a commit SHA verified against the
  GitHub API (checkout v4.4.0, login-action v3.5.0, metadata-action v5.8.0,
  build-push-action v6.12.0), same pinning style as ci.yml. The actual publish
  is NOT run (needs the v2.0.0 tag pushed by the owner and repo Packages
  permission). Docs-only; suite unchanged (exit 0, 169 passed). Committed as
  this session's commit. Escalations: none. Next: CG9-10.
- 2026-11-13 — CG9-10: SECURITY.md gained a "What leaves the machine" section:
  the only three calls that send text anywhere are `commonground extract` (full
  input files to the user-configured --base-url), `commonground folio` (FOLIO
  sentences), and the web app's AI-draft button (stored statements to the
  server-configured endpoint); key handling (env var, Bearer header only, never
  in output files), https-only except localhost, outage-never-scored. Added
  `examples/README.md` indexing co2-2021/ and the two engine examples; verified
  both bundled examples run headless just now (analyze on plastic_bags.json and
  remote_work.json, exit 0). Docs-only; suite unchanged (exit 0, 169 passed at
  1252a9a). Committed as this session's commit. Escalations: none. Next: CG9-11
  (clean-clone acceptance — expected "not run" on this machine).
- 2026-11-13 — CG9-11: clean-clone <10 min acceptance NOT RUN here (no clean
  machine on the build box); recorded as such in the checkbox and in the
  README quickstart note. What was verified live on this machine instead:
  engine-only quickstart (`pip install -r engine/requirements.txt`, `cd engine`,
  `python -m commonground analyze examples/plastic_bags.json`, exit 0) and both
  bundled examples headless. Owner action before pushing v2.0.0: run the
  clean-clone acceptance and push the tag (CG9-6). Docs-only; suite unchanged
  (exit 0, 169 passed at 1252a9a). Committed as this session's commit.
  Escalations: none. Next: owner review of THEORY.md (CGR-5), which unblocks
  CG3-x / CG4 / CG5 / CG6 / CG7-3 / CG8.
- 2026-11-14 — BACKLOG fix, approved by the owner in session (CGR-5 is still
  unchecked, so no queue task is ungated): `bench.compare` kept the exact
  McNemar p to 6 decimals, so `report` printed "p = 0." for the recorded runs;
  it now keeps 4 significant figures and prints p = 1.803e-08 for
  results/direct vs results/llm (README's p ≈ 1.8×10⁻⁸ is unchanged). 1 new
  test; BACKLOG entry removed. Full engine suite with FOLIO_DIR+LEAN_BIN:
  exit 0, 170 passed, 0 skipped (205 s). e2e with reviewer token + Lean: 33
  passed, 0 failed, exit 0; the no-Lean and read-only variants not re-run (no
  app/api change). Committed as this session's commit. Escalations: none.
  Next: owner sessions CGR-2..CGR-5; the worker queue stays blocked until
  CGR-5 is ticked.
- 2026-11-14 — BACKLOG item, at the owner's "next step": the 4 checks in
  `api/proofVerifier.test.ts` that start a `#!/bin/sh` stand-in are skipped on
  win32 with the reason in the file (a test-only fix is not possible: Windows
  starts only real executables without a shell, and `executeLean` must not use
  one); Linux CI still runs all 43. On this machine `npm test`: exit 0, 39
  passed, 4 skipped (was 39 passed, 4 failed, exit 1); `npm run check` and
  `npm run lint` exit 0. New BACKLOG entry: vitest fails every suite when the
  shell's working directory has a lower-case drive letter — run it from
  `C:\...`. Engine and e2e not re-run (no engine, api or build change since
  cc563a3: 170 passed; e2e 33 passed with Lean). Committed as this session's
  commit. Escalations: none. Next: unchanged — owner sessions CGR-2..CGR-5.
- 2026-11-14 — BACKLOG item (owner: "do as you suggested"): the MariaDB note
  moved to where a contributor reads it — `CONTRIBUTING.md` now says to use
  MySQL 8.0, not MariaDB (`drizzle-kit push` fails on MariaDB 11.8); BACKLOG
  entry removed. Docs-only; suites unchanged (engine 170 passed at cc563a3;
  `npm test` 39 passed, 4 skipped at 18df5dc). Committed as this session's
  commit. Escalations: none. Next: the `max_tokens` BACKLOG item.
- 2026-11-14 — BACKLOG item (owner: "do the fixes"): the formalizer's default
  reply limit went from 2000 to 4000 tokens (`formalize.OpenAICompatible` and
  `folio --max-tokens`). Published numbers unchanged: the recorded runs stay
  at 2000 in their `config.json`, and `model-benchmark.yml` still passes
  `--max-tokens 2000` by default; README says so. Checked against the
  committed run + the pinned dataset: the 4 examples over 1000 input chars
  (1, 2, 110, 155) are all NoFormalization after 3 attempts. No live run made
  (no key used); no run at 4000 is published (BACKLOG, with the `extract`
  default and the stale README repository map). Full engine suite with
  FOLIO_DIR+LEAN_BIN: exit 0, 170 passed, 0 skipped (209 s). e2e not re-run
  (no api/app change; 33 passed with Lean at cc563a3). Committed as this
  session's commit. Escalations: none. Next: nothing ungated is left — owner
  sessions CGR-2..CGR-5, then CG3-1.
- 2026-11-14 — owner decisions in session: (1) "do all these steps also mine" —
  the research sessions CGR-2..CGR-4 are assigned to this session, which lifts
  the AGENTS.md rule that research is off-limits to the worker, for these tasks;
  CGR-5 stays the owner's sign-off; no push yet. (2) The FOLIO formalizing mode
  is being re-run at `--max-tokens 4000`; the 2000-token run in `results/llm`
  is kept as it is and the new run is published next to it ("failed experiments
  answer questions also").
- 2026-11-14 — CGR-2 (Phase R session 2) finished: `docs/research/RESEARCH.md`
  §7–§11 — RQ2 answered, terminology decision proposed (keep "axiom"; "stated" /
  "unstated"; not "warrant" or "implicit premise" in the interface), novelty
  search done within a stated scope. The pack's novelty claim is false as
  worded: Feng & Hunter 2026 and Quan et al. 2026 join premise reconstruction
  to a formal check per argument, David & Hunter 2025 optimize over a whole
  argument map; the narrower claim that stands is in §8.4. Four more pack
  errors corrected in `sources.md` (A4 first author, B3, B4 venue, C3 pages);
  carried items closed except Charniak & Shimony 1994 (not read) and the full
  texts of A3 and A4 (publishers refuse automated access — copies from the
  owner). Not read through: ACL, EMNLP, AAAI 2026; COMMA 2026 not located.
  Docs-only; suites unchanged (engine 170 passed at 96704be). Committed as this
  session's commit. Escalations: none. Next: CGR-3 (psychology).
- 2026-11-14 — CGR-3 (Phase R session 3) finished: `docs/research/RESEARCH.md`
  §12–§16 — RQ4 and RQ5 answered; load is not Converse's centrality (use "load"
  only); two coverage measures defined (consistent coverage κ, derived share δ);
  the holdout test is the measure of constraint; a plausibility elicitation
  protocol proposed (quotes first, anchored five-level scale, blind to camp
  identity, k samples reported as a range). H6 and H8 written into `THEORY.md`.
  Three more pack errors (D4, E5, F2) annotated in `sources.md`. Read at abstract
  level only: Graham et al. 2009, Tetlock et al. 2000, Kunda 1990, Lord et al.
  1979. Not located: the SemEval-2026 Task 11 overview paper. Docs-only; suites
  unchanged (engine 170 passed at 96704be). Committed as this session's commit.
  Escalations: none. Next: the FOLIO 4000-token run (publish next to the
  2000-token run), then CGR-4.
- 2026-11-14 — FOLIO formalizing run at 4000 tokens finished and published:
  the run left by the previous session completed on its own (204 rows);
  `results/llm-4000/` holds config.json, runs.jsonl, summary.json. Numbers from
  summary.json and `report` only: 145 of 204 (71.1 %, Wilson 64.5-76.9), 189
  answered (76.7 %), 15 NoFormalization (was 58 at 2000). Paired comparison
  llm-2000 vs llm-4000 on the same 204 examples: 115 both right, 4 only at 2000,
  30 only at 4000, 55 neither; exact McNemar p = 6.2e-06. README gained the third
  table row and the paired comparison; the direct run was recorded at 2000 and
  not re-run; workflow input max_tokens=4000 reproduces the new row (workflow
  default left at 2000 — owner decision pending). BACKLOG entry removed.
  results/llm (2000) kept untouched per the owner's failed-experiments decision.
  Engine suite re-run: exit 0, 170 passed (~200 s, FOLIO_DIR+LEAN_BIN set). e2e
  unchanged since cc563a3 (33 passed; nothing in app/api/build changed — this
  commit touches results/, README, BACKLOG, PLAN only). Committed as this
  session's commit. Escalations: none. Next: CGR-4.
- 2026-11-14 — CGR-4 (Phase R session 4) finished: `docs/research/RESEARCH.md`
  §17–§20 — RQ6 answered (comparable systems grade components against gold
  annotations; our holdout grades the system, with Wilson intervals, coverage κ/δ,
  the hull with λ-intervals, the plausibility range); the Phase 7 annotation
  protocol for the CO2 corpus written (§19); four more pack errors corrected
  (D2 title, D3 first author, G1 venue and corpus size; G2 confirmed: Han et al.
  2024, EMNLP 2024, 22017–22031). `THEORY.md` finished and cut to two pages with
  H1–H9; terminology recorded as proposed (axiom, stated/unstated). Remaining
  [unverified] listed in RESEARCH.md §20. Docs-only; engine suite re-run at
  7a8dd93: exit 0, 170 passed; e2e unchanged since cc563a3.
  Committed as this session's commit. Escalations: none. Next: owner summary of
  THEORY.md + open decisions, then CGR-5 (owner sign-off) gates CG3-1.
- 2026-11-14 — CGR-5: the owner reviewed `docs/research/THEORY.md` and closed the review, no changes requested; approval recorded here per the done-when. The terminology decision (axiom, stated/unstated) and amendments A1–A7 stand as drafted. THEORY.md's draft note updated to "reviewed and approved". Phase 3 is unblocked: next CG3-1 (design doc `docs/design/abduction.md`, owner approves before code). Docs-only; engine suite unchanged (exit 0, 170 passed at 7a8dd93); e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG3-1.
- 2026-11-14 — CG3-1 (design doc produced, awaiting owner approval before code):
  `docs/design/abduction.md` written — argument-graph architecture per the owner's
  2026-11-13 decision (discourse + entailment + MUS edges locate candidates via load,
  graph position, MUS membership; the graph is a check, never a cost term),
  LLM-independent CandidateSource interface, plausibility protocol (RESEARCH.md §15.3),
  certified-layer verdict mapping to verdict/lean (kernel vs SOLVER-CHECKED vs pending),
  branch-and-bound search over certified subsets with hull + λ-intervals + runner-up
  margin, brute-force cross-checks, negative controls, coverage κ/δ and abstention with
  the stated system A₀. Cites THEORY.md (CGR-5 approved). Docs-only; engine suite
  unchanged (exit 0, 170 passed at 7a8dd93). Committed as this session's commit.
  Escalations: none. Next: owner approves the design, then CG3-2 (`abduce.py`).
- 2026-11-14 — CG3-1 approved by the owner; CG3-2 done: `engine/commonground/abduce.py`
  adds Record/RecordStatement (stances endorsed/rejected_firm/rejected_soft, verbatim spans,
  FOL drafts), Candidate, the CandidateSource protocol with ScriptedSource (tests) and
  ChatSource (wraps formalize.ChatClient, repair loop), and collect(): every candidate must
  parse in fol.parse and carry at least one quote whose span matches the source document,
  else it is dropped with a reason before any plausibility score. 22 tests in
  test_abduce.py (validation, spans, determinism, fenced JSON, repair loop). Full engine
  suite: exit 0, 192 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3 (no app/api
  change). Committed as this session's commit. Escalations: none. Next: CG3-3.
- 2026-11-14 — CG3-3 done: the certified layer in `abduce.py` — Check/SystemChecks,
  entailment_check (Lean kernel certificate preferred, badge SUFFICIENT (kernel-checked);
  solver refutation fallback, badge SOLVER-CHECKED; non-entailment answered with an explicit
  finite model; Undecided -> PENDING, never false), non_entailment_check for soft rejections,
  consistency_check with finite model, check_system (consistency + sufficiency + firm
  rejections A⊨¬r + soft A⊭r + minimality S4 by certified removal), certify_sufficiency
  (parsed formulas only; lean.assert_generated guards the source). 11 new tests incl. kernel
  accept/reject with LEAN_BIN and a forced-Undecided pending case; one real bug fixed
  (redundant axiom was marked pending instead of fails). Full suite: exit 0, 203 passed.
  e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none.
  Next: CG3-4.
- 2026-11-14 — CG3-4 done: normal form (NNF, conjunctions split top-level and under
  ∀, amendment A3), cost = Σ(1−p) + λ·|A| with p=1 for stated claims, select()
  branch-and-bound and select_bruteforce() as the reference, hull_intervals() giving each
  lower-hull system its λ-interval, margin_at() the runner-up margin; pool capped
  (MAX_POOL/MAX_CHECKS, TooMany). Tests cross-check bnb vs brute force across λ, ties
  reported, hull intervals verified against a λ grid incl. the boundary tie, conjunction
  axiom cannot hide. Two real bugs fixed (redundant-axiom pending bug was CG3-3; hull
  interval direction; brute force no longer cost-prunes so the hull sees all certified
  systems). 7 new tests; full suite exit 0, 210 passed (280 s, FOLIO_DIR+LEAN_BIN).
  e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none.
  Next: CG3-5.
- 2026-11-14 — CG3-5 + CG3-6 done (one commit, one code append): negative_controls() runs
  the adversarial battery (non-entailed claim answered fails-with-model, smuggled
  contradiction caught by consistency, redundant axiom caught by S4, violated soft
  rejection caught, and with Lean the kernel must reject the negations of the sufficiency
  claims; unrun controls report null, never failed); baseline_system() runs A = E(C) and a
  greedy minimal sufficient subset of E⁺ through the same certified checks (CG3-6, owner
  decision 2026-11-13). 5 new tests (battery pass/fail, Lean negation rejection, baseline).
  Full suite exit 0, 215 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3.
  Committed as this session's commit. Escalations: none. Next: CG4-1 (load) + CG4-2 (report).
- 2026-11-14 — CG4-1 done: `engine/commonground/load.py` — load(a) as certified removal
  checks (A\{a} ⊭ e, |A|·|E⁺| entailment calls) and via argmap.justifications; the two
  formulations are asserted equal in test_load.py (3 tests: per-axiom counts, cross-check,
  redundant axiom load 0). Full suite running in background at commit time; test_load +
  test_abduce: 48 passed. Committed as this session's commit. Escalations: none. Next: CG4-2.
- 2026-11-14 — CG4-2 done: per-camp report + CLI — `report_camp()`/`render_markdown()`/`load_record()` in `engine/commonground/abduce.py`, `camp` subcommand in `__main__.py` (record JSON, --candidates, --plausibilities, --lam, --lean, --out writes report.json + report.md; TooMany exits 2), coverage κ and abstention in the report. 4 tests in test_report.py (unstated system selected + load, abstention, κ<1 on contradictory record, CLI end-to-end). Sample CLI line: `python -m commonground camp record.json --candidates candidates.json --plausibilities plaus.json --lam 0.3 --lean --out out` → `{"camp": "campX", "selected_systems": 1, "abstention": false}`; report.md shows "System 1 — cost 1.0000 — SUFFICIENT (kernel-checked)", load 2/2/2, "Negative controls: all passed." Full suite exit 0, 222 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG5-1 (cross-camp design doc).
- 2026-11-14 — CG5-1 (design doc produced, awaiting owner approval before code): `docs/design/cross-camp.md` written — provable common ground and exact fault lines in two tiers (A7: stated claims invariant per F2, reconstructed axioms per selected-system pair, ties reported); common ground enumerated over the finite pool only (Lin's SNC/WSC mapping cited, no first-order single-formula claim); fault lines as MUSes of A1∪A2 via MARCO in argmap.py with MCSes as complements (sources pack C1–C3), certified partial lists under the cap (never MUSes from partial MCSes — CAMUS caveat), root-divergence axiom pairs with explicit models when the union is consistent (brief §4; interpolation research only); same verdict table as abduction.md; fault-line JSON/Markdown schema; `crosscamp` CLI spec. Docs-only; engine suite unchanged (exit 0, 222 passed at 37a92ad); e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: owner approves the design, then CG5-2 (`crosscamp.py`).
- 2026-11-14 — CG5-1 approved by the owner ("ok continue" on the design doc); CG5-2 done: `engine/commonground/crosscamp.py` — `common_ground()` over >=2 camps: tier 1 stated (a reviewed statement is agreed when every camp's E+ entails it; union consistency check), tier 2 per selected-system combination (all ties reported, MAX_COMBINATIONS=64 then TooMany), pool = union of statements + validated candidates deduplicated by FOL text, derivation viewer via argmap.justifications (pending marked, never agreed without a positive verdict). 6 tests in test_crosscamp.py (shared claim, JSON round-trip, 3-camp unanimity, firm-rejection conflict, reconstructed tier with the unstated axiom + derivations, kernel-checked with LEAN_BIN). One real bug fixed in abduce.py: S4 minimality and the baseline's greedy drop now run over E+ (THEORY.md §2 conditions 2 and 4), not endorsed-only — a firm-rejection-only record previously could not certify any system. Full suite exit 0, 228 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG5-3 (fault lines + crosscamp CLI).
- 2026-11-14 — CG5-3 done: fault lines + `crosscamp` CLI in `engine/commonground/crosscamp.py` + `__main__.py` — `fault_lines()`: tier 1 MUSes/MCSes of the union of the camps' E+ (MCSes as complements of the MSSes), tier 2 per selected-system combination via argmap's MARCO enumeration; a union that is consistent reports root divergence instead: load-bearing axiom pairs (a1, a2) with A1 not-entails a2 and A2 not-entails a1, each witnessed by an explicit finite model, ranked by load1(a1)+load2(a2) (brief §4). `analyze()` = common_ground + fault_lines; `render_markdown()` writes crosscamp.md; CLI `python -m commonground crosscamp A.json B.json --candidates a.json b.json --lam 0.3 --lean --out DIR` writes <camp>/report.* plus crosscamp.{json,md}, TooMany exits 2 after writing the per-camp reports. Honest deviation from the design wording: argmap.enumerate_mus_mss (frozen v1) raises TooMany without partials, so a capped run aborts instead of reporting an uncertified partial MUS list. 5 new tests (11 total in test_crosscamp.py: stated MUS on a firm-rejection conflict, root divergence with models on a consistent union, analyze+render, combination cap, CLI end-to-end). Sample CLI line: `crosscamp recA.json recB.json --candidates candA.json candB.json --lam 0.3 --lean --out xout` → `{"camps": ["campA", "campB"], "stated_agreed": 4, "fault_lines_found": 0}`, exit 0. Full suite exit 0, 233 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG7-3 (pipeline reproduces the CO2 golden) or CG6-1 (web app).
- 2026-11-14 — CG7-3 done: `engine/tests/test_golden.py` (6 tests) runs the pipeline on examples/co2-2021 (test document = the camp's statements joined with located spans, so the verbatim-span discipline still holds): all golden FOLs parse; each camp's golden candidate set is a certified axiom system through check_system (CG7-2's hand-check, now pipeline-certified); computed load vectors pinned (yes: YAF=3, YA1=3, YA3=2, rest 1; no: NA1=5, NA2=2, NA3=2, rest 1); crosscamp.analyze on the two golden camps: stated claims jointly consistent, no shared stated claim, root divergence ranked (top rank 8). Divergences from golden.json's hand-worked expected_load_ranking are audited in the new AUDIT.md (AUDIT-1 DUP: YA1 duplicates stated yes-1; AUDIT-2 CONJ: NA1 conjunction accumulates load; AUDIT-3 SENS: at λ=0.3 the stated system is cheaper — abstention; AUDIT-4 SCOPE: full 16-item search did not finish in a 250 s probe, bounded by the check cap, never wrong). Engine fixes this task: report_camp drops candidates duplicating a stated claim (p=1 already), and check_system early-exits on the first non-holding check (certified semantics unchanged; +1 test in test_report.py). Full suite exit 0, 240 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG7-4 (CLI runs both bundled examples headless).
- 2026-11-14 — CG7-4 done: new `co2` subcommand in `__main__.py` runs the bundled CO2 golden corpus headless (builds records from statements.json + golden.json with located spans, per-camp report_camp + crosscamp.analyze, writes <camp>/report.{json,md} + crosscamp.{json,md}); `--max-checks` threads a cap through select/select_bruteforce/report_camp; the search is now seeded with the stated system A₀ (F1) so the cap still yields a certified selection (bnb and brute force deduplicate the seed; cross-check test green). Runs recorded live: `python -m commonground analyze examples/plastic_bags.json` exit 0; `python -m commonground co2 --max-checks 150 --timeout-ms 3000 --out co2-cli-out` exit 0 → `{"camps": ["yes", "no"], "stated_agreed": 0, "fault_lines_found": 0}`; both camps report the certified stated system (abstention at λ=0.3, AUDIT-3). README gained the v2 example commands; 1 new CLI test in test_golden.py. Full suite exit 0, 241 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG6-1 (web app API) or CG8-1 (FOLIO abduction benchmark).
- 2026-11-14 — README gained a "What you can do with it today" table (capability → command → concrete output) right before the evidence section, so a newcomer sees the five working flows (check / analyze / extract / camp / co2+crosscamp) in simple terms; notes that the paste-your-own-debate UI is Phase 6 and not built yet. Docs-only; engine suite unchanged (exit 0, 241 passed at c855fb4); e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG6-1 or CG8-1 (owner's choice).
- 2026-11-14 — Soundness review of the v2 certification layer, then fixes (owner in session: "find a solution and correct/improve everything that is either important to improve or easy"). The review was read-only; every finding was reproduced with a run. Five high-severity holes: (1) a search stopped by `max_checks` was published as cost-minimal, with "abstention" and a hull on [0, ∞] — the bundled `co2 --max-checks 150` run did this for both camps; (2) "no system was certified" (pending check, cap, unformalized statement) was published as "no axiom system exists … cannot all hold together"; (3) a camp with inconsistent stated claims gave vacuous tier-1 common ground, kernel-badged under `--lean`; (4) unformalized statements were dropped from the stated tier, which then read "jointly consistent: no stated conflict"; (5) the system headline read "SUFFICIENT (kernel-checked)" when a single entailment was. All five fixed in `abduce.py`, `crosscamp.py`, `load.py`, `__main__.py`, each with a regression test: `search_complete` / `hull_complete` / `abstention: null` and "SEARCH INCOMPLETE" in report.md, `search_incomplete` in crosscamp; `existence` (certified | none + reason | pending + reason); per-camp consistency gate and a stated tier of reviewed statements only; consistency and fault lines pending while statements are unformalized; `system_badge` (kernel only when every entailment is, "NOT CERTIFIED" otherwise). Also fixed: λ > 0 and plausibility in [0, 1] enforced (with a plausibility above 1 accepted, branch-and-bound returned a non-optimal system); plausibility keys matched in any spelling; a stated claim is never charged an estimate (AUDIT-5: the CO2 stated systems cost 3.0 / 2.7, were 3.15 / 2.8); the 0.5 default is reported; the hull lists only systems some λ > 0 selects (an inverted interval was reported, also on the CO2 `no` camp); the empty system is considered; duplicate formulas count once; ¬(A ⊕ B) and ¬(A ↔ B) are normalized; load reports undecided removals as `pending`; root-divergence pairs without verdict are listed as pending; checks export their evidence (finite model; Lean source + SHA-256); negative controls call the check they name, require a certified system, add a fresh-symbol claim and, with Lean, a theorem accepted in the same run; record/candidate JSON validated with a reason (CLI exit 2, no traceback); a camp name cannot leave `--out`, duplicate camp names refused; `--lean` without Lean is an error; `camp`/`crosscamp` gained `--max-checks`; the candidate prompt shows the real grammar; a name no quantifier binds is listed as a warning; a solver refutation outside the Bernays–Schönfinkel class says so in its detail. Recorded run: CO2 camp `no` searched exhaustively (2,048 checks, complete): abstention at λ=0.3 established, stated system cost-minimal for λ ≤ 0.4 (AUDIT-3); camp `yes` not established. Left for the owner (BACKLOG): the Bernays–Schönfinkel boundary (the designs say "no verdict" outside the class; the engine accepts a Z3 refutation there and now labels it — gate, or amend the designs), the gameable size normal form, `lean.py`'s error regex on Windows paths, a complete hull beyond 12 pool items. v1 modules, `docs/research/` and `docs/design/` untouched. 94 new test cases. Full engine suite with FOLIO_DIR+LEAN_BIN: exit 0, 335 passed (was 241; 520 s). e2e not re-run (no app/api/build change since cc563a3). README (CO2 paragraph), AUDIT.md, CHANGELOG.md, BACKLOG.md updated. Committed as this session's commit. Escalations: none while fixing; one owner decision recorded (the boundary). Next: CG6-1 — the API must read `search_complete`, `existence`, `badge` and the per-check outcomes, never `abstention` or a headline alone — or CG8-1.
- 2026-11-14 — PLAN.md review after the soundness review (7b60efd), docs-only commit: CG6-1 split into CG6-1a (engine bridge api/engineRunner.ts + camp router + registration + contracts; must surface search_complete/existence/badge/certified/per-check outcomes, never abstention or a headline alone) and CG6-1b (crosscamp + extract routers); CG6-2..6-4 wording aligned with the new report fields (pending display, plausibility provenance, search_incomplete, pairwise >2 camps); CG6-5 count corrected to 33+33+8; CG8-1 reworded (recovery = certified sufficient subset of the premises, Wilson interval, sizes; files bench.py/__main__.py/test_folio.py); CG8-2 wording; CG8-4 moved after CG8-1/CG8-2 with deps fixed and scoped to the missing plausibility-range recomputation; CG8-3 last, CI guard 'or not run locally'; stale 'Decisions waiting' paragraph replaced by the current eight owner decisions. Engine suite unchanged (exit 0, 335 passed at 7b60efd, recorded; not re-run for this docs commit). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG8-1 implementation.
- 2026-11-14 — CG8-1 done: `bench.abduction()` + `folio --mode abduction` (CG8-1) — per FOLIO example the conclusion is the only endorsed claim and the pool is the example's own premises as unscored candidates; recovery graded cost-independently (a certified sufficient premise-subset exists, from all_certified; search_complete required for a definite negative), Wilson interval, min recovered size vs reference premise count, badges; parse errors and pool-cap rows counted, never crashed; config.json/runs.jsonl/summary.json written, resumable. 4 new tests in test_folio.py (recover, definite negative, parse-error + pool-cap, CLI end-to-end). Recorded run (slice --limit 25, solver-only, exit 0): 25/25 parsed, recovered 9/25 = 36.0% (Wilson 20.3–55.5), min recovered size mean 3.44 vs reference premises mean 5.6, all SOLVER-CHECKED. Full 204-example run: not run this session (feeds CG8-3); live LLM-candidate mode: not run (needs the owner's endpoint). Full suite exit 0, 339 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG8-2 (CO2 holdout) or CG6-1a.
- 2026-11-14 — CG8-2 done: leave-one-out holdout on the CO2 golden camps in test_golden.py (`holdout()`/`holdout_summary()`, RESEARCH.md §14.2): each reviewed statement is withheld in turn; the system is rebuilt from the remaining stated claims plus the candidates whose evidence is not solely the withheld statement; 'derived' is a certified entailment check carrying its badge (a non-derivation is a definite non-entailment with its finite model). Recorded in results/co2-holdout/summary.json: yes 2/7 re-derived (28.6%, Wilson 8.2–64.1), no 2/6 (33.3%, Wilson 9.7–70.0). The search-based selection is not part of the holdout (AUDIT-4: the 16-item yes-pool search does not finish under the cap) — the golden candidate extraction (CG7-2) is used, and the note in summary.json says so. 2 new tests. Full suite exit 0, 341 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG8-4 (plausibility-range sensitivity) or CG6-1a (web API).
- 2026-11-14 — CG8-4 done: plausibility ranges in `abduce.py` — a plausibility value may now be a number (point estimate) or a [min, max] range (RESEARCH.md §15.3 k samples); keys still canonicalized in any spelling, non-formula keys and out-of-range or inverted ranges are errors. The main selection runs at each range's midpoint; when any range is non-degenerate, report_camp recomputes the selection at all-min and all-max and reports `plausibility_sensitivity` (ranges, systems at each extreme with their own search_complete, `stable` true/false/null-pending); report.md gains a 'Plausibility sensitivity' section; --plausibilities accepts ranges. 4 new tests in test_report.py (range that flips the selection at λ=0.3 threshold p>0.7, stable range, point estimates give no section, invalid ranges are ValueErrors). Full suite exit 0, 345 passed (FOLIO_DIR+LEAN_BIN). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG8-3 (publish Phase 8 numbers in README) or CG6-1a (web API).
- 2026-11-14 — CG8-3 done: README publishes the Phase 8 numbers with reproduce commands — the FOLIO abduction slice (now committed at results/abduction-25/: 9/25 recovered = 36.0%, Wilson 20.3–55.5, recovered subsets 3.44 premises on average vs 5.6 given; solver-only run so every row is SOLVER-CHECKED; reproduce `FOLIO_DIR=… python -m commonground --timeout-ms 3000 folio --mode abduction --limit 25 --out results/abduction-25`) and the CO2 leave-one-out holdout (results/co2-holdout/summary.json from CG8-2; yes 2/7 = 28.6% Wilson 8.2–64.1, no 2/6 = 33.3% Wilson 9.7–70.0; reproduce `cd engine && python -m pytest tests/test_golden.py -k holdout`) — plus two "What has not been shown" bullets: the full 204-example abduction run and the live-LLM candidate mode were not run (endpoint needed), and the holdout skips the selection search per AUDIT-4 with intervals too wide to separate the camps. The camp row in "What you can do" now mentions the plausibility-sensitivity section (CG8-4). Docs+results only: engine suite unchanged (exit 0, 345 passed at 73e55b3, recorded; that run includes the CI number-guard test test_published_results_are_reproduced — green locally, the CI job itself runs on the next push, not run here). e2e unchanged since cc563a3. Committed as this session's commit. Escalations: none. Next: CG6-1a (web API engine bridge + camp router).
- 2026-11-14 — CG6-1a done: `api/engineRunner.ts` spawns `python -X utf8 -m commonground camp` in a temp dir (ENGINE_DIR or ./engine; ENGINE_PYTHON/PYTHON_BIN, default python/python3; ENGINE_TIMEOUT_MS default 120 s clamped 5–600 s; engineGate one run at a time; child env is a whitelist — PATH/HOME/APPDATA/LEAN_BIN etc., never the server's secrets) and parses out/report.json through the contracts whitelist `contracts/engineReport.ts` (camp, lam, search_complete, hull_complete, existence, selection, systems with badge/certified and per-check kind/claim/outcome/badge/detail — `abstention` and every unlisted key are stripped on parse, asserted by `contracts/engineReport.test.ts`). `parseEngineJson` reads Python's bare Infinity/NaN (unbounded λ-interval ends) as null outside strings — that was the one real interop bug found while bridging. Timeout / missing runtime / unreadable report / contract mismatch answer `no_verdict` (never scored as wrong); engine exit 2 answers `invalid_input` (BAD_REQUEST); `--lean` without a Lean binary is a no_verdict, not a silent fall-back. New `api/campRouter.ts` exposes `camp.run` (reviewerMutation, zod-validated record/candidates/plausibilities/lam/maxChecks/timeoutMs/lean, camp name mirroring the engine's directory-name rule), registered as `camp` in `api/router.ts`; `leanExecutable` is now exported from `api/proofVerifier.ts` for reuse. Verified against the real engine with a throwaway vitest file (report parsed with abstention stripped; bad span → invalid_input; bogus python → no_verdict), then deleted. `npm test` 46 passed + 4 skipped (win32 shebang skips), `npm run lint` and `npm run check` exit 0. e2e re-run for real (production build, MySQL 8.0.44, Chromium): no-Lean server 33 passed, Lean server 33 passed, read-only server 8 passed, all exit 0 — no existing route changed. Engine suite unchanged (exit 0, 345 passed at 73e55b3, recorded; engine untouched this task). Committed as this session's commit. Escalations: none. Next: CG6-1b (crosscamp + extract routers).
- 2026-11-14 — CG6-1b done: `crosscamp` and `extract` routers on the same bridge, registered in api/router.ts. `runCrosscamp` writes one record/candidates pair per camp to a temp dir, spawns `commonground crosscamp` (its own --timeout-ms after the subcommand, since the subparser shadows the global one) and parses out/crosscamp.json through the new whitelist contracts/crosscampReport.ts (camps, search_incomplete, both common-ground tiers, fault lines with mus/mcs and root_divergence + root_divergence_pending — pending pairs are surfaced, never dropped) plus each out/<camp>/report.json through the camp whitelist, so no abstention reaches the API from either file. `runExtract` writes the documents into a temp dir, runs `commonground extract` with PYTHONPATH at the engine and the server's LLM_API_KEY passed to the child only (never accepted from the client); engine exit 3 (provider outage stopped the run) and timeouts answer no_verdict, exit 2 is invalid_input; output validated by contracts/extractRun.ts (per-document statements with verbatim spans, relations, error rows). extract.run spends the site AI budget behind aiGate/aiBudget + reviewerMutation; crosscamp.run behind engineGate + reviewerMutation; input schemas reused from campRouter (record/candidates/plausibility), records 2–8 with matching candidates. New contracts test contracts/crosscampReport.test.ts (whitelist strips abstention keys, pending stated tier with null mus/mcs, missing search_incomplete rejected, extract rows incl. error rows). Verified against the real engine with a throwaway vitest file (CO2 crosscamp with maxChecks 150: report + both per-camp reports, search_incomplete [yes, no], no abstention; extract against the local stub LLM: spans returned; no LLM_API_KEY → no_verdict), then deleted. `npm test` 53 passed + 4 skipped, lint/tsc exit 0. e2e re-run for real (production build, MySQL 8.0.44, Chromium): 33 + 33 (Lean) + 8 (read-only) passed, all exit 0. Engine suite unchanged (exit 0, 345 passed at 73e55b3, recorded; engine untouched). Committed as this session's commit. Escalations: none. Next: CG6-2 (statement/camp input UI).
