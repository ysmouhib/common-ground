"""Where do two positions actually disagree, and what could they both accept?

A debate is a set of formal statements, each owned by a position (or shared).
Three questions are answered by search rather than by labelling:

* Are the positions compatible? Yes iff all their premises together have a model.
* If not, where exactly do they clash? The minimal unsatisfiable subsets (MUSes)
  are the irreducible conflicts; the minimal correction sets (MCSes) are the
  smallest sets of statements whose withdrawal restores consistency, and their
  complements, the maximal satisfiable subsets (MSSes), are the largest bodies of
  statements that can be held together.
* What does each conclusion really depend on? Its justifications are the minimal
  sets of premises that entail it.

Enumeration is MARCO (Liffiton et al.): a SAT solver over "which statements are
in the subset" proposes unexplored subsets, a satisfiability oracle classifies
them, and each MUS or MSS found blocks its supersets or subsets.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable, Hashable, Iterable

from pysat.solvers import Solver

from .fol import Formula, Not, parse, to_text
from .verdict import decide, satisfiable


class Undecided(RuntimeError):
    """The satisfiability oracle could not classify a subset, so the enumeration is not exhaustive."""


class TooMany(RuntimeError):
    """More subsets than the caller's limit; raise the limit or accept a partial picture."""


def enumerate_mus_mss(items: list[Hashable], is_satisfiable: Callable[[frozenset], bool | None],
                      limit: int = 2000) -> tuple[list[frozenset], list[frozenset]]:
    """All minimal unsatisfiable and all maximal satisfiable subsets of ``items``.

    ``is_satisfiable`` must be monotone: every subset of a satisfiable set is satisfiable.
    """
    index = {item: i + 1 for i, item in enumerate(items)}
    cache: dict[frozenset, bool] = {}

    def sat(subset: frozenset) -> bool:
        if subset not in cache:
            answer = is_satisfiable(subset)
            if answer is None:
                raise Undecided(f"could not decide a subset of {len(subset)} statement(s)")
            cache[subset] = answer
        return cache[subset]

    muses: list[frozenset] = []
    msses: list[frozenset] = []
    with Solver(name="glucose4") as seeds:
        for i in index.values():  # make every variable known to the solver
            seeds.add_clause([i, -i])
        while seeds.solve():
            model = set(seeds.get_model())
            seed = frozenset(item for item, i in index.items() if i in model)
            if sat(seed):
                for item in items:  # grow to a maximal satisfiable subset
                    if item not in seed and sat(seed | {item}):
                        seed = seed | {item}
                msses.append(seed)
                outside = [index[item] for item in items if item not in seed]
                if not outside:
                    break  # everything together is satisfiable: one MSS, no MUS
                seeds.add_clause(outside)
            else:
                for item in items:  # shrink to a minimal unsatisfiable subset
                    if item in seed and not sat(seed - {item}):
                        seed = seed - {item}
                muses.append(seed)
                if not seed:
                    break  # unsatisfiable with no statement at all: the empty set is the only MUS
                seeds.add_clause([-index[item] for item in seed])
            if len(muses) + len(msses) > limit:
                raise TooMany(f"more than {limit} minimal conflicts and maximal consistent sets")
    return muses, msses


def minimal_hitting_sets(sets: list[frozenset], universe: Iterable[Hashable]) -> list[frozenset]:
    """Brute-force minimal hitting sets. Used to cross-check MCSes against MUSes on small inputs."""
    universe = list(universe)
    found: list[frozenset] = []
    for mask in sorted(range(1 << len(universe)), key=lambda m: bin(m).count("1")):
        candidate = frozenset(u for i, u in enumerate(universe) if mask >> i & 1)
        if any(prior <= candidate for prior in found):
            continue
        if all(candidate & s for s in sets):
            found.append(candidate)
    return found


# ------------------------------------------------------------------------------ debates


@dataclass(frozen=True)
class Statement:
    id: str
    owner: str        # a position name, or "shared"
    kind: str         # "conclusion" marks a statement to be derived; anything else is a premise
    formula: Formula | None
    text: str = ""


def load_debate(path: str) -> tuple[dict, list[Statement]]:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    statements = []
    for row in raw["statements"]:
        formula = parse(row["fol"]) if row.get("fol") else None
        statements.append(Statement(row["id"], row["owner"], row["kind"], formula, row.get("text", "")))
    ids = [s.id for s in statements]
    if len(set(ids)) != len(ids):
        raise ValueError("statement ids must be unique")
    return raw, statements


