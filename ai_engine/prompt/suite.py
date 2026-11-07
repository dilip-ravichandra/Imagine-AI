"""Checker for the versioned prompt suite (evaluation/prompts/prompt_suite_v1.json).

An `expect` block is matched against a PromptAnalysis. Lists of lighting/style/environment/negations/
ambiguities are subset checks; objects and relations are exact unless the block says otherwise.
"""
import json
from pathlib import Path
from typing import Any

from .parser import analyze_prompt
from .schema import PromptAnalysis

SUITE_PATH = Path(__file__).resolve().parents[2] / "evaluation" / "prompts" / "prompt_suite_v1.json"
CATEGORIES = ["simple", "multi_object", "attributes", "relations", "scene_lighting", "ambiguous", "long", "unseen"]


def load_suite(path: Path = SUITE_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _obj_matches(o, exp: dict) -> bool:
    if o.name != exp["name"]:
        return False
    for k in ("count", "count_kind", "frame_position"):
        if k in exp and getattr(o, k) != exp[k]:
            return False
    for typ, vals in exp.get("attributes", {}).items():
        have = {a.value for a in o.attributes if a.type == typ}
        if not set(vals) <= have:
            return False
    if "actions" in exp and not set(exp["actions"]) <= set(o.actions):
        return False
    if "other_modifiers" in exp and not set(exp["other_modifiers"]) <= set(o.other_modifiers):
        return False
    return True


def check_case(a: PromptAnalysis, exp: dict) -> list[str]:
    fails: list[str] = []
    if a.validation.valid != exp.get("valid", True):
        fails.append(f"valid={a.validation.valid}")
    if "objects" in exp:
        pool = list(a.objects)
        for e in exp["objects"]:
            hit = next((o for o in pool if _obj_matches(o, e)), None)
            if hit is None:
                fails.append(f"missing object {e}; got {[(o.name, o.count, [x.value for x in o.attributes]) for o in a.objects]}")
            else:
                pool.remove(hit)
        if exp.get("exact_objects", True) and pool:
            fails.append(f"unexpected objects {[o.name for o in pool]}")
    names = {o.id: o.name for o in a.objects} | {e.id: e.name for e in a.environment}
    if "relations" in exp:
        got = {(names.get(r.subject, None), r.relation, names.get(r.object, None)) for r in a.relations}
        want = {tuple(r) for r in exp["relations"]}
        if want - got:
            fails.append(f"missing relations {sorted(want - got)}; got {sorted(map(str, got))}")
        if exp.get("exact_relations", True) and got - want:
            fails.append(f"unexpected relations {sorted(map(str, got - want))}")
    for key, have in (("environment", {e.name for e in a.environment}), ("lighting", {x.value for x in a.lighting}),
                      ("style", {x.value for x in a.style}), ("negations", {n.text for n in a.negations}),
                      ("ambiguities", {x.code for x in a.ambiguities})):
        miss = set(exp.get(key, [])) - have
        if miss:
            fails.append(f"missing {key} {sorted(miss)}; got {sorted(have)}")
    for name in exp.get("forbidden_objects", []):
        if any(o.name == name for o in a.objects):
            fails.append(f"forbidden object present: {name}")
    if exp.get("no_ambiguities") and a.ambiguities:
        fails.append(f"unexpected ambiguities {[x.code for x in a.ambiguities]}")
    return fails


def run_suite(suite: dict, split: str | None = None) -> list[dict[str, Any]]:
    results = []
    for c in suite["cases"]:
        if split and c["split"] != split:
            continue
        a = analyze_prompt(c["prompt"])
        fails = check_case(a, c["expect"])
        results.append({"id": c["id"], "category": c["category"], "split": c["split"], "prompt": c["prompt"],
                        "passed": not fails, "failures": fails})
    return results


def summarize(results: list[dict]) -> dict:
    by: dict[str, list[int]] = {}
    for r in results:
        by.setdefault(r["category"], [0, 0])
        by[r["category"]][0] += r["passed"]
        by[r["category"]][1] += 1
    return {"passed": sum(r["passed"] for r in results), "total": len(results),
            "by_category": {k: f"{v[0]}/{v[1]}" for k, v in by.items()}}
