"""CG5-2 of docs/design/cross-camp.md: the provable common ground between camps.

Two tiers (amendment A7; THEORY.md F2). Tier 1, *stated* (invariant): a reviewed
statement is common ground when every camp's E⁺ entails it — this holds for every
reconstruction. Tier 2, *reconstructed* (selection-relative): per combination of
selected systems (all ties reported), a pool statement is agreed when every selected
system entails it. Every check is a certified abduce.Check — nothing is reported as
agreed without a positive verdict, and a pending check never counts as agreement.
The per-claim derivation viewer lists, for each agreed statement, every minimal
premise set inside the union of the selected systems (argmap.justifications).
Fault lines (MUS/MCS over the union of selected systems) are CG5-3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import product

from . import abduce, argmap, fol
from .abduce import Record
from .fol import Formula

MAX_COMBINATIONS = 64   # selected-system combinations (ties can multiply); argmap.TooMany beyond


@dataclass
class Camp:
    """One camp entering the cross-camp analysis: its record plus its per-camp report."""

    record: Record
    report: dict            # the dict returned by abduce.report_camp


def _union_pool(camps: list[Camp]) -> list[tuple[str, str, str, Formula]]:
    """Every reviewed statement and every validated candidate of every camp, deduplicated
    by FOL text: (origin camp, id or "candidate", FOL text, formula)."""
    seen: set[str] = set()
    out: list[tuple[str, str, str, Formula]] = []
    for c in camps:
        for st in c.record.statements:
            f = st.formula()
            if f is None:
                continue
            text = fol.to_text(f)
            if text not in seen:
                seen.add(text)
                out.append((c.record.camp, st.id, text, f))
        for cand in c.report["pool"]["candidates"]:
            f = fol.parse(cand["fol"])
            text = fol.to_text(f)
            if text not in seen:
                seen.add(text)
                out.append((c.record.camp, "candidate", text, f))
    return out


def _agreed_by(pool_item, premises_per_camp, kind, timeout_ms, lean_bin):
    """The pool statement agreed on by every camp's premise set, with all checks; None
    when any check is not a positive verdict (pending never counts as agreement)."""
    origin, sid, text, f = pool_item
    checks = [abduce.entailment_check(premises, f, kind=kind, timeout_ms=timeout_ms, lean_bin=lean_bin)
              for premises in premises_per_camp]
    if checks and all(c.outcome == "holds" for c in checks):
        return {"statement": text, "origin": origin, "id": sid,
                "checks": [c.to_json() for c in checks]}
    return None


def common_ground(camps: list[Camp], timeout_ms: int = 5000, lean_bin: str | None = None,
                  limit: int = 2000) -> dict:
    """The common-ground section of the cross-camp report, as plain JSON-able data
    (design §3)."""
    if len(camps) < 2:
        raise ValueError("cross-camp analysis needs at least two camps")
    pool = _union_pool(camps)
    targets = [abduce._targets(c.record) for c in camps]

    # tier 1: stated claims, invariant (F2) — entailed by every camp's E⁺
    stated_agreed = [entry for entry in
                     (_agreed_by(item, targets, "common_ground_stated", timeout_ms, lean_bin)
                      for item in pool)
                     if entry is not None]
    union_consistent = abduce.consistency_check([f for t in targets for f in t], timeout_ms)
    stated = {"agreed": stated_agreed,
              "union_consistent": union_consistent.to_json(),
              "pool": [item[2] for item in pool]}

    # tier 2: reconstructed axioms, selection-relative — per combination of selected
    # certified systems (all ties reported)
    selected = [[s["axioms"] for s in c.report["systems"] if s["certified"]] for c in camps]
    no_certified = [c.record.camp for c, sel in zip(camps, selected) if not sel]
    combinations = []
    combos = list(product(*selected)) if all(selected) else []
    if len(combos) > MAX_COMBINATIONS:
        raise argmap.TooMany(f"{len(combos)} selected-system combinations (cap {MAX_COMBINATIONS})")
    for combo in combos:
        axioms_per_camp = [[fol.parse(t) for t in texts] for texts in combo]
        agreed = [entry for entry in
                  (_agreed_by(item, axioms_per_camp, "common_ground_system", timeout_ms, lean_bin)
                   for item in pool)
                  if entry is not None]
        union_axioms: dict[str, Formula] = {}
        for texts in combo:
            for t in texts:
                union_axioms[t] = fol.parse(t)
        for entry in agreed:
            try:
                entry["derivations"] = argmap.justifications(
                    union_axioms, fol.parse(entry["statement"]), timeout_ms, limit)
            except argmap.Undecided as exc:
                entry["derivations"] = None
                entry["derivations_note"] = f"pending: {exc}"
        combinations.append({"camps": [c.record.camp for c in camps],
                             "systems": [list(texts) for texts in combo],
                             "agreed": agreed})
    return {"camps": [c.record.camp for c in camps],
            "stated": stated,
            "per_system_pair": combinations,
            "no_certified_systems": no_certified}


def to_jsonable(report: dict) -> dict:
    """Round-trip guard: the report must be plain JSON data."""
    return json.loads(json.dumps(report))