def input_hash(statements: list[Statement]) -> str:
    """Hash of exactly what the analysis depends on, so a stored analysis can be pinned to its input."""
    canon = [[s.id, s.owner, s.kind, to_text(s.formula) if s.formula else None] for s in statements]
    return hashlib.sha256(json.dumps(canon, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _oracle(formulas: dict[str, Formula], hard: list[Formula], timeout_ms: int):
    def check(subset: frozenset) -> bool | None:
        answer = satisfiable([formulas[i] for i in sorted(subset)] + hard, timeout_ms)
        return {"sat": True, "unsat": False}.get(answer.status)
    return check


def justifications(premises: dict[str, Formula], conclusion: Formula, timeout_ms: int = 5000,
                   limit: int = 2000) -> list[list[str]]:
    """Every minimal set of premises that entails ``conclusion`` and is itself consistent."""
    ids = sorted(premises)
    muses, _ = enumerate_mus_mss(ids, _oracle(premises, [Not(conclusion)], timeout_ms), limit)
    consistent = _oracle(premises, [], timeout_ms)
    out = []
    for m in muses:
        status = consistent(m)
        if status is None:
            raise Undecided("could not decide whether a candidate justification is consistent")
        if status:  # drop "anything follows from a contradiction"
            out.append(sorted(m))
    return sorted(out, key=lambda j: (len(j), j))


def analyze(statements: list[Statement], timeout_ms: int = 5000, limit: int = 2000) -> dict:
    """The full report for one debate, as plain data."""
    premises = {s.id: s.formula for s in statements if s.kind != "conclusion" and s.formula is not None}
    conclusions = [s for s in statements if s.kind == "conclusion" and s.formula is not None]
    owner = {s.id: s.owner for s in statements}
    positions = sorted({s.owner for s in statements if s.owner != "shared"})
    ids = sorted(premises)

    muses, msses = enumerate_mus_mss(ids, _oracle(premises, [], timeout_ms), limit)
    compatible = not muses
    witness = satisfiable([premises[i] for i in ids], timeout_ms) if compatible else None

    def side(position: str) -> dict[str, Formula]:
        return {i: f for i, f in premises.items() if owner[i] in (position, "shared")}

    report_conclusions = {}
    for c in conclusions:
        from_all = decide([premises[i] for i in ids], c.formula, timeout_ms)
        per_position = {p: decide(list(side(p).values()), c.formula, timeout_ms).label for p in positions}
        report_conclusions[c.id] = {
            "owner": c.owner,
            "from_all_premises": from_all.label,
            "from_each_position": per_position,
            "justifications": justifications(premises, c.formula, timeout_ms, limit),
        }

    def describe(subset: frozenset) -> dict:
        members = sorted(subset)
        return {"statements": members, "positions": sorted({owner[i] for i in members})}

    conflicts = sorted((describe(m) for m in muses), key=lambda d: (len(d["statements"]), d["statements"]))
    # A correction set is what must be withdrawn to reach a maximal consistent set. When
    # everything is consistent the only one is empty: there is nothing to concede.
    corrections = [frozenset(ids) - m for m in msses]
    concessions = sorted((describe(c) for c in corrections if c),
                         key=lambda d: (len(d["statements"]), d["statements"]))
    in_every_mss = sorted(set(ids).intersection(*msses)) if msses else []
    return {
        "input_hash": input_hash(statements),
        "premise_ids": ids,
        "positions": positions,
        "positions_compatible": compatible,
        "compatibility_witness": (
            {"domain_size": witness.structure.size, "engine": witness.engine,
             "rechecked_by_independent_evaluator": True}
            if witness is not None and witness.structure is not None else None),
        "conflicts": conflicts,                      # minimal unsatisfiable subsets
        "minimal_concessions": concessions,          # minimal correction sets
        "uncontested": in_every_mss,                 # premises in every maximal consistent set
        "position_consistent": {p: satisfiable(list(side(p).values()), timeout_ms).status == "sat"
                                for p in positions},
        "conclusions": report_conclusions,
        "statements_without_formula": sorted(s.id for s in statements if s.formula is None),
    }
