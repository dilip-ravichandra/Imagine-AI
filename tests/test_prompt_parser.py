import json
import random
import string
from pathlib import Path

import pytest

from ai_engine.prompt import MAX_PROMPT_CHARS, PARSER_VERSION, SCHEMA_VERSION, PromptAnalysis, analyze_prompt
from ai_engine.prompt.suite import CATEGORIES, check_case, load_suite, run_suite
from backend.app.schemas.v1 import GenerateRequest

ROOT = Path(__file__).resolve().parents[1]
SUITE = load_suite()


def names(a):
    m = {o.id: o.name for o in a.objects} | {e.id: e.name for e in a.environment}
    return {(m.get(r.subject), r.relation, m.get(r.object)) for r in a.relations}


# ---------------- raw prompt + validation ----------------
@pytest.mark.parametrize("raw", ["  A red robot\tbeside   a blue submarine \n", "Ünïcode ☃ cat", "a CAT", "x" * 500])
def test_raw_prompt_preserved_exactly(raw):
    assert analyze_prompt(raw).raw_prompt == raw


def test_empty_and_blank_invalid():
    for p in ["", "   ", "\n\t "]:
        a = analyze_prompt(p)
        assert a.validation.valid is False and a.validation.code == "EMPTY_PROMPT" and a.raw_prompt == p
        assert a.objects == [] and a.relations == []


def test_overlong_invalid_and_limit_matches_api():
    assert MAX_PROMPT_CHARS == GenerateRequest.model_fields["prompt"].metadata[1].max_length
    ok = analyze_prompt("a cat " * 83 + "ab")  # 500 chars
    assert len("a cat " * 83 + "ab") == 500 and ok.validation.valid
    bad = analyze_prompt("a" * 501)
    assert bad.validation.valid is False and bad.validation.code == "TOO_LONG" and bad.raw_prompt == "a" * 501


def test_non_string_rejected():
    with pytest.raises(TypeError):
        analyze_prompt(None)  # type: ignore[arg-type]


# ---------------- schema stability ----------------
def test_schema_keys_always_present_and_versions():
    j = analyze_prompt("a cat").model_dump(mode="json")
    assert set(j) == {"schema_version", "parser_version", "raw_prompt", "validation", "objects", "environment",
                      "relations", "lighting", "style", "negations", "ambiguities", "complexity", "notice"}
    assert j["schema_version"] == SCHEMA_VERSION and j["parser_version"] == PARSER_VERSION
    assert "CLIP" in j["notice"] and "does not verify" in j["notice"]
    assert set(j["objects"][0]) == {"id", "name", "surface", "count", "count_kind", "quantifier", "attributes",
                                    "other_modifiers", "actions", "frame_position", "lexicon_match",
                                    "evidence", "span"}


def test_committed_json_schema_matches_model():
    committed = json.loads((ROOT / "docs" / "prompt_analysis_schema_v1.json").read_text(encoding="utf-8"))
    assert committed == PromptAnalysis.model_json_schema(), "regenerate docs/prompt_analysis_schema_v1.json"


def test_deterministic():
    p = "a cat sitting on a sofa beside a lamp, soft golden light at sunset"
    assert analyze_prompt(p).model_dump_json() == analyze_prompt(p).model_dump_json()


# ---------------- required relations ----------------
@pytest.mark.parametrize("prompt,rel", [
    ("a cat beside a dog", "beside"), ("a cat next to a dog", "beside"), ("a cat behind a dog", "behind"),
    ("a cat above a dog", "above"), ("a cat below a dog", "below"), ("a cat beneath a dog", "below"),
    ("a cat to the left of a dog", "left_of"), ("a cat on the left of a dog", "left_of"),
    ("a cat to the right of a dog", "right_of"), ("a cat in front of a dog", "in_front_of"),
    ("a cat inside a dog", "inside"), ("a cat in a box", "inside")])
def test_required_relations(prompt, rel):
    a = analyze_prompt(prompt)
    assert len(a.relations) == 1 and a.relations[0].relation == rel
    assert a.relations[0].subject == "o1" and a.relations[0].object == "o2"


def test_relation_evidence_is_the_phrase():
    a = analyze_prompt("a cat in front of a dog")
    r = a.relations[0]
    assert r.evidence == "in front of" and a.raw_prompt[r.span[0]:r.span[1]] == "in front of"


def test_in_front_of_not_split_into_in_and_of():
    a = analyze_prompt("a car in front of a house")
    assert [r.relation for r in a.relations] == ["in_front_of"]


# ---------------- counts ----------------
@pytest.mark.parametrize("prompt,count,kind", [
    ("a cat", 1, "exact"), ("the cat", 1, "exact"), ("three cats", 3, "exact"), ("12 cats", 12, "exact"),
    ("cats", None, "plural_unspecified"), ("cat", None, "unspecified"), ("several cats", None, "approximate"),
    ("a couple of cats", 2, "approximate"), ("a dozen eggs", 12, "exact"), ("water", None, "unspecified"),
    ("a flock of birds", None, "approximate"), ("both cats", 2, "exact")])
def test_counts(prompt, count, kind):
    o = analyze_prompt(prompt).objects[0]
    assert (o.count, o.count_kind) == (count, kind)


