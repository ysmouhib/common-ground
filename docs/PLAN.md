# Plan and state for Common Ground v2

This file carries the state between sessions (CLAUDE.md, "Session economy"). The
phases are defined in [`v2-build-brief.md`](v2-build-brief.md) §8 and are not repeated
here.

## State on 13 November 2026

| Phase | Status |
|---|---|
| 0 Baseline | **Not recorded.** This file did not exist when Phase R opened. No test suite was run in the Phase R session, so nothing here confirms that the README numbers reproduce, and the PR-sized mapping of phases 1 to 9 that Phase 0 asks for is not written. |
| R Scientific grounding | **In progress: session 1 of 4 done.** |
| 1 to 9 | Not started. No abduction code before the owner has reviewed `THEORY.md` (brief §8). |

Nothing is committed. `CLAUDE.md` and `docs/` are untracked in git.

## Phase R

### Rules set by the owner (13 November 2026)

1. Act as senior researcher, not as coder. No Phase 1 code in a Phase R session.
2. Verify every pack entry before citing it. Never invent a citation. What cannot be
   verified is tagged `[unverified]` and stays out of `THEORY.md`.
3. Answer RQ1 to RQ6 in writing, each grounded only in sources read or verified in the
   session that writes the answer.
4. Critique the pack: mark what is wrong, weak or superseded, and add what is missing
   (pack §I), above all the 2025–2026 search for any system that combines enthymeme
   reconstruction with formal verification over whole corpora.
5. Produce `THEORY.md`: definitions, H1 to H9 with citations, limits, open problems.
6. One phase per session; update this file as you go.

### Files

| File | Role | State |
|---|---|---|
| `docs/research/sources.md` | The owner's source pack. Corrected in place when an entry is verified; log in its §K. | B1, B2, B5, C2 verified |
| `docs/research/RESEARCH.md` | Verified annotated bibliography, answers to the research questions, critique of the pack, proposed amendments. | RQ1, RQ3 drafted |
| `docs/research/THEORY.md` | The theory document that code and interface will cite. | Draft: definitions, F1–F5, H2–H4 |

### Sessions (pack §J)

- [x] **Session 1, formal core.** Lin 2001, Hobbs et al. 1993 and Liffiton & Sakallah
  2008 read and verified; RQ1 and RQ3 drafted; 19 supporting sources checked and one
  left `[unverified]`; seven amendments to brief §4 proposed.
- [ ] **Session 2, reconstruction precedent.** In this order:
  1. The novelty search (pack §I.3): ArgMining, COMMA, ACL, EMNLP, AAAI, 2025–2026.
  2. A3 (Sviridova et al.), then A4, then A1 skim. Answer RQ2.
  3. Decide the terminology: axiom, warrant or implicit premise (brief §3, question 1).
  4. Verify every `[classic, verify]` entry in Themes A, B and C: A1, A2, B3, B4, C1
     (with Schlobach & Cornet and Peñaloza), C3.
  5. Carried from session 1: read Ng & Mooney 1990 and Charniak & Shimony 1994
     themselves; settle the page range of Doherty et al. 2001; verify Reiter & de Kleer
     1987.
- [ ] **Session 3, psychology.** D1, E1, E3, E5. Answer RQ4 and RQ5. Draft H6 and H8.
  Also: the coverage measure for records that admit no axiom system (starting point:
  `RESEARCH.md` §2.4, existence); whether load is a defensible reading of Converse's
  centrality (brief §3, question 3); whether a model's plausibility estimate can be
  treated as a probability, and the elicitation protocol (pack §I.5).
- [ ] **Session 4, evaluation.** A6, D2, D3, G3. Answer RQ6. Define the Phase 7
  annotation protocol. Finish `THEORY.md` within two pages. List every remaining
  `[unverified]`. Then: ESCALATE for the final review of `THEORY.md` (CLAUDE.md,
  escalation item 6).

### The brief's six questions and where they are answered

| Brief §3 question | Answered in |
|---|---|
| 1. Terminology decision | Session 2 |
| 2. Is weighted parsimony the accepted formalization? | `RESEARCH.md` §3 (draft): an accepted form, among four; the values are not grounded |
| 3. Is load a defensible operationalization of centrality? | Session 3 |
| 4. Closest prior art and our differentiation | Session 2 |
| 5. Failure modes of model-based implicit-premise extraction | Sessions 2 to 4 |
| 6. Evaluation designs of comparable systems | Session 4 |

### Decisions waiting for the owner

**Owner's instruction, 13 November 2026 (after Session 1):** "start next phase
(following the upgrade decisions mentioned here)". Read as: continue with Session 2 and
proceed on the proposed amendments A1 to A7. They are adopted for drafting and remain
subject to the owner's review of the finished `THEORY.md`. Items 1 and 3 below were not
answered explicitly and keep their defaults: files stay under `docs/research/`, and
Phase 0 stays unrecorded.

1. **Location of the two documents.** The brief and CLAUDE.md say `docs/RESEARCH.md`
   and `docs/THEORY.md`; the Phase R instruction said `docs/research/THEORY.md`. Both
   files are under `docs/research/` for now. Moving them is one `git mv` each.
2. **Amendments A1 to A7 to brief §4** (`RESEARCH.md` §5). The ones that change what
   Phase 3 builds: A1 (minimality means no sufficient proper subset), A3 (size counted
   on a normal form, because a single conjunction of all claims otherwise wins), A4 (a
   floor or a logarithmic charge on plausibility, because five claims replaced buys any
   axiom at λ = 0.3), A5 (report the hull and λ-intervals instead of one λ).
3. **Phase 0.** Whether to run and record the baseline before Phase R continues. The
   research does not depend on it; Phase 1 does.

### Pack entries that look wrong at a glance

Noticed while reading, **not checked**. They say where to look first; do not copy them
as corrections.

- B3: the second author's initial.
- B4: the volume and the year do not seem to belong together.
- F2: the journal and pages may belong to a different paper by the same author.
- G1 and G2: the pack itself asks for the venue and the canonical citation.

### How verification was done on this machine

- Crossref's REST API answers plain `curl` requests with a generic user agent and gives
  volume, issue and pages. DBLP, ScienceDirect and DTIC refuse automated requests.
- For older *Artificial Intelligence* papers the authors' pages often hold a PostScript
  preprint. There is no Ghostscript here; dvips output can be turned into readable text
  by a short script that tracks the font of each string.
- `pdftotext` is on the path and works for PDFs with ordinary fonts. PDF pages cannot
  be rendered as images here.

## To resume

Read `CLAUDE.md`, this file, and `RESEARCH.md` §5 and §6. Then start Session 2, item 1.
