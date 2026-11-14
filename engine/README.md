# commonground-engine

First-order verdicts with checked evidence: a parser, two decision engines, Lean
kernel certificates, conflict analysis, and a benchmark. Given reviewed statements
of one or more camps, it reports sets of formulas that are **verified sufficient**
to generate a camp's claims, ranks them by a declared cost, and shows where two
camps' systems agree and clash. It certifies deductions, not truth and not belief.

Every verdict carries a badge: `SUFFICIENT` (kernel-checked, needs a Lean 4
executable via `LEAN_BIN` and `--lean`), `SOLVER-CHECKED` (Z3 refutation / finite
model), or `PENDING` (no verdict — never silently picked).

## Install

```bash
pip install commonground-engine
```

Requires Python >= 3.10. Dependencies (`z3-solver`, `python-sat`) install automatically.

## Quickstart

```bash
python -m commonground check --premise "∀x (Human(x) → Mortal(x))" --premise "Human(socrates)" --conclusion "Mortal(socrates)"
python -m commonground --help
```

Add `--lean` to `check` for a kernel-checked certificate (set `LEAN_BIN` to a Lean 4.35.0
`lean` executable); without it the same argument is answered `SOLVER-CHECKED`.

Commands: `check` (one argument), `analyze` (conflicts, concessions, justifications
for a debate file), `camp` / `crosscamp` (per-camp axiom systems and cross-camp
common ground / fault lines from reviewed records), `co2` (the bundled golden
example, end to end), `extract` (statements from text, with verbatim spans, via a
configured LLM endpoint), `folio` / `compare` / `report` (benchmarks and run reports).

## Documentation

Full documentation, the worked CO2 example with a screenshot, the research behind
the definitions, and the recorded benchmark runs:
https://github.com/ysmouhib/common-ground

## License

MIT.
