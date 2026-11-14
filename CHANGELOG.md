# Changelog

All notable changes to this project are documented here, in Keep a Changelog
format. Versions follow Semantic Versioning.

## [Unreleased]

### Added (v2 build-out, phases 0-2 and 7 so far)

- `engine/commonground/extract.py`: statement extraction from text with
  verbatim quotes located by the engine in the source text (a quote that is not there is
  rejected; every statement carries its span), support/
  runs with `config.json`/`runs.jsonl` provenance; `python -m commonground
  extract <files> --out DIR`.; since 2026-11-14 the prompt asks only for
  verbatim quotes (the engine locates them; default reply limit 8000) — re-run live:
  2 of 2 short CO2 documents at 2000 and at 8000, one attempt each.
- Live language-model benchmark on FOLIO validation (deepseek-flash,
  2026-11-13, results in `results/direct` and `results/llm`): direct answering
  162/204 (79.4 %), formalize-then-solve 119/204 (58.3 %, 81.5 % when a
  formalization parses); Wilson intervals and exact McNemar in the README.
- Live deepseek-flash runs at a 4000-token reply limit (2026-11-14,
  `results/llm-4000/` and `results/direct-4000/`): direct answering 163/204
  (79.9 %, 82.3 % when it answers, 6 Invalid); paired at the same limit with
  the formalizing mode, exact McNemar p = 0.0039.
- Golden corpus skeleton `examples/co2-2021/` (Swiss CO2-law votation, vote
  644): sources, camp definitions, 13 verbatim statements, and a machine-
  checked hand-worked golden reconstruction (`golden.json`).
- `LICENSE` (MIT), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, PR and issue
  templates.

### Fixed (soundness review of the v2 certification layer, 2026-11-14)

- A search stopped by the check budget is reported as incomplete: `report.md`
  says "SEARCH INCOMPLETE", `search_complete` is false, `abstention` is null and
  the hull is labelled partial. It was reported as cost-minimal, with abstention.
- "No system was certified" is no longer reported as "no axiom system exists":
  `existence` gives the reason (inconsistent, a soft rejection entailed) or says
  pending (unformalized statements, no verdict, search stopped).
- Cross-camp: no stated common ground from a camp whose stated claims are
  inconsistent; with unformalized statements, joint consistency and the absence
  of a stated conflict are pending; the stated tier lists reviewed statements
  only; root-divergence pairs without a verdict are listed as pending.
- The system headline reads "SUFFICIENT (kernel-checked)" only when every
  entailment was kernel-checked, and "NOT CERTIFIED" when the re-check fails.
- λ must be positive and plausibility estimates in [0, 1]; keys of the
  plausibilities file are matched in any spelling; a stated claim is never
  charged an estimate; the 0.5 default for an unscored candidate is reported.
- The hull lists only systems that some λ > 0 selects; load counts a removal
  check without verdict as pending; checks export their evidence (finite model,
  or Lean source with its SHA-256).
- Negative controls test the check they name, and a Lean that rejects everything
  no longer passes; record and candidate JSON are validated with a reason
  (exit 2, no traceback); a camp name cannot move a report outside `--out`;
  `--lean` without Lean is an error; `camp` and `crosscamp` gained `--max-checks`.

## [0.2.0] - 2026-11-13

### Added

- The logic engine: strict FOL parser, Z3 and grounding-to-SAT verdicts with
  explicit finite models, Lean 4.35 kernel certificates, MARCO-based conflict /
  concession / minimal-justification analysis, the FOLIO benchmark harness
  (reference run 195/204 with a 9-example annotation audit, Lean 128/128).
- The web app: one sourced debate, reviewer-token access, dispute suspension,
  rate limits, lockout, strict CSP; 33 + 8 end-to-end checks in CI against the
  container image.

[Unreleased]: https://github.com/ysmouhib/common-ground/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ysmouhib/common-ground/releases/tag/v0.2.0
