"""First-order formulas: syntax tree, strict parser and printers.

This module is the trust boundary of the engine. Everything that arrives as text
(a dataset annotation, a model's proposed formalization, a statement typed by a
reviewer) is parsed here into a small syntax tree, and every later stage (solver,
finite-model checker, Lean generator) works on that tree, never on the text.

Grammar, loosest binding first:

    iff      :=  implies ( ("↔" | "⟷" | "<->") implies )*
    implies  :=  xor ( ("→" | "->") implies )?            right associative
    xor      :=  or ( "⊕" or )*
    or       :=  and ( ("∨" | "|") and )*
    and      :=  unary ( ("∧" | "&") unary )*
    unary    :=  ("¬" | "~") unary | quantified | atom | "(" iff ")"
    quantified := ("∀" | "∃") VAR unary                   scope="tight" (default)
               |  ("∀" | "∃") VAR iff                     scope="wide"
    atom     :=  NAME "(" term ("," term)* ")" | NAME | term ("=" | "≠") term
    term     :=  NAME | NAME "(" term ("," term)* ")"

A NAME in term position is a variable when an enclosing quantifier binds it and a
constant otherwise. A quantifier binds one variable; write ``∀x ∀y`` for two. Two conventions are in common use for how far a quantifier
reaches when its body is not followed by the end of the formula; ``scope`` selects
one, and the benchmark reports results under both.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterator, Union

# ----------------------------------------------------------------------------- terms


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Const:
    name: str


@dataclass(frozen=True)
class Fn:
    name: str
    args: tuple["Term", ...]


Term = Union[Var, Const, Fn]

# -------------------------------------------------------------------------- formulas


@dataclass(frozen=True)
class Pred:
    name: str
    args: tuple[Term, ...] = ()


@dataclass(frozen=True)
class Eq:
    left: Term
    right: Term


@dataclass(frozen=True)
class Not:
    body: "Formula"


@dataclass(frozen=True)
class And:
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Or:
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Implies:
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Iff:
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Xor:
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Forall:
    var: str
    body: "Formula"


@dataclass(frozen=True)
class Exists:
    var: str
    body: "Formula"


Formula = Union[Pred, Eq, Not, And, Or, Implies, Iff, Xor, Forall, Exists]
BINARY = (And, Or, Implies, Iff, Xor)
QUANT = (Forall, Exists)


class ParseError(ValueError):
    """The text is not a formula of the grammar above."""

    def __init__(self, message: str, position: int = -1):
        super().__init__(message)
        self.position = position


# ---------------------------------------------------------------------------- lexer

MAX_FORMULA_CHARS = 4000
MAX_DEPTH = 200

_SYMBOLS = {
    "∀": "FORALL", "∃": "EXISTS", "¬": "NOT", "~": "NOT",
    "∧": "AND", "&": "AND", "∨": "OR", "|": "OR",
    "→": "IMPLIES", "↔": "IFF", "⟷": "IFF", "⊕": "XOR",
    "(": "LP", ")": "RP", ",": "COMMA", "=": "EQ", "≠": "NEQ",
}
_ASCII = (("<->", "IFF"), ("->", "IMPLIES"))
# Inside a name: letters and digits of any script, "_", and the three characters
# the FOLIO annotations use inside names (apostrophes and a decimal point).
_NAME_INNER = frozenset("_'’.")


def _is_name_start(ch: str) -> bool:
    return ch == "_" or unicodedata.category(ch)[0] in ("L", "N")


def _is_name_char(ch: str) -> bool:
    return ch in _NAME_INNER or unicodedata.category(ch)[0] in ("L", "N")


def tokenize(text: str) -> list[tuple[str, str, int]]:
    if len(text) > MAX_FORMULA_CHARS:
        raise ParseError(f"formula longer than {MAX_FORMULA_CHARS} characters")
    tokens: list[tuple[str, str, int]] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        for lit, kind in _ASCII:
            if text.startswith(lit, i):
                tokens.append((kind, lit, i))
                i += len(lit)
                break
        else:
            if ch in _SYMBOLS:
                tokens.append((_SYMBOLS[ch], ch, i))
                i += 1
            elif _is_name_start(ch):
                j = i + 1
                while j < n and _is_name_char(text[j]):
                    j += 1
                # a trailing "." or apostrophe belongs to the sentence, not the name
                while j > i + 1 and text[j - 1] in ".'’":
                    j -= 1
                tokens.append(("NAME", text[i:j], i))
                i = j
            else:
                raise ParseError(f"unexpected character {ch!r} at position {i}", i)
    tokens.append(("END", "", n))
    return tokens


# --------------------------------------------------------------------------- parser


class _Parser:
    def __init__(self, text: str, scope: str, connectives: str = "standard"):
        if scope not in ("tight", "wide"):
            raise ValueError("scope must be 'tight' or 'wide'")
        if connectives not in ("standard", "flat-right"):
            raise ValueError("connectives must be 'standard' or 'flat-right'")
        self.connectives = connectives
        self.toks = tokenize(text)
        self.pos = 0
        self.scope = scope
        self.bound: list[str] = []
        self.depth = 0

    def peek(self) -> str:
        return self.toks[self.pos][0]

    def take(self, kind: str) -> str:
        k, v, at = self.toks[self.pos]
        if k != kind:
            raise ParseError(f"expected {kind} but found {v or 'end of formula'!r} at position {at}", at)
        self.pos += 1
        return v

    def _enter(self) -> None:
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise ParseError("formula nested too deeply")

    def formula(self) -> Formula:
        self._enter()
        left = self.implies()
        while self.peek() == "IFF":
            self.pos += 1
            left = Iff(left, self.implies())
        self.depth -= 1
        return left

    def implies(self) -> Formula:
        self._enter()
        left = self.xor()
        if self.peek() == "IMPLIES":
            self.pos += 1
            left = Implies(left, self.implies())
        self.depth -= 1
        return left

    def xor(self) -> Formula:
        left = self.disj()
        while self.peek() == "XOR":
            self.pos += 1
            left = Xor(left, self.disj())
        return left

    def disj(self) -> Formula:
        if self.connectives == "flat-right":
            return self.flat()
        left = self.conj()
        while self.peek() == "OR":
            self.pos += 1
            left = Or(left, self.conj())
        return left

    def flat(self) -> Formula:
        """∧ and ∨ on one level, grouping to the right: ``A ∧ B ∨ C`` is ``A ∧ (B ∨ C)``."""
        self._enter()
        left = self.unary()
        kind = self.peek()
        if kind in ("AND", "OR"):
            self.pos += 1
            right = self.flat()
            left = And(left, right) if kind == "AND" else Or(left, right)
        self.depth -= 1
        return left

    def conj(self) -> Formula:
        left = self.unary()
        while self.peek() == "AND":
            self.pos += 1
            left = And(left, self.unary())
        return left

    def unary(self) -> Formula:
        self._enter()
        try:
            kind = self.peek()
            if kind == "NOT":
                self.pos += 1
                return Not(self.unary())
            if kind in ("FORALL", "EXISTS"):
                self.pos += 1
                name = self.take("NAME")
                self.bound.append(name)
                body = self.formula() if self.scope == "wide" else self.unary()
                self.bound.pop()
                return Forall(name, body) if kind == "FORALL" else Exists(name, body)
            if kind == "LP":
                self.pos += 1
                inner = self.formula()
                self.take("RP")
                return inner
            return self.atom()
        finally:
            self.depth -= 1

    def atom(self) -> Formula:
        name = self.take("NAME")
        if self.peek() == "LP":
            args = self.arguments()
            if self.peek() in ("EQ", "NEQ"):  # f(a) = b
                return self.equation(Fn(name, args))
            return Pred(name, args)
        if self.peek() in ("EQ", "NEQ"):
            return self.equation(self.name_term(name))
        return Pred(name, ())

    def equation(self, left: Term) -> Formula:
        negated = self.peek() == "NEQ"
        self.pos += 1
        eq = Eq(left, self.term())
        return Not(eq) if negated else eq

    def name_term(self, name: str) -> Term:
        return Var(name) if name in self.bound else Const(name)

    def arguments(self) -> tuple[Term, ...]:
        self.take("LP")
        args = [self.term()]
        while self.peek() == "COMMA":
            self.pos += 1
            args.append(self.term())
        self.take("RP")
        return tuple(args)

    def term(self) -> Term:
        self._enter()
        name = self.take("NAME")
        out: Term = Fn(name, self.arguments()) if self.peek() == "LP" else self.name_term(name)
        self.depth -= 1
        return out


def parse(text: str, scope: str = "tight", connectives: str = "standard") -> Formula:
    """Parse one formula. Raises ParseError on anything outside the grammar.

    ``connectives="standard"`` gives ∧ precedence over ∨. ``"flat-right"`` puts them on
    one level, grouping to the right; it exists to measure how much a result depends on
    how unbracketed mixes are read.
    """
    p = _Parser(text, scope, connectives)
    out = p.formula()
    if p.peek() != "END":
        _, v, at = p.toks[p.pos]
        raise ParseError(f"unexpected {v!r} at position {at}", at)
    return out


# --------------------------------------------------------------------------- queries


def subterms(t: Term) -> Iterator[Term]:
    yield t
    if isinstance(t, Fn):
        for a in t.args:
            yield from subterms(a)


def atoms_terms(f: Formula) -> Iterator[Term]:
    """Every term occurring in the formula (with repetitions)."""
    if isinstance(f, Pred):
        for a in f.args:
            yield from subterms(a)
    elif isinstance(f, Eq):
        yield from subterms(f.left)
        yield from subterms(f.right)
    elif isinstance(f, Not):
        yield from atoms_terms(f.body)
    elif isinstance(f, BINARY):
        yield from atoms_terms(f.left)
        yield from atoms_terms(f.right)
    else:
        yield from atoms_terms(f.body)


def subformulas(f: Formula) -> Iterator[Formula]:
    yield f
    if isinstance(f, Not) or isinstance(f, QUANT):
        yield from subformulas(f.body)
    elif isinstance(f, BINARY):
        yield from subformulas(f.left)
        yield from subformulas(f.right)


@dataclass(frozen=True)
class Signature:
    constants: tuple[str, ...]
    predicates: tuple[tuple[str, int], ...]
    functions: tuple[tuple[str, int], ...]
    uses_equality: bool


def signature(formulas: list[Formula] | tuple[Formula, ...]) -> Signature:
    consts: dict[str, None] = {}
    preds: dict[tuple[str, int], None] = {}
    funcs: dict[tuple[str, int], None] = {}
    eq = False
    for f in formulas:
        for sub in subformulas(f):
            if isinstance(sub, Pred):
                preds[(sub.name, len(sub.args))] = None
            elif isinstance(sub, Eq):
                eq = True
        for t in atoms_terms(f):
            if isinstance(t, Const):
                consts[t.name] = None
            elif isinstance(t, Fn):
                funcs[(t.name, len(t.args))] = None
    return Signature(tuple(consts), tuple(preds), tuple(funcs), eq)


class SignatureError(ValueError):
    """A symbol is used inconsistently (two arities, or as predicate and function)."""


def check_signature(sig: Signature) -> None:
    seen: dict[str, tuple[str, int]] = {}
    for kind, items in (("predicate", sig.predicates), ("function", sig.functions)):
        for name, arity in items:
            if name in seen and seen[name] != (kind, arity):
                was_kind, was_arity = seen[name]
                raise SignatureError(
                    f"{name!r} is used as a {was_kind} of {was_arity} argument(s) and as a {kind} of {arity}")
            seen[name] = (kind, arity)
    for name in sig.constants:
        if name in seen:
            raise SignatureError(f"{name!r} is used both as a constant and as a {seen[name][0]}")


# A name that looks like a variable (a single letter from u to z) but is not bound by any
# quantifier. Annotators sometimes drop the quantifier; see `close`. Deliberately narrow:
# FOLIO writes constants such as ``y1984`` (a title) and ``a`` or ``b`` are common names for
# individuals, and closing those would silently turn a fact about one thing into a law.
_VARIABLE_LIKE = re.compile(r"^[u-z]$")


def unbound_variable_like(f: Formula) -> list[str]:
    out: dict[str, None] = {}
    for t in atoms_terms(f):
        if isinstance(t, Const) and _VARIABLE_LIKE.match(t.name):
            out[t.name] = None
    return list(out)


def _rename_const_to_var(f: Formula, names: frozenset[str]) -> Formula:
    def term(t: Term) -> Term:
        if isinstance(t, Const) and t.name in names:
            return Var(t.name)
        if isinstance(t, Fn):
            return Fn(t.name, tuple(term(a) for a in t.args))
        return t

    if isinstance(f, Pred):
        return Pred(f.name, tuple(term(a) for a in f.args))
    if isinstance(f, Eq):
        return Eq(term(f.left), term(f.right))
    if isinstance(f, Not):
        return Not(_rename_const_to_var(f.body, names))
    if isinstance(f, BINARY):
        return type(f)(_rename_const_to_var(f.left, names), _rename_const_to_var(f.right, names))
    return type(f)(f.var, _rename_const_to_var(f.body, names))


def close(f: Formula) -> tuple[Formula, list[str]]:
    """Universally close unbound variable-like names; return the sentence and the names closed."""
    names = unbound_variable_like(f)
    if not names:
        return f, []
    body = _rename_const_to_var(f, frozenset(names))
    for name in reversed(names):
        body = Forall(name, body)
    return body, names


# -------------------------------------------------------------------------- printing


def term_text(t: Term) -> str:
    if isinstance(t, Fn):
        return f"{t.name}({', '.join(term_text(a) for a in t.args)})"
    return t.name


_OPS = {And: "∧", Or: "∨", Implies: "→", Iff: "↔", Xor: "⊕"}


def to_text(f: Formula) -> str:
    """Canonical, fully parenthesised text. ``parse(to_text(f)) == f`` under either scope."""
    if isinstance(f, Pred):
        return f.name if not f.args else f"{f.name}({', '.join(term_text(a) for a in f.args)})"
    if isinstance(f, Eq):
        return f"({term_text(f.left)} = {term_text(f.right)})"
    if isinstance(f, Not):
        return f"¬{to_text(f.body)}"
    if isinstance(f, BINARY):
        return f"({to_text(f.left)} {_OPS[type(f)]} {to_text(f.right)})"
    q = "∀" if isinstance(f, Forall) else "∃"
    return f"({q}{f.var} {to_text(f.body)})"
