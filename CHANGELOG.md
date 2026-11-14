# Changelog

All notable changes to this project are documented here, in Keep a Changelog
format. Versions follow Semantic Versioning.

## [Unreleased]

### Added (v2 build-out, phases 0-2 and 7 so far)

- `engine/commonground/extract.py`: statement extraction from text with
  verbatim quotes and character spans (validated against the source), support/
  attack relations between statements, schema-validated repair loop, resumable
  runs with `config.json`/`runs.jsonl` provenance; `python -m commonground
  extract <files> --out DIR`.
- Live language-model benchmark on FOLIO validation (deepseek-flash,
  2026-11-13, results in `results/direct` and `results/llm`): direct answering
  162/204 (79.4 %), formalize-then-solve 119/204 (58.3 %, 81.5 % when a
  formalization parses); Wilson intervals and exact McNemar in the README.
- Golden corpus skeleton `examples/co2-2021/` (Swiss CO2-law votation, vote
  644): sources, camp definitions, 13 verbatim statements, and a machine-
  checked hand-worked golden reconstruction (`golden.json`).
- `LICENSE` (MIT), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, PR and issue
  templates.

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
