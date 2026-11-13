# Operating rules for this repo

This file is the canonical instruction file for any agent working in this
repo. `CLAUDE.md` points here. It ports the rules that previously lived only
in `CLAUDE.md` and makes them model-agnostic.

## Who works here: escalation, not model switching

- You are the default worker. Run every task on the model you are on; never
  ask to switch models.
- Stop and escalate when a task is a hard design decision — the `abduce.py`
  design, the cross-camp common-ground algorithm, Lean 4 or grammar edge
  cases — or when a bug survives two fix attempts.
- To escalate: write `ESCALATE: <reason>` in your reply, commit the green
  state (tests passing, work committed), and wait. The owner decides what
  happens next.

## Definition of Done

A task is complete ONLY when all of these pass:

1. `pytest` exits 0 on the full suite.
2. The e2e checks pass.
3. Changes are committed with a conventional message
   (`type(scope): description`).
4. README evidence tables are updated if any shown number changed.

Never self-assess completion; the tests decide.

## Scope fences

- Do only the current task. No refactors, no new dependencies, no file
  rewrites outside task scope, even for problems you notice: record them in
  `docs/BACKLOG.md` instead.
- If a decision is not covered by `AGENTS.md` or `docs/PLAN.md`, ask the
  owner; do not improvise.

## Task protocol

- One phase per session. Start every session by reading `AGENTS.md` and the
  current task in `docs/PLAN.md`.
- If a task touches more than 2 files or needs more than 1 unclear decision,
  split it before starting.
- Never rewrite whole files when a targeted edit works.
- Never re-read the full repo; `AGENTS.md`, `docs/PLAN.md` and the build
  brief carry the state.
- Update `docs/PLAN.md` at the end of every session so the next session
  resumes.

## Evidence discipline

- Never fabricate citations, numbers, or results. README numbers come from
  actual runs only. Write "not run" when a command cannot run.
- Research is off-limits to you: do not verify `[classic, verify]` citations,
  do not edit `docs/research/sources.md`, do not write `THEORY.md`. The owner
  handles research with another tool.
- Phase-order constraint: the owner-reviewed `docs/research/THEORY.md` comes
  before any abduction code. You neither write nor verify research content.

## Product bar

- Any fresh clone must reach a first analysis in under 10 minutes (Phase 9
  acceptance). Degradation is honest: SOLVER-CHECKED vs kernel-certified,
  outage shown as outage.
- No telemetry, analytics, or tracking. Local-first privacy: document
  exactly what leaves the machine (only calls to the configured LLM
  endpoint).
