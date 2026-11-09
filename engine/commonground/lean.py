"""Lean 4 certificates for verdicts.

A verdict "the premises entail the conclusion" is restated as a Lean theorem and
handed to Lean's own automation. If Lean accepts it and the axiom audit is clean,
the verdict no longer rests on the SMT solver: it has been checked by the kernel.

Security. Lean runs arbitrary code while elaborating a file (``#eval``, macros,
``initialize``), so untrusted text must never reach it. Nothing here is written
by a model or a user: this module generates every character of the source from
the syntax tree, symbols are renamed to ``p0, c0, x0, ...`` before printing, and
``assert_generated`` refuses to run a source containing any token outside that
vocabulary.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .fol import (And, Const, Eq, Exists, Fn, Forall, Formula, Iff, Implies, Not, Or, Pred, Term, Var, Xor,
                  signature)

TOOLCHAIN = "4.35.0"
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
HEADER = "set_option linter.unusedVariables false\nset_option maxHeartbeats 400000\nnamespace CG\n"
FOOTER = "end CG\n"

_KEYWORDS = frozenset(
    "set_option linter unusedVariables false maxHeartbeats namespace end CG theorem Entity Type Prop by first "
    "grind splitImp true have obtain False print axioms".split())
_GENERATED = re.compile(r"^(?:[pcfxhiek]\d+|t_\d+|w|\d+)$")
_SYMBOLS = frozenset("()→↔∧∨¬∀∃,:=|.#⟨⟩; \n")


class UnsafeSource(ValueError):
    """The text is not something this module generates; it is not passed to Lean."""


def assert_generated(source: str) -> None:
    for token in re.findall(r"[A-Za-z_0-9']+|[^A-Za-z_0-9'\s]", source):
        if token in _KEYWORDS or _GENERATED.match(token) or token in _SYMBOLS:
            continue
        raise UnsafeSource(f"token {token!r} is outside the generated vocabulary")


class _Names:
    def __init__(self, formulas: list[Formula]):
        sig = signature(formulas)
        self.pred = {key: f"p{i}" for i, key in enumerate(sig.predicates)}
        self.const = {name: f"c{i}" for i, name in enumerate(sig.constants)}
        self.func = {key: f"f{i}" for i, key in enumerate(sig.functions)}

    def binders(self) -> str:
        parts = ["(Entity : Type)", "(w : Entity)"]
        for (_, arity), ident in self.pred.items():
            parts.append(f"({ident} : {'Entity → ' * arity}Prop)")
        for (_, arity), ident in self.func.items():
            parts.append(f"({ident} : {'Entity → ' * arity}Entity)")
        for ident in self.const.values():
            parts.append(f"({ident} : Entity)")
        return " ".join(parts)

    def table(self) -> dict:
        return {
            "predicates": {ident: f"{name}/{arity}" for (name, arity), ident in self.pred.items()},
            "constants": {ident: name for name, ident in self.const.items()},
            "functions": {ident: f"{name}/{arity}" for (name, arity), ident in self.func.items()},
        }


def _term(t: Term, names: _Names, env: dict[str, str]) -> str:
    if isinstance(t, Var):
        return env[t.name]
    if isinstance(t, Const):
        return names.const[t.name]
    return "(" + " ".join([names.func[(t.name, len(t.args))]] + [_term(a, names, env) for a in t.args]) + ")"


def _formula(f: Formula, names: _Names, env: dict[str, str], depth: int) -> str:
    if isinstance(f, Pred):
        head = names.pred[(f.name, len(f.args))]
        return head if not f.args else "(" + " ".join([head] + [_term(a, names, env) for a in f.args]) + ")"
    if isinstance(f, Eq):
        return f"({_term(f.left, names, env)} = {_term(f.right, names, env)})"
    if isinstance(f, Not):
        return f"(¬ {_formula(f.body, names, env, depth)})"
    if isinstance(f, (Forall, Exists)):
        bound = f"x{depth}"
        body = _formula(f.body, names, {**env, f.var: bound}, depth + 1)
        return f"({'∀' if isinstance(f, Forall) else '∃'} {bound} : Entity, {body})"
    a, b = _formula(f.left, names, env, depth), _formula(f.right, names, env, depth)
    if isinstance(f, And):
        return f"({a} ∧ {b})"
    if isinstance(f, Or):
        return f"({a} ∨ {b})"
    if isinstance(f, Implies):
        return f"({a} → {b})"
    if isinstance(f, Iff):
        return f"({a} ↔ {b})"
    if isinstance(f, Xor):
        return f"(¬ ({a} ↔ {b}))"
    raise TypeError(f"not a formula: {f!r}")


def _universal_prefix(f: Formula) -> tuple[int, Formula]:
    n = 0
    while isinstance(f, Forall):
        n, f = n + 1, f.body
    return n, f


def _hints(premises: list[Formula], names: _Names, budget: int = 160) -> list[str]:
    """Instantiate universally quantified premises at the named individuals, and open
    existential ones. This only adds consequences of the hypotheses; Lean still checks
    every step, so a useless hint costs time and nothing else."""
    lines: list[str] = []
    individuals = ["w"] + list(names.const.values())
    counter = 0
    for i, premise in enumerate(premises):  # existential premises introduce a witness each
        if isinstance(premise, Exists):
            lines.append(f"obtain ⟨e{i}, k{i}⟩ := h{i}")
            individuals.append(f"e{i}")
    for i, premise in enumerate(premises):
        arity, _ = _universal_prefix(premise)
        if arity == 0 or len(individuals) ** arity > budget - counter:
            continue
        stack = [[]]
        for _ in range(arity):
            stack = [prefix + [ind] for prefix in stack for ind in individuals]
        for args in stack:
            lines.append(f"have i{counter} := h{i} {' '.join(args)}")
            counter += 1
    return lines


@dataclass
class Theorem:
    name: str
    source: str
    symbols: dict


def theorem(index: int, premises: list[Formula], goal: Formula | None, hints: bool = True) -> Theorem:
    """Lean text of "premises ⊢ goal"; ``goal=None`` states that the premises are contradictory."""
    names = _Names(premises + ([goal] if goal is not None else []))
    hyps = " ".join(f"(h{i} : {_formula(p, names, {}, 0)})" for i, p in enumerate(premises))
    target = "False" if goal is None else _formula(goal, names, {}, 0)
    # Tried in order; the first that closes the goal is what the kernel checks.
    script = ["  first", "    | grind", "    | grind (splitImp := true)"]
    hint_lines = _hints(premises, names) if hints else []
    if hint_lines:
        prefix = "; ".join(hint_lines)
        script.append(f"    | ({prefix}; grind)")
        script.append(f"    | ({prefix}; grind (splitImp := true))")
    text = f"theorem t_{index} {names.binders()} {hyps} : {target} := by\n" + "\n".join(script) + "\n"
    return Theorem(f"t_{index}", text, names.table())


def assemble(theorems: list[Theorem]) -> str:
    body = "\n".join(t.source for t in theorems)
    audit = "".join(f"#print axioms CG.{t.name}\n" for t in theorems)
    return HEADER + body + FOOTER + audit


@dataclass
class Certificate:
    name: str
    accepted: bool
    axioms: list[str] = field(default_factory=list)
    reason: str = ""


def find_lean() -> str | None:
    """Path of a Lean executable of the pinned version, or None."""
    for candidate in (os.environ.get("LEAN_BIN"), shutil.which("lean")):
        if candidate and Path(candidate).exists():
            out = subprocess.run([candidate, "--version"], capture_output=True, text=True, timeout=30)
            if f"version {TOOLCHAIN}" in out.stdout:
                return candidate
    return None


_ERROR = re.compile(r"^[^\n:]*:(\d+):\d+: error: (.*)$", re.MULTILINE)
_AXIOMS = re.compile(r"^'CG\.(t_\d+)' depends on axioms: \[([^\]]*)\]", re.MULTILINE)
_NO_AXIOMS = re.compile(r"^'CG\.(t_\d+)' does not depend on any axioms", re.MULTILINE)


def run(theorems: list[Theorem], lean_bin: str, timeout_s: int = 300) -> dict[str, Certificate]:
    """Compile the theorems in one Lean process and report, per theorem, whether the kernel accepted it."""
    source = assemble(theorems)
    assert_generated(source)
    spans: dict[str, range] = {}
    line = HEADER.count("\n") + 1
    for t in theorems:
        height = t.source.count("\n") + 1
        spans[t.name] = range(line, line + height)
        line += height
    workdir = tempfile.mkdtemp(prefix="commonground-lean-")
    try:
        path = Path(workdir) / "Certificates.lean"
        path.write_text(source, encoding="utf-8")
        try:
            proc = subprocess.run([lean_bin, str(path)], cwd=workdir, capture_output=True, text=True,
                                  timeout=timeout_s, env={"PATH": os.environ.get("PATH", ""), "HOME": workdir})
            output = proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            return {t.name: Certificate(t.name, False, reason=f"Lean exceeded {timeout_s}s") for t in theorems}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    failed: dict[str, str] = {}
    for match in _ERROR.finditer(output):
        number = int(match.group(1))
        for name, span in spans.items():
            if number in span:
                failed.setdefault(name, match.group(2)[:200])
    audited: dict[str, list[str]] = {m.group(1): [] for m in _NO_AXIOMS.finditer(output)}
    for match in _AXIOMS.finditer(output):
        audited[match.group(1)] = [a.strip() for a in match.group(2).split(",") if a.strip()]

    out: dict[str, Certificate] = {}
    for t in theorems:
        if t.name in failed:
            out[t.name] = Certificate(t.name, False, reason=failed[t.name])
        elif t.name not in audited:
            out[t.name] = Certificate(t.name, False, reason="no axiom report: the theorem was not added")
        elif not set(audited[t.name]) <= ALLOWED_AXIOMS:
            out[t.name] = Certificate(t.name, False, audited[t.name], "depends on a non-standard axiom")
        else:
            out[t.name] = Certificate(t.name, True, audited[t.name])
    return out


def certify(problems: list[tuple[list[Formula], Formula | None]], lean_bin: str, chunk: int = 40,
            timeout_s: int = 300, hints: bool = True) -> list[Certificate]:
    """Certify each (premises, goal); problems are batched to share Lean's start-up cost."""
    results: list[Certificate] = []
    for start in range(0, len(problems), chunk):
        batch = [theorem(start + i, p, g, hints) for i, (p, g) in enumerate(problems[start:start + chunk])]
        certificates = run(batch, lean_bin, timeout_s)
        results.extend(certificates[t.name] for t in batch)
    return results
