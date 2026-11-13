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
| 1 to 9 | Not started. No abduction code before the owner has reviewed `THEORY.md` (brief §8; gate CGR-5). |

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
- [ ] **CGR-2** — Session 2, reconstruction precedent (owner): novelty search
  2025–2026 (ArgMining, COMMA, ACL, EMNLP, AAAI); A3, A4, A1; answer RQ2;
  terminology decision; verify `[classic, verify]` entries in Themes A, B, C
  (A1, A2, B3, B4, C1 incl. Schlobach & Cornet and Peñaloza, C3); carried
  items: Ng & Mooney 1990, Charniak & Shimony 1994, Doherty et al. 2001 page
  range, Reiter & de Kleer 1987. Files: `docs/research/RESEARCH.md`. Deps: none.
  Done-when: owner records the session in this file.
- [ ] **CGR-3** — Session 3, psychology (owner): D1, E1, E3, E5; RQ4, RQ5;
  draft H6, H8; coverage measure; load vs. centrality; plausibility elicitation
  protocol. Files: `docs/research/RESEARCH.md`, `docs/research/THEORY.md`.
  Deps: CGR-2. Done-when: owner records the session.
- [ ] **CGR-4** — Session 4, evaluation (owner): A6, D2, D3, G3; RQ6; Phase 7
  annotation protocol; finish `THEORY.md` within two pages; list every
  remaining `[unverified]`. Deps: CGR-3. Done-when: owner records the session.
- [ ] **CGR-5** — Owner review of the finished `THEORY.md`. Gates CG3-1.
  Deps: CGR-4. Done-when: owner approval recorded here.

### Phase 1 — The formalizer goes live

- [ ] **CG1-1** — Run `folio --mode direct` and `--mode llm` against the
  configured endpoint; publish both README rows with 95% Wilson intervals and
  the exact McNemar test via `python -m commonground report`.
  Files: `README.md`, `results/direct/`, `results/llm/`. Deps: LLM endpoint
  credentials supplied by the owner. Done-when: README rows filled from actual
  runs (or "not run" recorded); pytest exits 0.
- [ ] **CG1-2** — Confirm `.github/workflows/model-benchmark.yml` matches the
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
- [ ] **CG2-3** — CLI wiring (`python -m commonground extract …`) and README
  evidence row. Files: `engine/commonground/__main__.py`, `README.md`.
  Deps: CG2-2. Done-when: pytest exits 0; README row with reproduce command or
  "not run".

### Phase 3 — The abduction engine (blocked on CGR-5; [PLAN] on the design)

- [ ] **CG3-1 [PLAN]** — Design doc first: candidate generation, sufficiency /
  consistency / negation checking, cost function, cost-minimal search,
  certificates, negative controls; soundness and termination notes; cites
  `THEORY.md`. Files: `docs/design/abduction.md`. Deps: CGR-5.
  Done-when: step-by-step plan produced in-session; owner approves before code.
- [ ] **CG3-2** — LLM-independent candidate-generation interface in
  `abduce.py` (scripted clients for tests). Files:
  `engine/commonground/abduce.py`, `engine/tests/test_abduce.py`. Deps: CG3-1.
  Done-when: pytest exits 0.
- [ ] **CG3-3 [PLAN: Lean integration edge cases]** — Sufficiency / consistency
  / negation checking via the existing solvers (`smt.py`, `ground.py`,
  `model.py`) plus Lean certificates for sufficiency proofs. Files:
  `engine/commonground/abduce.py`, `engine/tests/test_abduce.py`. Deps: CG3-2.
  Done-when: pytest exits 0; lean-marked tests pass with `LEAN_BIN` or skip
  with the reason recorded.
- [ ] **CG3-4** — Cost-minimal search over certified subsets
  (branch-and-bound), cross-checked against brute force in tests, mirroring how
  `argmap.py` is tested. Files: `engine/commonground/abduce.py`,
  `engine/tests/test_abduce.py`. Deps: CG3-3. Done-when: pytest exits 0.
