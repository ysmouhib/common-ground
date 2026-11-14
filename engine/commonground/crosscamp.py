"""CG5-2 of docs/design/cross-camp.md: the provable common ground between camps.

Two tiers (amendment A7; THEORY.md F2). Tier 1, *stated* (invariant): a reviewed
statement is common ground when every camp's E⁺ entails it — this holds for every
reconstruction. Tier 2, *reconstructed* (selection-relative): per combination of
selected systems (all ties reported), a pool statement is agreed when every selected
system entails it. Every check is a certified abduce.Check — nothing is reported as
agreed without a positive verdict, and a pending check never counts as agreement.
Two things an entailment check alone would get wrong are handled here: a camp whose
stated claims are inconsistent entails everything, so tier 1 reports agreement only
when every camp's E⁺ has a model (otherwise the camp is named as vacuous or pending);
and a statement without a reviewed formalization is covered by no check, so with any
such statement "the stated claims are consistent" and "no stated conflict" are
pending, while conflicts and agreements found among the formalized ones stand.
The per-claim derivation viewer lists, for each agreed statement, every minimal
premise set inside the union of the selected systems (argmap.justifications).
Fault lines (MUS/MCS over the union of selected systems) are CG5-3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import product

from . import abduce, argmap, fol, verdict
from .abduce import Record
from .fol import Formula

MAX_COMBINATIONS = 64   # selected-system combinations (ties can multiply); argmap.TooMany beyond


@dataclass
class Camp:
    """One camp entering the cross-camp analysis: its record plus its per-camp report."""

    record: Record
    report: dict            # the dict returned by abduce.report_camp


def _camp_names(camps: list[Camp]) -> list[str]:
    """The camps' names; at least two camps, and no two with the same name (a report is
    keyed by camp name, so a repeated name would let one camp stand for another)."""
    if len(camps) < 2:
        raise ValueError("cross-camp analysis needs at least two camps")
    names = [c.record.camp for c in camps]
    if len(set(names)) != len(names):
        raise ValueError(f"camp names must be unique, got {names}")
    return names


def _unformalized(camps: list[Camp]) -> list[dict]:
    """Statements without a reviewed formalization: no check below covers them."""
    return [{"camp": c.record.camp, "id": sid} for c in camps for sid in c.record.unformalized()]


def _whole_record(check: abduce.Check, unformalized: list[dict]) -> abduce.Check:
    """A model of the formalized statements says nothing about the ones that are not
    formalized yet: consistency of all stated claims is then pending. An inconsistency
    stands — adding statements cannot remove it."""
    if check.outcome != "holds" or not unformalized:
        return check
    missing = ", ".join(f"{u['camp']}: {u['id']}" for u in unformalized)
    return abduce.Check(check.kind, check.claim, "pending", abduce.BADGE_PENDING,
                        f"the formalized stated claims have a model, but {len(unformalized)} statement(s) "
                        f"have no reviewed formalization ({missing}), so the consistency of all stated "
                        "claims is not established")


def _union_pool(camps: list[Camp], include_candidates: bool = True) -> list[tuple[str, str, str, Formula]]:
    """Every reviewed statement and (unless excluded) every validated candidate of every
    camp, deduplicated by FOL text: (origin camp, id or "candidate", FOL text, formula)."""
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
        if not include_candidates:
            continue
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
    names = _camp_names(camps)
    pool = _union_pool(camps)
    stated_pool = _union_pool(camps, include_candidates=False)
    targets = [abduce._targets(c.record) for c in camps]
    unformalized = _unformalized(camps)

    # tier 1: stated claims, invariant (F2) — a reviewed statement entailed by every camp's E⁺.
    # An inconsistent E⁺ entails everything, so agreement is reported only when every camp's
    # stated claims have a model; a camp without one makes the agreement vacuous, a camp
    # without a verdict leaves it pending.
    camp_consistency = [abduce.consistency_check(t, timeout_ms) for t in targets]
    vacuous = [n for n, chk in zip(names, camp_consistency) if chk.outcome == "fails"]
    undecided = [n for n, chk in zip(names, camp_consistency) if chk.outcome == "pending"]
    stated_agreed = [] if vacuous or undecided else [
        entry for entry in
        (_agreed_by(item, targets, "common_ground_stated", timeout_ms, lean_bin) for item in stated_pool)
        if entry is not None]
    union_consistent = _whole_record(
        abduce.consistency_check([f for t in targets for f in t], timeout_ms), unformalized)
    stated = {"agreed": stated_agreed,
              "union_consistent": union_consistent.to_json(),
              "camp_consistency": [{"camp": n, **chk.to_json()} for n, chk in zip(names, camp_consistency)],
              "vacuous_camps": vacuous, "pending_camps": undecided,
              "unformalized": unformalized,
              "pool": [item[2] for item in stated_pool]}

    # tier 2: reconstructed axioms, selection-relative — per combination of selected
    # certified systems (all ties reported)
    combos = _selected_combinations(camps)
    no_certified = [c.record.camp for c in camps
                    if not any(s["certified"] for s in c.report["systems"])]
    combinations = []
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


# ---------------------------------------------------------------------------
# CG5-3 (design §4, §6): fault lines — the reduced disagreement — and the
# combined report. MUSes of the union of the camps' E⁺ (tier 1, invariant) and
# of each selected-system combination (tier 2) come from argmap's MARCO
# enumeration; MCSes are the complements of the MSSes. A MUS is certified by a
# solver refutation (sound inside the Bernays–Schönfinkel class, ground.py);
# an undecided subset raises argmap.Undecided and the entry stays pending.
# When a union is consistent there is no conflict: the camps diverge at the
# root, reported as load-bearing axiom pairs (a₁, a₂) with A₁ ⊭ a₂ and A₂ ⊭ a₁,
# each non-entailment witnessed by an explicit finite model, ranked by
# load₁(a₁) + load₂(a₂) (brief §4). Note: argmap.enumerate_mus_mss (frozen v1)
# raises TooMany without returning partials, so a capped run aborts (CLI exit 2)
# rather than reporting an uncertified partial list.


def _sat_oracle(by_text: dict[str, Formula], timeout_ms: int):
    def is_sat(subset: frozenset) -> bool | None:
        answer = verdict.satisfiable([by_text[t] for t in sorted(subset)], timeout_ms)
        return {"sat": True, "unsat": False}.get(answer.status)
    return is_sat


def _mus_mcs(texts: list[str], timeout_ms: int, limit: int) -> tuple[list[list[str]], list[list[str]]]:
    by_text = {t: fol.parse(t) for t in texts}
    muses, msses = argmap.enumerate_mus_mss(texts, _sat_oracle(by_text, timeout_ms), limit)
    mcses = [sorted(set(texts) - s) for s in msses]
    return [sorted(m) for m in muses], mcses


def _selected_combinations(camps: list[Camp]) -> list[list[list[str]]]:
    selected = [[s["axioms"] for s in c.report["systems"] if s["certified"]] for c in camps]
    combos = list(product(*selected)) if all(selected) else []
    if len(combos) > MAX_COMBINATIONS:
        raise argmap.TooMany(f"{len(combos)} selected-system combinations (cap {MAX_COMBINATIONS})")
    return [[list(t) for t in combo] for combo in combos]


def fault_lines(camps: list[Camp], timeout_ms: int = 5000, limit: int = 2000) -> dict:
    """The fault-line section of the cross-camp report (design §4)."""
    _camp_names(camps)
    unformalized = _unformalized(camps)
    # tier 1: stated claims — MUSes/MCSes of the union of every camp's E⁺. Over the formalized
    # statements only: each MUS found is a conflict of the whole record, but with statements
    # still unformalized the list may be incomplete and "no conflict" is not established.
    targets = [f for c in camps for f in abduce._targets(c.record)]
    texts = sorted({fol.to_text(f) for f in targets})
    by_text = {t: fol.parse(t) for t in texts}
    union_consistent = _whole_record(
        abduce.consistency_check([by_text[t] for t in texts], timeout_ms), unformalized)
    try:
        mus, mcs = _mus_mcs(texts, timeout_ms, limit)
        stated = {"consistent": union_consistent.to_json(), "mus": mus, "mcs": mcs}
    except argmap.Undecided as exc:
        stated = {"consistent": union_consistent.to_json(), "mus": None, "mcs": None,
                  "pending": f"no verdict: {exc}"}
    stated["unformalized"] = unformalized
    stated["complete"] = not unformalized and stated["mus"] is not None

    # tier 2: per combination of selected certified systems
    combos = _selected_combinations(camps)
    load_by_system = [{tuple(sorted(s["axioms"])): {row["axiom"]: row["load"] for row in s["load"]}
                       for s in c.report["systems"] if s["certified"]} for c in camps]
    load_pending = [{tuple(sorted(s["axioms"])): {row["axiom"]: row.get("pending", 0) for row in s["load"]}
                     for s in c.report["systems"] if s["certified"]} for c in camps]
    pairs = []
    for combo in combos:
        union_texts = sorted({t for texts_ in combo for t in texts_})
        axioms_per_camp = [[fol.parse(t) for t in texts_] for texts_ in combo]
        entry = {"camps": [c.record.camp for c in camps], "systems": combo}
        try:
            mus, mcs = _mus_mcs(union_texts, timeout_ms, limit)
            entry["mus"] = mus
            entry["mcs"] = mcs
            entry["consistent"] = not mus
        except argmap.Undecided as exc:
            entry["mus"] = None
            entry["mcs"] = None
            entry["consistent"] = None
            entry["pending"] = f"no verdict: {exc}"
        roots = []
        roots_pending = []   # pairs whose non-entailment, or whose load, has no verdict: never dropped silently
        if entry["consistent"]:
            for i in range(len(combo)):
                for j in range(i + 1, len(combo)):
                    key_i, key_j = tuple(sorted(combo[i])), tuple(sorted(combo[j]))
                    loads_i, loads_j = load_by_system[i][key_i], load_by_system[j][key_j]
                    pend_i, pend_j = load_pending[i][key_i], load_pending[j][key_j]
                    for a in combo[i]:
                        if loads_i.get(a, 0) <= 0 and not pend_i.get(a, 0):
                            continue  # established: not load-bearing
                        for b in combo[j]:
                            if loads_j.get(b, 0) <= 0 and not pend_j.get(b, 0):
                                continue
                            pair = {"camp1": camps[i].record.camp, "a1": a,
                                    "camp2": camps[j].record.camp, "a2": b}
                            if loads_i.get(a, 0) <= 0 or loads_j.get(b, 0) <= 0:
                                roots_pending.append({**pair, "pending": "load not established"})
                                continue
                            c1 = abduce.non_entailment_check(axioms_per_camp[i], fol.parse(b),
                                                             kind="root_divergence", timeout_ms=timeout_ms)
                            c2 = abduce.non_entailment_check(axioms_per_camp[j], fol.parse(a),
                                                             kind="root_divergence", timeout_ms=timeout_ms)
                            if c1.outcome == "holds" and c2.outcome == "holds":
                                roots.append({**pair, "rank": loads_i[a] + loads_j[b],
                                              "rank_is_lower_bound": bool(pend_i.get(a, 0) or pend_j.get(b, 0)),
                                              "checks": [c1.to_json(), c2.to_json()]})
                            elif "pending" in (c1.outcome, c2.outcome) and "fails" not in (c1.outcome, c2.outcome):
                                roots_pending.append({**pair, "pending": "non-entailment undecided"})
            roots.sort(key=lambda r: -r["rank"])
        entry["root_divergence"] = roots
        entry["root_divergence_pending"] = roots_pending
        pairs.append(entry)
    no_certified = [c.record.camp for c in camps
                    if not any(s["certified"] for s in c.report["systems"])]
    return {"stated": stated, "per_system_pair": pairs, "no_certified_systems": no_certified}


def analyze(camps: list[Camp], timeout_ms: int = 5000, lean_bin: str | None = None,
            limit: int = 2000) -> dict:
    """The full cross-camp report: common ground (CG5-2) plus fault lines (CG5-3)."""
    return {"camps": [c.record.camp for c in camps],
            # camps whose search the check budget stopped: their systems are certified, but not
            # shown to be cost-minimal, so every selection-relative section is provisional for them
            "search_incomplete": [c.record.camp for c in camps
                                  if c.report.get("search_complete", True) is False],
            "common_ground": common_ground(camps, timeout_ms, lean_bin, limit),
            "fault_lines": fault_lines(camps, timeout_ms, limit)}


def render_markdown(report: dict) -> str:
    """crosscamp.md. Describes, never diagnoses; never promises that showing common
    ground reduces disagreement (Lord, Ross & Lepper 1979; RESEARCH.md)."""
    cg = report["common_ground"]
    fl = report["fault_lines"]
    lines = [f"# Cross-camp analysis — camps {', '.join(f'`{c}`' for c in report['camps'])}",
             "",
             "Provable common ground and exact fault lines — certified deductions, "
             "not claims about what anyone believes.", ""]
    if report.get("search_incomplete"):
        lines += ["**Search incomplete for " + ", ".join(f"`{c}`" for c in report["search_incomplete"])
                  + ".** The check budget stopped that search: the systems compared below are certified, "
                    "but not shown to be cost-minimal, so the selection-relative sections (reconstructed "
                    "axioms) are provisional. The sections on stated claims do not depend on it.", ""]
    lines += ["## Common ground among stated claims (invariant — holds for every reconstruction)", ""]
    cons = cg["stated"]["union_consistent"]
    lines.append(f"Union of the camps' stated E⁺ is consistent: **{cons['outcome']}** "
                 f"({cons['badge']}).")
    missing = cg["stated"].get("unformalized") or fl["stated"].get("unformalized") or []
    if missing:
        lines += ["", f"{len(missing)} statement(s) have no reviewed formalization ("
                      + ", ".join(f"{u['camp']}: {u['id']}" for u in missing)
                      + "): no check covers them. Agreements listed here stand; consistency and the "
                        "absence of a conflict are PENDING for the whole record."]
    vacuous = cg["stated"].get("vacuous_camps") or []
    undecided = cg["stated"].get("pending_camps") or []
    if vacuous:
        lines += ["", "No stated common ground is reported: the stated claims of "
                      + ", ".join(f"`{c}`" for c in vacuous)
                      + " are inconsistent, so every statement would follow from them vacuously."]
    elif undecided:
        lines += ["", "Stated common ground is PENDING: the consistency of the stated claims of "
                      + ", ".join(f"`{c}`" for c in undecided) + " has no verdict."]
    elif cg["stated"]["agreed"]:
        lines += ["", "| agreed statement | origin | badges |", "|---|---|---|"]
        for e in cg["stated"]["agreed"]:
            badges = ", ".join(sorted({c["badge"] for c in e["checks"]}))
            lines.append(f"| `{e['statement']}` | {e['origin']} ({e['id']}) | {badges} |")
    else:
        lines += ["", "No stated claim is entailed by every camp."]
    lines += ["", "## Common ground among reconstructed axioms (selection-relative)", ""]
    if cg["per_system_pair"]:
        for k, pair in enumerate(cg["per_system_pair"], start=1):
            lines += [f"### Combination {k}: " + "; ".join(
                f"`{camp}`: " + ", ".join(f"`{a}`" for a in system)
                for camp, system in zip(pair["camps"], pair["systems"])), ""]
            if pair["agreed"]:
                lines += ["| agreed statement | derivations (minimal premise sets) |", "|---|---|"]
                for e in pair["agreed"]:
                    d = e.get("derivations")
                    dtxt = "pending" if d is None else str(len(d))
                    lines.append(f"| `{e['statement']}` | {dtxt} |")
            else:
                lines.append("No pool statement is entailed by every selected system.")
            lines.append("")
    else:
        lines += ["No certified selected systems to compare.", ""]
    lines += ["## Fault lines among stated claims (invariant)", ""]
    st = fl["stated"]
    if st.get("mus") is None:
        lines += [f"Pending: {st.get('pending', 'capped')}", ""]
    elif st["mus"]:
        lines += ["Minimal conflicts (each certified by a solver refutation):", ""]
        for m in st["mus"]:
            lines.append("- " + "; ".join(f"`{x}`" for x in m))
        lines += ["", "Smallest concessions (MCS, complements of the maximal consistent sets):", ""]
        for m in st["mcs"]:
            lines.append("- give up " + ", ".join(f"`{x}`" for x in m))
        if missing:
            lines += ["", "Computed over the formalized statements: each conflict above is a conflict "
                          "of the whole record, but the list may be incomplete and the concessions "
                          "are relative to the formalized statements."]
    elif missing:
        lines += ["No conflict among the formalized stated claims. PENDING for the whole record: "
                  "the statements without a formalization are not covered.", ""]
    else:
        lines += ["The stated claims are jointly consistent: no stated conflict.", ""]
    lines += ["", "## Fault lines among reconstructed axioms (selection-relative)", ""]
    for k, pair in enumerate(fl["per_system_pair"], start=1):
        lines += [f"### Combination {k}", ""]
        if pair.get("mus") is None:
            lines += [f"Pending: {pair.get('pending', 'capped')}", ""]
        elif pair["mus"]:
            lines += ["Fault lines (MUSes of the union of the selected systems):", ""]
            for m in pair["mus"]:
                lines.append("- " + "; ".join(f"`{x}`" for x in m))
            lines += ["", "Smallest concessions:", ""]
            for m in pair["mcs"]:
                lines.append("- give up " + ", ".join(f"`{x}`" for x in m))
            lines.append("")
        elif pair["consistent"]:
            lines += ["The selected systems are jointly consistent: no contradiction — "
                      "the camps diverge at the root:", "",
                      "| camp 1 axiom | camp 2 axiom | downstream claims explained (rank) |",
                      "|---|---|---|"]
            for r in pair["root_divergence"]:
                rank = f"{r['rank']}" + (" (at least)" if r.get("rank_is_lower_bound") else "")
                lines.append(f"| `{r['a1']}` ({r['camp1']}) | `{r['a2']}` ({r['camp2']}) | {rank} |")
            lines.append("")
            pending = pair.get("root_divergence_pending") or []
            if pending:
                lines += [f"{len(pending)} further axiom pair(s) are PENDING (no verdict on the "
                          "non-entailment or on the load); they are listed in crosscamp.json.", ""]
        else:
            lines += ["Consistent union.", ""]
    return "\n".join(lines)
