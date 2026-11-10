"""Benchmark runs on FOLIO. Every number in the repository's README comes from ``reference``."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import time
from collections import Counter
from pathlib import Path

from . import folio, lean
from .fol import And, BINARY, Formula, Not, Or, ParseError, QUANT, parse
from .ground import epr_bound
from .verdict import decide

LABELS = ("True", "False", "Uncertain")


def engine_hash() -> str:
    """Hash of the engine's source files: pins a results file to the code that produced it."""
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def environment(lean_bin: str | None) -> dict:
    import pysat
    import z3
    return {
        "python": platform.python_version(),
        "z3": z3.get_version_string(),
        "pysat": pysat.__version__,
        "lean": lean.TOOLCHAIN if lean_bin else None,
        "engine_sha256": engine_hash(),
    }


def _flatten(f: Formula):
    """The formula with nested ∧ (and nested ∨) flattened, so regrouping alone does not count as a change."""
    if isinstance(f, (And, Or)):
        parts = []
        for side in (f.left, f.right):
            g = _flatten(side)
            parts.extend(g[1] if isinstance(g, tuple) and g[0] == type(f).__name__ else [g])
        return (type(f).__name__, parts)
    if isinstance(f, Not):
        return ("Not", _flatten(f.body))
    if isinstance(f, BINARY):
        return (type(f).__name__, _flatten(f.left), _flatten(f.right))
    if isinstance(f, QUANT):
        return (type(f).__name__, f.var, _flatten(f.body))
    return f


def bracketing_ambiguous(text: str) -> bool:
    """Does the formula mix ∧ and ∨ without brackets, so that the two reading conventions differ?"""
    try:
        return _flatten(parse(text)) != _flatten(parse(text, connectives="flat-right"))
    except ParseError:
        return False


def _verdicts(examples, scope: str, connectives: str, timeout_ms: int, engine: str = "auto"):
    rows = []
    for ex in examples:
        row = {"index": ex.index, "gold": ex.label}
        try:
            parsed = folio.parse_example(ex, scope=scope, connectives=connectives)
        except ParseError as exc:
            rows.append({**row, "verdict": "ParseError", "note": str(exc), "parsed": None})
            continue
        verdict = decide(parsed.premises, parsed.conclusion, timeout_ms, engine)
        rows.append({**row, "verdict": verdict.label, "parsed": parsed, "detail": verdict})
    return rows


def _agreement(rows) -> int:
    return sum(r["verdict"] == r["gold"] for r in rows)


