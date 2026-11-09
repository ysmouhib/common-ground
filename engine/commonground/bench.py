"""Benchmark runs on FOLIO. Every number in the repository's README comes from ``reference``."""
from __future__ import annotations

import csv
import hashlib
import json
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


def with_model(data_file: Path, out_dir: Path, client, mode: str, limit: int | None = None,
               timeout_ms: int = 5000) -> dict:
    """Run a language model on FOLIO validation: ``mode`` is "llm" (formalize, then solve) or "direct".

    Results are appended to ``runs.jsonl`` as they arrive, so an interrupted run can be resumed.
    """
    from . import formalize  # imported here: the reference benchmark must not depend on it
    examples = folio.load(data_file)[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "runs.jsonl"
    done = {}
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
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
                               formulas=result.premises_text + [result.conclusion_text])
            except formalize.FormalizationError as exc:
                row.update(verdict="NoFormalization", attempts=len(exc.history))
            row["seconds"] = round(time.time() - started, 2)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            done[ex.index] = row
    rows = [done[ex.index] for ex in examples]
    answered = [r for r in rows if r["verdict"] in LABELS]
    summary = {
        "mode": mode, "examples": len(rows),
        "accuracy": round(sum(r["verdict"] == r["gold"] for r in rows) / len(rows), 4),
        "answered": len(answered),
        "accuracy_when_answered": round(sum(r["verdict"] == r["gold"] for r in answered) / len(answered), 4)
        if answered else None,
        "verdict_counts": dict(Counter(r["verdict"] for r in rows)),
        "environment": environment(None),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
