# Example: a pasted debate text, end to end (clinton-debate-2016)

A local test of the whole v2 pipeline on one long, realistic user input: an excerpt of
Hillary Clinton's answers in the first 2016 US presidential debate (a public debate
transcript), 30,281 characters, pasted as one text. Everything here is recorded output
from a real run on 2026-11-14; nothing was invented. No API key appears in any file —
the key is only ever read from the `LLM_API_KEY` environment variable, and each run's
`config.json` records model/host/settings, never the key.

## The pipeline this exercises

```
pasted text ──extract──> statements (verbatim quotes + spans) ──formalize──> record.json ──camp──> report
```

This is exactly the flow of the web app's Camps view (paste texts → extract → review /
formalize → per-camp report); here it runs headless through the engine CLI. The web app
does the formalization review in the UI; here `build_record.py` does it with one LLM
call per statement.

## What each file is

| Path | What it is |
|---|---|
| `input/clinton-debate-raw.txt` | The pasted text as given, 30,281 characters. Kept to document the input cap below. |
| `input/clinton-debate-1.txt`, `input/clinton-debate-2.txt` | The raw text split in two at a paragraph boundary (~15k chars each), because `extract` refuses a single document over **20,000 characters** ("the document must be non-empty text of at most 20000 characters", see `logs/extract.log`). |
| `extract-out/` | The recorded live extract run: `runs.jsonl` (one row per document: statements, relations, attempts, token usage), `summary.json`, `config.json` (model, host, settings — no key). |
| `build_record.py` | Turns `extract-out/runs.jsonl` into a camp record by formalizing each statement (one LLM call each, `GRAMMAR_CARD` prompt, `fol.parse`-validated; up to 2 attempts per statement). |
| `record.json` | The recorded output of `build_record.py`: camp `clinton-2016-debate`, both documents, 80 statements with stance `endorsed`, `fol` where formalization parsed, `quote` + `span` always. |
| `record-small.json` | The first 12 formalized statements as a record small enough for `camp` (see the pool cap below). |
| `candidates.json` | Empty candidate pool (`{"candidates": []}`): this test exercises the stated system only. |
| `logs/extract.log`, `logs/formalize.log` | Console logs of the two live runs, including the 20,000-character refusal and the per-statement ok/FAILED lines. |

## Recorded results (2026-11-14, deepseek-flash, temperature 0)

- **Extract** at `--max-tokens 16000` (the new quote-only prompt): **2 of 2 documents,
  80 statements + 33 relations, 0 failed** — 2 attempts on part 1 (11,854 + 6,698
  completion tokens), 1 attempt on part 2 (12,157 tokens). All 80 quotes were re-checked
  against the source files: verbatim, spans consistent. For comparison, the old
  offset-asking prompt extracted 0 of 3 longer documents at 2000/4000 tokens and 0 of 2
  at 16000 (see `docs/BACKLOG.md`).
- **Formalize**: **67 of 80** statements parsed into FOL (`logs/formalize.log`); 13
  stayed unformalized. In the product they are shown as PENDING, never dropped.
- **`camp` limits hit**: the full record was refused — "pool of 67 exceeds the cap of
  16" (`MAX_POOL`; the documented scope is "tens of statements"). A `camp --lean` run on
  the 12-statement `record-small.json` (with `LEAN_BIN` set to a Lean 4.35.0 binary, so
  sufficiency would be kernel-checked, badge SUFFICIENT) was still in its search phase
  after ~30 minutes and was stopped; no report was written. Both caps — 20,000
  characters per document, 16 pool items — are the first limits a user hits on a long
  pasted text; raising them is an owner decision.

## Reproduce

From the repo root, with the key in the environment only:

```bash
cd engine
LLM_API_KEY=... python -X utf8 -m commonground extract \
  ../examples/clinton-debate-2016/input/clinton-debate-1.txt \
  ../examples/clinton-debate-2016/input/clinton-debate-2.txt \
  --base-url https://api.deepseek.com/v1 --model deepseek-flash \
  --max-tokens 16000 --out /tmp/debate-extract

cd ../examples/clinton-debate-2016
LLM_API_KEY=... python -X utf8 build_record.py     # rewrites record.json / candidates.json

cd ../../engine
LEAN_BIN=~/.elan/toolchains/leanprover--lean4---v4.35.0/bin/lean.exe \
python -X utf8 -m commonground camp \
  ../examples/clinton-debate-2016/record-small.json \
  --candidates ../examples/clinton-debate-2016/candidates.json --lean --out /tmp/debate-camp
```

`extract` and `build_record.py` need a live LLM endpoint; `camp` does not (solver-only
runs read SOLVER-CHECKED, with `--lean` and `LEAN_BIN` the selected system's sufficiency
is kernel-checked). Any OpenAI-compatible endpoint works via `--base-url`/`--model`;
a local one (e.g. Ollama) keeps the text on the machine.