def reference(data_file: Path, out_dir: Path, lean_bin: str | None, timeout_ms: int = 5000) -> dict:
    """Decide every FOLIO validation example from the dataset's own formulas and audit the result."""
    examples = folio.load(data_file)
    started = time.time()
    rows = _verdicts(examples, "auto", "standard", timeout_ms)
    solver_seconds = time.time() - started

    # Second engine: grounding to SAT. Where it gives a definite answer it must agree with the first.
    cross = {"compared": 0, "agree": 0, "grounding_definite": 0, "in_decidable_class": 0}
    for r in rows:
        if r["parsed"] is None:
            continue
        p = r["parsed"]
        r["decidable_class"] = epr_bound(p.premises + [p.conclusion]) is not None and \
            epr_bound(p.premises + [Not(p.conclusion)]) is not None
        cross["in_decidable_class"] += r["decidable_class"]
        other = decide(p.premises, p.conclusion, timeout_ms, engine="grounding").label
        r["grounding"] = other
        if other != "Undecided":
            cross["grounding_definite"] += 1
        if other != "Undecided" and r["verdict"] != "Undecided":
            cross["compared"] += 1
            cross["agree"] += other == r["verdict"]

    # Lean: certify every entailment verdict; offer every false statement as a soundness probe.
    lean_stats = None
    if lean_bin:
        proofs, probes = [], []
        for r in rows:
            if r["parsed"] is None:
                continue
            p = r["parsed"]
            if r["verdict"] == "True":
                proofs.append((r, p.premises, p.conclusion))
                probes.append((p.premises, Not(p.conclusion)))
            elif r["verdict"] == "False":
                proofs.append((r, p.premises, Not(p.conclusion)))
                probes.append((p.premises, p.conclusion))
            elif r["verdict"] == "Uncertain":
                probes += [(p.premises, p.conclusion), (p.premises, Not(p.conclusion))]
            elif r["verdict"] == "Inconsistent":
                proofs.append((r, p.premises, None))
        started = time.time()
        certificates = lean.certify([(pr, goal) for _, pr, goal in proofs], lean_bin)
        proof_seconds = time.time() - started
        for (r, _, _), certificate in zip(proofs, certificates):
            r["lean"] = "certified" if certificate.accepted else f"not certified: {certificate.reason}"
        started = time.time()
        wrongly = sum(c.accepted for c in lean.certify(probes, lean_bin))
        lean_stats = {
            "entailment_verdicts": len(proofs),
            "certified_by_kernel": sum(c.accepted for c in certificates),
            "axioms_used": sorted({a for c in certificates for a in c.axioms}),
            "seconds": round(proof_seconds, 1),
            "false_statements_offered": len(probes),
            "false_statements_accepted": wrongly,
            "probe_seconds": round(time.time() - started, 1),
        }

    # How much do the results depend on reading conventions?
    conventions = {}
    for scope in ("auto", "tight", "wide"):
        for connectives in ("standard", "flat-right"):
            if (scope, connectives) == ("auto", "standard"):
                conventions["auto/standard"] = _agreement(rows)
            else:
                conventions[f"{scope}/{connectives}"] = _agreement(_verdicts(examples, scope, connectives, timeout_ms))
    alt = {r["index"]: r["verdict"] for r in _verdicts(examples, "auto", "flat-right", timeout_ms)}
    for r in rows:
        r["verdict_flat_right"] = alt[r["index"]]

    parsed_rows = [r for r in rows if r["parsed"] is not None]
    confusion = Counter((r["gold"], r["verdict"]) for r in rows)
    summary = {
        "dataset": {"name": "FOLIO validation", "examples": len(examples),
                    "revision": folio.revision(data_file.parents[2]), "licence": "CC BY-SA 4.0"},
        "environment": environment(lean_bin),
        "parsing": {
            "examples_parsed": len(parsed_rows),
            "examples_with_a_malformed_formula": len(rows) - len(parsed_rows),
            "examples_needing_bracket_repair": sum(bool(r["parsed"].repaired_brackets) for r in parsed_rows),
            "examples_with_unbound_variables_closed": sum(bool(r["parsed"].closed_variables) for r in parsed_rows),
            "examples_with_ambiguous_bracketing": sum(
                any(bracketing_ambiguous(folio.repair_brackets(t)[0]) for t in ex.premises_fol + [ex.conclusion_fol])
                for ex in examples),
            "examples_with_unequal_sentence_and_formula_counts": sum(
                len(ex.premises_text) != len(ex.premises_fol) for ex in examples),
        },
        "agreement_with_labels": {"agree": _agreement(rows), "of": len(rows),
                                  "rate": round(_agreement(rows) / len(rows), 4)},
        "confusion_gold_then_verdict": {f"{g} -> {v}": n for (g, v), n in sorted(confusion.items())},
        "verdict_counts": dict(Counter(r["verdict"] for r in rows)),
        "second_engine": cross,
        "lean": lean_stats,
        "agreement_by_reading_convention": conventions,
        "solver_seconds": round(solver_seconds, 1),
        "disagreements": [r["index"] for r in rows if r["verdict"] != r["gold"]],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with open(out_dir / "per_example.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["index", "gold_label", "verdict", "agrees", "verdict_if_and_or_grouped_right",
                         "second_engine_verdict", "in_decidable_class", "lean", "countermodel_sizes", "note"])
        for r in rows:
            detail = r.get("detail")
            sizes = ""
            if detail is not None:
                sizes = "/".join(str(m.size) for m in (detail.model_true, detail.model_false) if m is not None)
            writer.writerow([r["index"], r["gold"], r["verdict"], r["verdict"] == r["gold"], r["verdict_flat_right"],
                             r.get("grounding", ""), r.get("decidable_class", ""), r.get("lean", ""), sizes,
                             r.get("note", "")])
    return summary


def wilson_interval(successes: int, n: int, z: float = 1.959964) -> tuple[float, float] | None:
    """Wilson score interval for a proportion (95 % by default). None when there is no observation."""
    if n == 0:
        return None
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact(only_first: int, only_second: int) -> float:
    """Two-sided exact McNemar p-value from the two discordant counts of a paired comparison."""
    n = only_first + only_second
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(only_first, only_second) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def _interval(successes: int, n: int) -> list[float] | None:
    interval = wilson_interval(successes, n)
    return [round(interval[0], 4), round(interval[1], 4)] if interval else None


REFUSALS_IN_A_ROW = 3


class ConfigurationMismatch(ValueError):
    """The output directory already holds a run made with another mode, model or provider."""


