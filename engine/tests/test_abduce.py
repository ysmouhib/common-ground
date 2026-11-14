import json

import pytest

from commonground import abduce, fol

DOC = "All humans are mortal. Socrates is a human. Therefore Socrates is mortal."
DOC2 = "Every politician promises change."
S1 = (0, DOC.index(".") + 1)
S2 = (S1[1] + 1, S1[1] + 1 + len("Socrates is a human."))


def record(**overrides):
    r = abduce.Record(
        camp="campA",
        documents=[abduce.Document("d1", DOC), abduce.Document("d2", DOC2)],
        statements=[
            abduce.RecordStatement("e1", abduce.STANCE_ENDORSED, "Mortal(socrates)", "d1", DOC[S1[0]:S2[1]], (S1[0], S2[1])),
            abduce.RecordStatement("r1", abduce.STANCE_FIRM, None, "d2", DOC2, (0, len(DOC2))),
        ],
    )
    for key, value in overrides.items():
        setattr(r, key, value)
    return r


def candidate(fol_text, quotes):
    return abduce.Candidate(fol_text, quotes)


GOOD_QUOTE = ("d1", DOC[S1[0]:S1[1]], S1)


def test_record_validation_accepts_verbatim_spans_and_parses_fol():
    record().validate()


@pytest.mark.parametrize("mutate, problem", [
    (lambda r: r.statements[0].__setattr__("span", (0, 3)), "does not match"),
    (lambda r: r.statements[0].__setattr__("span", (0, 10_000)), "outside document"),
    (lambda r: r.statements[0].__setattr__("stance", "maybe"), "stance"),
    (lambda r: r.statements[0].__setattr__("document", "nope"), "unknown document"),
    (lambda r: r.statements[0].__setattr__("fol_text", "Mortal((socrates)"), "expected NAME"),
    (lambda r: r.statements.append(r.statements[0]), "unique"),
    (lambda r: r.documents.append(abduce.Document("d1", "other")), "unique"),
])
def test_record_validation_rejects(mutate, problem):
    r = record()
    mutate(r)
    with pytest.raises(ValueError, match=problem):
        r.validate()


def test_scripted_source_returns_candidates_once_per_call_in_order():
    c1 = candidate("∀x (Human(x) → Mortal(x))", [GOOD_QUOTE])
    c2 = candidate("Human(socrates)", [("d1", DOC[S2[0]:S2[1]], S2)])
    src = abduce.ScriptedSource([c1, c2])
    pool = abduce.collect(src, record())
    assert src.calls == ["campA"]
    assert [fol.to_text(c.formula) for c in pool.candidates] == [
        fol.to_text(fol.parse("∀x (Human(x) → Mortal(x))")), fol.to_text(fol.parse("Human(socrates)"))]
    assert pool.dropped == []
    # every quote span exists verbatim in its source document
    docs = record().documents_by_id()
    for c in pool.candidates:
        for doc_id, quote, (start, end) in c.quotes:
            assert docs[doc_id].text[start:end] == quote


@pytest.mark.parametrize("cand, problem", [
    (candidate("not a formula", [GOOD_QUOTE]), "does not parse"),
    (candidate("Human(socrates)", []), "no supporting quote"),
    (candidate("Human(socrates)", [("d1", "Socrates is a mortal.", S1)]), "does not match"),
    (candidate("Human(socrates)", [("nope", DOC[:5], (0, 5))]), "unknown document"),
    (candidate("Human(socrates)", [("d1", DOC[:5], (0, 10_000))]), "outside document"),
    (candidate("  ", [GOOD_QUOTE]), "no FOL text"),
])
def test_invalid_candidates_are_dropped_with_reason(cand, problem):
    pool = abduce.collect(abduce.ScriptedSource([cand]), record())
    assert pool.candidates == []
    assert len(pool.dropped) == 1 and problem in pool.dropped[0].reason


def test_duplicate_candidates_are_dropped():
    cand = candidate("Human(socrates)", [GOOD_QUOTE])
    pool = abduce.collect(abduce.ScriptedSource([cand, cand]), record())
    assert len(pool.candidates) == 1
    assert pool.dropped[0].reason == "duplicate candidate"


def test_too_many_candidates_is_refused():
    cands = [candidate("Human(socrates)", [("d1", DOC[S1[0]:S1[1]], S1)]) for _ in range(abduce.MAX_CANDIDATES + 1)]
    with pytest.raises(ValueError, match="at most"):
        abduce.collect(abduce.ScriptedSource(cands), record())


def test_collect_is_deterministic_for_a_scripted_source():
    c1 = candidate("∀x (Human(x) → Mortal(x))", [GOOD_QUOTE])
    first = abduce.collect(abduce.ScriptedSource([c1]), record())
    second = abduce.collect(abduce.ScriptedSource([c1]), record())
    assert [fol.to_text(c.formula) for c in first.candidates] == [fol.to_text(c.formula) for c in second.candidates]


class Scripted:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def describe(self):
        return {"model": "scripted-chat", "temperature": 0.0}

    def complete(self, system, user):
        self.calls.append((system, user))
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply, {"total_tokens": 10}


GOOD_REPLY = json.dumps({"candidates": [
    {"fol": "∀x (Human(x) → Mortal(x))",
     "quotes": [{"document": "d1", "text": DOC[S1[0]:S1[1]], "span": list(S1)}]},
]})


def test_chat_source_parses_json_and_validates():
    src = abduce.ChatSource(Scripted(GOOD_REPLY))
    pool = abduce.collect(src, record())
    assert [fol.to_text(c.formula) for c in pool.candidates] == [fol.to_text(fol.parse("∀x (Human(x) → Mortal(x))"))]
    assert pool.dropped == []
    assert src.describe() == {"model": "scripted-chat", "temperature": 0.0}


def test_chat_source_accepts_fenced_reply_and_retries_bad_json():
    client = Scripted("not json", "```json" + chr(10) + GOOD_REPLY + chr(10) + "```")
    pool = abduce.collect(abduce.ChatSource(client), record())
    assert len(pool.candidates) == 1 and len(client.calls) == 2


def test_chat_source_without_json_raises():
    src = abduce.ChatSource(Scripted("nope", "still nope", "and nope"))
    with pytest.raises(ValueError, match="no JSON object"):
        abduce.collect(src, record())


def test_chat_source_drops_a_candidate_with_a_bad_span():
    reply = json.dumps({"candidates": [
        {"fol": "Human(socrates)",
         "quotes": [{"document": "d1", "text": "Socrates is a mortal.", "span": list(S1)}]},
    ]})
    pool = abduce.collect(abduce.ChatSource(Scripted(reply)), record())
    assert pool.candidates == [] and "does not match" in pool.dropped[0].reason