- [ ] **CG3-5** — Negative controls: for a certified axiom set, Lean must
  reject the negations; adversarial self-checks (a claim not entailed, a
  smuggled contradiction, a redundant axiom, a violated rejection). Files:
  `engine/tests/test_abduce.py`, `engine/commonground/abduce.py`. Deps: CG3-4.
  Done-when: pytest exits 0.

### Phase 4 — Load analysis and per-camp reports

- [ ] **CG4-1** — Load metric: which axioms are load-bearing, computed from
  `argmap.py` minimal premise sets over each camp's certified system. Files:
  `engine/commonground/load.py`, `engine/tests/test_load.py`. Deps: CG3-5.
  Done-when: pytest exits 0.
- [ ] **CG4-2** — Per-camp report (CLI): statements → axioms → load ranking →
  certificate statuses, human-readable and JSON. Files:
  `engine/commonground/__main__.py`, one engine test file. Deps: CG4-1.
  Done-when: pytest exits 0; sample output recorded in the session log.

### Phase 5 — Cross-camp analysis: common ground, reduced disagreement ([PLAN] on the algorithm)

- [ ] **CG5-1 [PLAN]** — Design doc: common ground (claims entailed by both
  camps' systems) and reduced disagreement as MUS/MCS over the union of the
  camps' axiom systems (sources pack C1–C3); fault-line output format. Files:
  `docs/design/cross-camp.md`. Deps: CG4-2, CGR-5. Done-when: owner-approved
  plan before code.
- [ ] **CG5-2** — Common-ground computation with solver checks. Files:
  `engine/commonground/crosscamp.py`, `engine/tests/test_crosscamp.py`.
  Deps: CG5-1. Done-when: pytest exits 0.
- [ ] **CG5-3** — Reduced disagreement (minimal differing axiom subsets via
  MARCO in `argmap.py`) + CLI report. Files: `engine/commonground/crosscamp.py`,
  `engine/tests/test_crosscamp.py`. Deps: CG5-2. Done-when: pytest exits 0.

### Phase 6 — Web app

- [ ] **CG6-1** — API routers (tRPC) for extract / abduce / cross-camp with
  the existing access control: public reads, reviewer token for mutations,
  schema validation, timeouts, provider outage never scored as a wrong answer.
  Files: one `api/` router file, one contracts test. Deps: CG3-5, CG5-3.
  Done-when: `npm test` and e2e pass.
- [ ] **CG6-2** — Statement and camp input UI (paste texts, assign camps).
  Files: two `src/` files. Deps: CG6-1. Done-when: `npm test` and e2e pass.
- [ ] **CG6-3** — Axiom review queue UI (proposed axioms with evidence quotes,
  approve/reject; no LLM output reaches Lean without human approval). Files:
  two `src/` files. Deps: CG6-2. Done-when: `npm test` and e2e pass.
- [ ] **CG6-4** — Camp comparison view: provable common ground and exact fault
  lines. Files: two `src/` files. Deps: CG6-3. Done-when: `npm test` and e2e
  pass.
- [ ] **CG6-5** — Extend the e2e suite (currently 33 + 8 checks) for the new
  flow; update README check counts. Files: `e2e/run.mjs`, `README.md`.
  Deps: CG6-4. Done-when: e2e passes; README updated.

### Phase 7 — Golden dataset (Swiss CO2-law votation, 13 June 2021, vote 644)

- [ ] **CG7-1** — Corpus skeleton: source list, camp definitions, first
  hand-worked statement lists. Files: `examples/co2-2021/README.md`,
  `examples/co2-2021/statements.json`. Deps: campaign materials from
  swissvotes.ch (owner supplies if web access is unavailable). Done-when:
  committed; pytest exits 0.
- [ ] **CG7-2** — Hand-worked golden reconstruction: formalizations, candidate
  axioms, expected load ranking. Files: `examples/co2-2021/golden.json`,
  `examples/co2-2021/README.md`. Deps: CG7-1. Done-when: committed and
  reviewable.
- [ ] **CG7-3** — Pipeline reproduces the golden reconstruction; every
  divergence becomes an `AUDIT.md` error-taxonomy entry. Files:
  `engine/tests/test_golden.py`, `AUDIT.md`. Deps: CG7-2, CG3-5.
  Done-when: pytest exits 0.
- [ ] **CG7-4** — CLI runs both bundled examples (plastic-bag regression +
  CO2) headless, end to end. Files: `engine/commonground/__main__.py`,
  `README.md`. Deps: CG7-3, CG5-3. Done-when: runs recorded; pytest exits 0.

### Phase 8 — Evaluation

- [ ] **CG8-1** — Abduction benchmark on FOLIO: hide premises, check whether
  the system recovers *sufficient* premises; reuse the Wilson-interval /
  McNemar harness. Files: `engine/commonground/folio.py`,
  `engine/tests/test_folio.py`. Deps: CG3-5. Done-when: pytest exits 0;
  numbers recorded or "not run".
- [ ] **CG8-2** — CO2 holdout test: remove published statements of a camp,
  extract axioms from the rest, check the extracted system still derives the
  withheld statements. Files: `engine/tests/test_golden.py`, `results/`.
  Deps: CG7-3. Done-when: pytest exits 0; README row added.
- [ ] **CG8-3** — Publish all evaluation numbers README-style with reproduce
  commands; update "What has not been shown". Files: `README.md`. Deps:
  CG8-1, CG8-2. Done-when: README updated; CI number guard green.

### Phase 9 — Release readiness

- [ ] **CG9-1** — MIT `LICENSE`. Files: `LICENSE`. Done-when: committed.
- [ ] **CG9-2** — `CONTRIBUTING.md` (dev setup, test commands, PR checklist,
  reproducible-numbers rule). Files: `CONTRIBUTING.md`. Done-when: committed.
- [ ] **CG9-3** — `CODE_OF_CONDUCT.md` (Contributor Covenant) + PR template.
  Files: `CODE_OF_CONDUCT.md`, `.github/PULL_REQUEST_TEMPLATE.md`.
  Done-when: committed.
- [ ] **CG9-4** — Issue templates: bug report + feature request. Files:
  `.github/ISSUE_TEMPLATE/bug.md`, `.github/ISSUE_TEMPLATE/feature.md`.
  Done-when: committed.
- [ ] **CG9-5** — Issue template: research question. Files:
  `.github/ISSUE_TEMPLATE/research.md`. Done-when: committed.
- [ ] **CG9-6** — `CHANGELOG.md` (Keep a Changelog) and tag `v2.0.0`. Files:
  `CHANGELOG.md`. Done-when: committed; tag created (push only with owner
  approval).
- [ ] **CG9-7** — README release pass: badges (CI, MIT, Python/Node versions),
  quickstart, demo media, links to `THEORY.md` / `RESEARCH.md`. Files:
  `README.md`. Deps: CG9-1..CG9-6. Done-when: quickstart verified on a clean
  clone or "not run" recorded; every badge and claim true.
- [ ] **CG9-8** — Engine packaging for PyPI; name decision recorded here.
  Files: `engine/pyproject.toml`, `docs/PLAN.md`. Done-when: build works or
  "not run" recorded.
- [ ] **CG9-9** — CI publishes the container to GHCR. Files:
  `.github/workflows/ci.yml` (or a new release workflow). Done-when: workflow
  validated; green or "not run" locally.
- [ ] **CG9-10** — `SECURITY.md` refresh + `examples/` index. Files:
  `SECURITY.md`, `examples/README.md`. Done-when: committed.
- [ ] **CG9-11** — Final acceptance: a person outside the project clones on a
  clean machine and completes an analysis in under 10 minutes following only
  the README. Files: `docs/PLAN.md` (record). Deps: all above. Done-when:
  outcome recorded.

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

Decisions waiting for the owner: (1) location of RESEARCH.md/THEORY.md (both
under `docs/research/` for now; moving is one `git mv` each); (2) amendments
A1–A7 to brief §4 — A1 minimality = no sufficient proper subset, A3 size
counted on a normal form, A4 floor/logarithmic charge on plausibility, A5
report the hull and λ-intervals; (3) Phase 0 — whether to run and record the
baseline before Phase R continues (partly answered by CG0-1's recorded run).

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