def with_model(data_file: Path, out_dir: Path, client, mode: str, limit: int | None = None,
               timeout_ms: int = 5000) -> dict:
    """Run a language model on FOLIO validation: ``mode`` is "llm" (formalize, then solve) or "direct".

    Results are appended to ``runs.jsonl`` as they arrive, so an interrupted run can be resumed.
    A provider failure stops the run instead of being scored as a wrong answer. A request the
    provider refuses as such (HTTP 400 or 422) is recorded as ``ProviderRefused``, unless
    ``REFUSALS_IN_A_ROW`` of them come one after the other: that is a setting the provider does
    not accept, not a property of the examples, so the run stops and none of them is recorded.
    """
    from . import formalize  # imported here: the reference benchmark must not depend on it
    if mode not in ("llm", "direct"):
        raise ValueError('mode must be "llm" or "direct"')
    examples = folio.load(data_file)[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)

    describe = getattr(client, "describe", None)
    config = {"mode": mode, "client": describe() if callable(describe) else {"model": type(client).__name__}}
    config_file = out_dir / "config.json"
    if config_file.exists():
        previous = json.loads(config_file.read_text(encoding="utf-8"))
        if previous != config:
            raise ConfigurationMismatch(
                f"{out_dir} holds a run made with {previous}; use an empty directory for {config}")
    else:
        config_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    log = out_dir / "runs.jsonl"
    done = {}
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done[row["index"]] = row
    refused: list[dict] = []  # refusals not yet written: they may turn out to be a configuration problem

    def record(fh, row: dict) -> None:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        done[row["index"]] = row

    with open(log, "a", encoding="utf-8") as fh:
        for ex in examples:
            if ex.index in done:
                continue
            row = {"index": ex.index, "gold": ex.label, "mode": mode}
            started = time.time()
            try:
                if mode == "direct":
                    row["verdict"], usage = formalize.direct(client, ex.premises_text, ex.conclusion_text)
                    row["usage"] = [usage]
                else:
                    verdict, result = formalize.answer(client, ex.premises_text, ex.conclusion_text,
                                                       timeout_ms=timeout_ms)
                    row.update(verdict=verdict.label, attempts=result.attempts, usage=result.usage,
                               formulas_by_premise=result.by_sentence, conclusion_formula=result.conclusion_text)
            except formalize.FormalizationError as exc:
                row.update(verdict="NoFormalization", attempts=len(exc.history))
            except formalize.ProviderError as exc:
                if exc.status not in (400, 422):
                    raise
                row.update(verdict="ProviderRefused", note=str(exc)[:300], seconds=round(time.time() - started, 2))
                refused.append(row)
                if len(refused) >= REFUSALS_IN_A_ROW:
                    raise formalize.ProviderError(
                        f"{len(refused)} requests in a row were refused, the last with: {exc}. "
                        "That is a setting the provider does not accept (the model name, response_format, "
                        "temperature, max_tokens), not the examples; nothing was recorded for them.",
                        exc.status) from None
                continue
            row["seconds"] = round(time.time() - started, 2)
            for earlier in refused:  # an answer followed: those refusals were about their own examples
                record(fh, earlier)
            refused.clear()
            record(fh, row)
        for earlier in refused:
            record(fh, earlier)
    rows = [done[ex.index] for ex in examples]
    answered = [r for r in rows if r["verdict"] in LABELS]
    correct = sum(r["verdict"] == r["gold"] for r in rows)
    correct_answered = sum(r["verdict"] == r["gold"] for r in answered)
    tokens = Counter()
    for r in rows:
        for used in r.get("usage", []):
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if isinstance(used.get(key), int):
                    tokens[key] += used[key]
    confusion = Counter((r["gold"], r["verdict"]) for r in rows)
    summary = {
        **config,
        "dataset": {"name": "FOLIO validation", "examples": len(rows),
                    "revision": folio.revision(data_file.parents[2]), "licence": "CC BY-SA 4.0"},
        "examples": len(rows),
        "correct": correct,
        "accuracy": round(correct / len(rows), 4) if rows else None,
        "accuracy_interval_95": _interval(correct, len(rows)),
        "answered": len(answered),
        "accuracy_when_answered": round(correct_answered / len(answered), 4) if answered else None,
        "accuracy_when_answered_interval_95": _interval(correct_answered, len(answered)),
        "verdict_counts": dict(Counter(r["verdict"] for r in rows)),
        "confusion_gold_then_verdict": {f"{g} -> {v}": n for (g, v), n in sorted(confusion.items())},
        "tokens": dict(tokens),
        "environment": environment(None),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def _runs(directory: Path) -> dict[int, dict]:
    rows = {}
    for line in (directory / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows[row["index"]] = row
    return rows


def compare(first_dir: Path, second_dir: Path) -> dict:
    """Paired comparison of two model runs on the examples both of them answered or failed.

    The two runs see the same examples, so the test is McNemar's: only the examples on
    which exactly one run is right carry information about which run is better.
    """
    first, second = _runs(first_dir), _runs(second_dir)
    shared = sorted(set(first) & set(second))
    if not shared:
        raise ValueError("the two runs have no example in common")
    for index in shared:
        if first[index]["gold"] != second[index]["gold"]:
            raise ValueError(f"example {index} has different labels in the two runs: not the same dataset")
    right_first = {i for i in shared if first[i]["verdict"] == first[i]["gold"]}
    right_second = {i for i in shared if second[i]["verdict"] == second[i]["gold"]}
    only_first, only_second = len(right_first - right_second), len(right_second - right_first)

    def side(directory: Path, right: set[int]) -> dict:
        config = json.loads((directory / "config.json").read_text(encoding="utf-8")) \
            if (directory / "config.json").exists() else {}
        return {"directory": str(directory), **config, "correct": len(right),
                "accuracy": round(len(right) / len(shared), 4), "accuracy_interval_95": _interval(len(right), len(shared))}

    return {
        "examples_compared": len(shared),
        "first": side(first_dir, right_first),
        "second": side(second_dir, right_second),
        "both_right": len(right_first & right_second),
        "only_first_right": only_first,
        "only_second_right": only_second,
        "neither_right": len(shared) - len(right_first | right_second),
        "mcnemar_exact_p": round(mcnemar_exact(only_first, only_second), 6),
    }


RUN_NAMES = {"direct": "The model answers itself", "llm": "The model writes formulas, the solver answers"}


def _percent(value: float | None) -> str:
    # Two decimals: the summaries store proportions to four places, so nothing is rounded twice.
    return "n/a" if value is None else f"{100 * value:.2f} %"


def _reference_on(indices: list[int], published: Path) -> tuple[int, int] | None:
    """How many of these examples the reference run gets right, from its per-example file."""
    try:
        with open(published / "per_example.csv", newline="", encoding="utf-8") as fh:
            agrees = {int(row["index"]): row["agrees"] == "True" for row in csv.DictReader(fh)}
    except (OSError, KeyError, ValueError):
        return None
    if not all(i in agrees for i in indices):
        return None
    return sum(agrees[i] for i in indices), len(indices)


def report(first_dir: Path, second_dir: Path, published: Path | None = None) -> str:
    """Markdown summary of two model runs: each run's accuracy with its interval, then the paired comparison."""
    comparison = compare(first_dir, second_dir)
    summaries = [json.loads((d / "summary.json").read_text(encoding="utf-8")) for d in (first_dir, second_dir)]
    client = summaries[0].get("client", {})
    lines = [
        f"## FOLIO validation with `{client.get('model', 'an unnamed model')}` ({client.get('host', 'unknown host')})",
        "",
        "| Run | Examples | Correct | Accuracy | 95 % interval | Answered | Accuracy when answered | Tokens |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for summary in summaries:
        interval = summary.get("accuracy_interval_95")
        lines.append("| {name} | {n} | {correct} | {accuracy} | {interval} | {answered} | {when} | {tokens} |".format(
            name=RUN_NAMES.get(summary.get("mode"), summary.get("mode", "?")),
            n=summary["examples"], correct=summary["correct"], accuracy=_percent(summary["accuracy"]),
            interval=f"{_percent(interval[0])} to {_percent(interval[1])}" if interval else "n/a",
            answered=summary["answered"], when=_percent(summary["accuracy_when_answered"]),
            tokens=summary.get("tokens", {}).get("total_tokens")
            or sum(summary.get("tokens", {}).get(k, 0) for k in ("prompt_tokens", "completion_tokens")) or "not reported"))
    lines += [
        "",
        f"On the {comparison['examples_compared']} examples both runs cover: both right on "
        f"{comparison['both_right']}, only the first on {comparison['only_first_right']}, only the second on "
        f"{comparison['only_second_right']}, neither on {comparison['neither_right']}. "
        f"Exact McNemar test on the two middle counts: p = {comparison['mcnemar_exact_p']:.4g}.",
    ]
    published = published or Path(__file__).resolve().parents[2] / "results" / "folio-validation"
    shared = sorted(set(_runs(first_dir)) & set(_runs(second_dir)))
    reference_run = _reference_on(shared, published)
    if reference_run:
        lines += ["", f"For scale, the dataset's own formulas through the same solver agree with the label on "
                      f"{reference_run[0]} of these {reference_run[1]} examples."]
    for summary in summaries:
        counts = ", ".join(f"{verdict}: {n}" for verdict, n in sorted(summary["verdict_counts"].items()))
        lines += ["", f"{RUN_NAMES.get(summary.get('mode'), summary.get('mode', '?'))}, verdicts given: {counts}."]
    lines += ["", "An answer that is not one of True, False, Uncertain (no usable formalization, an inconsistent "
                  "one, a refused request) counts as wrong in \"Accuracy\" and is left out of \"Answered\"."]
    return "\n".join(lines) + "\n"
