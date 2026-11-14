# Operating rules for this repo



## Model strategy (owner is on a limited plan)

  implementation (Phase 3), (2) the cross-camp reduced-disagreement algorithm
  (Phase 5), (3) Lean certificate edge cases and failing negative controls,
  (4) fol.py grammar edge cases, (5) any bug after two failed fix attempts,
  (6) final review of docs/THEORY.md before Phase 3 begins.
- Never switch models on your own. When a task hits the escalation list,
  stop and say: "ESCALATE: <reason>". The owner switches with /model.

## Research rules (Phase R)
- docs/RESEARCH.md and docs/THEORY.md come before abduction code.
- Every citation must be verified (title, authors, venue, year). If you
  cannot verify a source, mark it "unverified" or drop it. Never invent
  a citation. If you have no web access, ask the owner for abstracts.

## Session economy
- One phase per session. Work only inside the current phase in docs/PLAN.md.
- Never rewrite whole files when a targeted edit works.
- Never re-read the full repo; CLAUDE.md, PLAN.md and the brief carry the state.
- Never fabricate benchmark numbers. Write "not run" when a command cannot run.
- Update docs/PLAN.md at the end of every session so the next session resumes.

## Product bar
- Any fresh clone must reach a first analysis in under 10 minutes (Phase 9
  acceptance). Degradation is honest: SOLVER-CHECKED vs kernel-certified,
  outage shown as outage.
- No telemetry, analytics, or tracking. Local-first privacy: document
  exactly what leaves the machine (only calls to the configured LLM endpoint).
Canonical instructions live in AGENTS.md.
