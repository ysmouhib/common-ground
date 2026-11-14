# Contributing

Common Ground certifies deductions, not truth. Contributions keep that boundary:
nothing a language model writes is ever passed to Lean without human approval,
and no published number may be unreproducible.

## Dev setup

- Python 3.13 for `engine/` (`pip install -r engine/requirements.txt`); the
  engine also runs on 3.10+.
- Node.js (LTS) for the app: `npm ci`.
- Optional but used by CI: Lean 4.35.0 (`LEAN_BIN`), a FOLIO clone
  (`FOLIO_DIR`), MySQL 8.0 (`DATABASE_URL`) and a Playwright browser for e2e.

## Test commands

```bash
# engine (full suite; the two FOLIO tests and three Lean tests skip without
# FOLIO_DIR / LEAN_BIN and run when they are set)
cd engine && python -m pytest

# app: unit tests, types, lint
npm test && npm run check && npm run lint

# end to end: build, start a server with a database and a reviewer token, then
npm run build
NODE_ENV=production DATABASE_URL=mysql://… REVIEWER_TOKEN=… node dist/boot.js &
npm run e2e            # 33 checks; E2E_READ_ONLY=1 against a tokenless server: 8 more
```

CI (`.github/workflows/ci.yml`) runs all of this on every pull request and
push to `main`, including the e2e checks against the container image.

## Pull request checklist

- [ ] `python -m pytest` in `engine/` exits 0; `npm test`, `npm run check`,
      `npm run lint` pass; e2e passes if you touched the app.
- [ ] If a number shown in the README changed, the change comes from an actual
      run whose command is in the README next to the number, and the recorded
      results under `results/` are updated in the same PR. CI fails otherwise.
- [ ] "What has not been shown" in the README is updated if your change touches
      a claim. Write "not run" when a command cannot run; never invent a number
      or a citation.
- [ ] New LLM-facing surface: schema validation, timeouts, provider outage is
      never scored as a wrong answer, and no model output reaches Lean.
- [ ] The plastic-bag debate still analyzes identically (`contracts/` tests).
- [ ] No new dependency without a paragraph in the PR description arguing for it
      in `docs/PLAN.md` first.
- [ ] Conventional commit messages: `type(scope): description`
      (e.g. `feat(engine): …`, `docs(plan): …`, `test(engine): …`).

## Where work is planned

`docs/PLAN.md` is the task queue of record; `AGENTS.md` is the operating rules
(escalation, Definition of Done, scope fences). Pick a task from the queue,
keep to it, and record out-of-scope problems in `docs/BACKLOG.md` instead of
fixing them in the same PR.
