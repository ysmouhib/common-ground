"""FOLIO: loading and the reference-formalization benchmark.

FOLIO (Han et al., 2022, CC BY-SA 4.0) pairs short natural-language arguments with
first-order formalizations and a label True / False / Uncertain. The dataset is not
redistributed here; ``fetch`` downloads it from the authors' repository.

The benchmark in this file uses FOLIO's own formalizations, so it involves no
language model. It answers two questions any formalize-then-prove system has to
answer first:

1. Does a solver, given the dataset's formulas, reproduce the dataset's labels?
   Where it does not, no formalizer scored against those labels can be right for
   the right reason, so this is a ceiling and an audit of the annotations.
2. How many of those verdicts can be certified down to the Lean kernel?
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .fol import Formula, ParseError, SignatureError, check_signature, close, parse, signature, \
    unbound_variable_like

REPOSITORY = "https://github.com/Yale-LILY/FOLIO.git"
VALIDATION = "data/v0.0/folio-validation.jsonl"


def fetch(target: Path) -> Path:
    """Clone the dataset repository (shallow) unless it is already there; return the validation file."""
    if not (target / VALIDATION).exists():
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", REPOSITORY, str(target)], check=True)
    return target / VALIDATION


def revision(target: Path) -> str:
    out = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


@dataclass
class Example:
    index: int
    premises_text: list[str]
    conclusion_text: str
    premises_fol: list[str]
    conclusion_fol: str
    label: str


def load(path: Path) -> list[Example]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            row = json.loads(line)
            label = {"Unknown": "Uncertain"}.get(row["label"], row["label"])
            premises = row["premises"]
            premises = premises if isinstance(premises, list) else premises.split("\n")
            fol = row["premises-FOL"]
            fol = fol if isinstance(fol, list) else fol.split("\n")
            out.append(Example(i, premises, row["conclusion"], fol, row.get("conclusion-FOL", ""), label))
    return out


@dataclass
class Parsed:
    premises: list[Formula]
    conclusion: Formula
    repaired_brackets: int = 0       # formulas whose surplus closing brackets were dropped
    closed_variables: int = 0        # formulas with unbound variable-like names, universally closed
    wide_scope_used: int = 0         # formulas where the quantifier had to reach past its bracket
    issues: list[str] = field(default_factory=list)


def _balanced(text: str) -> bool:
    depth = 0
    for ch in text:
        depth += (ch == "(") - (ch == ")")
        if depth < 0:
            return False
    return depth == 0


def repair_brackets(text: str) -> tuple[str, bool]:
    """Drop surplus closing brackets at the very end of a formula (an annotation typo).

    Applied only when that alone makes the brackets balance; nothing else is repaired.
    """
    surplus = text.count(")") - text.count("(")
    stripped = text.rstrip()
    if surplus > 0 and stripped.endswith(")" * surplus) and _balanced(stripped[: len(stripped) - surplus]):
        return stripped[: len(stripped) - surplus], True
    return text, False


def parse_formula(text: str, scope: str, connectives: str = "standard") -> tuple[Formula, bool]:
    """Parse under a scope convention. Returns the formula and whether wide scope was used.

    ``auto`` reads a quantifier as covering its bracket only, unless that leaves one of
    its variables unbound in the rest of the formula and the wide reading binds it.
    """
    if scope in ("tight", "wide"):
        return parse(text, scope, connectives), scope == "wide"
    tight = parse(text, "tight", connectives)
    if unbound_variable_like(tight):
        wide = parse(text, "wide", connectives)
        if not unbound_variable_like(wide):
            return wide, True
    return tight, False


def parse_example(ex: Example, scope: str = "auto", repair: bool = True, close_free: bool = True,
                  connectives: str = "standard") -> Parsed:
    """Parse one example or raise ParseError / SignatureError naming the formula at fault."""
    out = Parsed([], None)  # type: ignore[arg-type]
    formulas = []
    for position, text in enumerate(ex.premises_fol + [ex.conclusion_fol]):
        where = "conclusion" if position == len(ex.premises_fol) else f"premise {position + 1}"
        if repair:
            text, changed = repair_brackets(text)
            out.repaired_brackets += changed
        try:
            f, wide = parse_formula(text, scope, connectives)
        except ParseError as exc:
            raise ParseError(f"{where}: {exc}") from None
        out.wide_scope_used += wide
        if close_free:
            f, names = close(f)
            out.closed_variables += bool(names)
        elif unbound_variable_like(f):
            out.issues.append(f"{where}: unbound variable-like name treated as a constant")
        formulas.append(f)
    try:
        check_signature(signature(formulas))
    except SignatureError as exc:
        out.issues.append(f"signature: {exc}")
    out.premises, out.conclusion = formulas[:-1], formulas[-1]
    return out