def test_numeral_does_not_invent_other_counts():
    a = analyze_prompt("three red apples and an orange")
    assert [(o.name, o.count) for o in a.objects] == [("apple", 3), ("orange", 1)]
    assert [x.value for x in a.objects[0].attributes] == ["red"]


# ---------------- never invent ----------------
def test_negations_never_become_objects():
    for p in ["a street without cars", "no people", "a room with no chairs", "a beach, no birds"]:
        a = analyze_prompt(p)
        assert a.negations, p
        assert not {n.text for n in a.negations} & {o.name for o in a.objects}, p


def test_unknown_words_are_not_turned_into_attributes():
    a = analyze_prompt("a zorbly cat")
    o = a.objects[0]
    assert o.name == "cat" and o.attributes == [] and o.other_modifiers == ["zorbly"]


def test_unknown_noun_flagged_not_dropped():
    o = analyze_prompt("a glorptank").objects[0]
    assert o.name == "glorptank" and o.lexicon_match is False


def test_nothing_found_reports_ambiguity():
    a = analyze_prompt("beautiful")
    assert a.objects == [] and any(x.code == "NO_OBJECTS_FOUND" for x in a.ambiguities)


def test_non_english_flagged():
    a = analyze_prompt("一只红色的猫坐在沙发上")
    assert any(x.code == "UNSUPPORTED_LANGUAGE" for x in a.ambiguities)


def test_time_of_day_needs_preposition():
    assert analyze_prompt("a cat at night").lighting[0].value == "night"
    assert analyze_prompt("a night owl").lighting == []


def test_coreference_of_the_same_noun():
    a = analyze_prompt("a fox on a log, a tree behind the fox")
    assert [o.name for o in a.objects] == ["fox", "log", "tree"]
    assert ("tree", "behind", "fox") in names(a)


# ---------------- evidence integrity over the whole suite + fuzz ----------------
def _spans(a):
    for o in a.objects:
        yield o.evidence, o.span
        for t in o.attributes:
            yield t.evidence, t.span
    for e in a.environment:
        yield e.evidence, e.span
    for r in a.relations:
        yield r.evidence, r.span
    for t in [*a.lighting, *a.style]:
        yield t.evidence, t.span
    for n in a.negations:
        yield n.evidence, n.span


def _assert_integrity(a):
    for ev, sp in _spans(a):
        assert 0 <= sp[0] < sp[1] <= len(a.raw_prompt)
        assert a.raw_prompt[sp[0]:sp[1]] == ev
    ids = [o.id for o in a.objects] + [e.id for e in a.environment]
    assert len(ids) == len(set(ids))
    for r in a.relations:
        assert r.object in ids and (r.subject is None or r.subject in ids)
    for o in a.objects:  # every claimed attribute word is literally in the prompt
        for t in o.attributes:
            assert t.value.split()[-1] in a.raw_prompt.lower()
    assert a.complexity.object_count == len(a.objects) and a.complexity.relation_count == len(a.relations)


@pytest.mark.parametrize("case", SUITE["cases"], ids=lambda c: c["id"])
def test_evidence_integrity_on_suite_prompts(case):
    _assert_integrity(analyze_prompt(case["prompt"]))


def test_fuzz_never_raises_and_keeps_integrity():
    rng = random.Random(1234)
    vocab = ("a an the red blue cat dog robot beside behind above below left right of in on to front inside "
             "and or , . ; no without with sitting flying two three forest night sunset oil painting 3d 's "
             "'s - & ( ) \" ☃ 猫 é").split()
    for _ in range(600):
        if rng.random() < 0.7:
            p = " ".join(rng.choice(vocab) for _ in range(rng.randint(1, 25)))
        else:
            p = "".join(rng.choice(string.printable + "é猫☃") for _ in range(rng.randint(1, 80)))
        if not p.strip():
            continue
        a = analyze_prompt(p)
        assert a.raw_prompt == p
        _assert_integrity(a)


# ---------------- versioned suite ----------------
def test_suite_covers_all_categories_and_ids_unique():
    cats = {c["category"] for c in SUITE["cases"]}
    assert set(CATEGORIES) <= cats
    ids = [c["id"] for c in SUITE["cases"]]
    assert len(ids) == len(set(ids))
    assert SUITE["suite_version"] == "1.0" and SUITE["parser_target"] == PARSER_VERSION
    assert all(len(c["prompt"]) <= MAX_PROMPT_CHARS for c in SUITE["cases"])


@pytest.mark.parametrize("case", [c for c in SUITE["cases"] if c["split"] == "dev"], ids=lambda c: c["id"])
def test_dev_suite_case(case):
    assert check_case(analyze_prompt(case["prompt"]), case["expect"]) == []


def test_holdout_does_not_regress_below_first_run():
    rec = json.loads((ROOT / "evaluation" / "results" / "prompt_suite_v1_holdout_first_run.json").read_text("utf-8"))
    res = run_suite(SUITE, "holdout")
    assert len(res) == rec["total"] == 20
    assert sum(r["passed"] for r in res) >= rec["passed"], "hold-out accuracy dropped below the frozen first run"
