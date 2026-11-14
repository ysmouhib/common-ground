# Examples

Seed data for the engine CLI and for the v2 pipeline (build brief section 6).

| Path | What it is | Run it |
|---|---|---|
| `co2-2021/` | The golden corpus: the Swiss CO2-law votation of 13 June 2021 (swissvotes.ch vote 644) — 13 hand-worked statements with verbatim text and booklet pages in `statements.json`, and the machine-checked target reconstruction in `golden.json` | see `co2-2021/README.md`; the pipeline run on it is CG7-3 in `docs/PLAN.md` |
| `../engine/examples/plastic_bags.json` | The plastic-bag policy debate as engine input; statement ids match the web app seed (`db/seed-data.ts`) | `cd engine && python -m commonground analyze examples/plastic_bags.json` |
| `../engine/examples/remote_work.json` | A constructed contradiction that shows minimal conflicts and minimal correction sets | `cd engine && python -m commonground analyze examples/remote_work.json` |

The plastic-bag debate lives under `engine/examples/` rather than here because
the README quickstart and `engine/tests/test_generated.py` run it from `engine/`;
the same debate is what the web app seeds into MySQL. Both bundled examples run
headless, with no server, no database and no LLM key.
