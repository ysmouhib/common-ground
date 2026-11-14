## What this PR does

<!-- One paragraph: what changes, and which task in docs/PLAN.md it is. -->

## Checks

- [ ] `cd engine && python -m pytest` exits 0
- [ ] `npm test && npm run check && npm run lint` pass
- [ ] `npm run e2e` passes if the app or API changed
- [ ] README numbers changed only via actual runs, with the reproduce command
      next to the number and `results/` updated in this PR
- [ ] "What has not been shown" updated if a claim changed
- [ ] No LLM output reaches Lean without human approval; provider outage is
      never scored as a wrong answer
- [ ] Out-of-scope problems noticed are in `docs/BACKLOG.md`, not fixed here

## Notes

<!-- Anything a reviewer should know: assumptions, trade-offs, open questions. -->
