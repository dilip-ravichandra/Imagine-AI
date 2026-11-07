import json

import pytest

from ai_engine.evaluation import get
from ai_engine.evaluation.dryrun import SyntheticEngine
from ai_engine.evaluation.harness import run_variant, select_eval_prompts
from ai_engine.prompt.suite import load_suite
from tests.p7_helpers import ENV_GPU, PROMPTS, Clock, GpuFakeEngine, StubClip


def test_select_prompts_defaults_to_frozen_holdout_and_is_deterministic():
    suite = load_suite()
    a, b = select_eval_prompts(suite), select_eval_prompts(suite)
    assert a == b and len(a) == 20 and {p["category"] for p in a} == {"unseen"}
    dev = select_eval_prompts(suite, "dev", per_category=1)
    assert len({p["category"] for p in dev}) == len(dev) and "unseen" not in {p["category"] for p in dev}
    assert len(select_eval_prompts(suite, "dev", limit=3)) == 3


def test_run_counts_files_and_protocol(tmp_path):
    eng, clip = GpuFakeEngine(), StubClip()
    res = run_variant(get("V0"), eng, PROMPTS, [1, 2], repeats=3, warmup=2, out_dir=tmp_path, environment=ENV_GPU,
                      clip=clip, clock=Clock(), suite_info={"split": "test"})
    assert res["status"] == "ok" and res["summary"]["n_ok"] == 4 * 2 * 3
    assert len(eng.calls) == 2 + 24  # warm-up calls are not recorded as runs
    assert len(list((tmp_path / "images" / "V0").glob("*.png"))) == 8  # one image per (prompt, seed)
    assert clip.calls == 8  # CLIP once per (prompt, seed), not per repeat
    assert (tmp_path / "V0.json").exists() and json.loads((tmp_path / "V0.json").read_text())["schema"].startswith("p7_")
    p = res["protocol"]
    assert p["seeds"] == [1, 2] and p["repeats"] == 3 and p["warmup"] == 2 and p["clip_model"] == "stub-clip"
    assert "excludes model load" in p["latency_definition"].lower()
    assert res["model_load_ms"] == 5.0 and res["synthetic"] is False
    assert res["generation_seen"]["steps"] == 4


def test_same_prompts_seeds_settings_reach_engine_for_every_variant(tmp_path):
    seen = {}
    for vid in ("V0", "V2", "V5"):
        eng = GpuFakeEngine()
        run_variant(get(vid), eng, PROMPTS[:2], [7], 1, 0, tmp_path, ENV_GPU, clock=Clock())
        seen[vid] = eng.calls
    assert [(p, s) for p, s, *_ in seen["V0"]] == [(p, s) for p, s, *_ in seen["V2"]] == [(p, s) for p, s, *_ in seen["V5"]]
    assert {c[4] for c in seen["V0"]} == {4} and {c[4] for c in seen["V2"]} == {2}  # only steps differ


def test_latency_uses_injected_clock_and_cv_is_separate(tmp_path):
    clk = Clock(step=0.010)  # every clock() call advances 10 ms
    r0 = run_variant(get("V0"), GpuFakeEngine(), PROMPTS[:1], [1], 1, 0, tmp_path, ENV_GPU, clock=clk)
    run0 = r0["runs"][0]
    assert run0["generation_ms"] == pytest.approx(10.0) and run0["cv_ms"] == 0.0
    assert run0["end_to_end_ms"] == pytest.approx(10.0)
    r5 = run_variant(get("V5"), GpuFakeEngine(), PROMPTS[:1], [1], 1, 0, tmp_path, ENV_GPU, clock=Clock(0.010))
    run5 = r5["runs"][0]
    assert run5["cv_ms"] == pytest.approx(10.0)
    assert run5["end_to_end_ms"] == pytest.approx(run5["generation_ms"] + run5["cv_ms"])


def test_cv_variant_records_raw_and_processed_and_clip_for_both(tmp_path):
    res = run_variant(get("V5"), GpuFakeEngine(), PROMPTS[:2], [1], 1, 0, tmp_path, ENV_GPU, clip=StubClip(),
                      clock=Clock())
    x = res["runs"][0]
    assert x["clip_score"] is not None and x["clip_score_raw"] is not None
    assert x["cv_applied"] in (True, False) and "cv_pixel_fidelity_vs_raw" in x
    assert (tmp_path / "images" / "V5_raw").is_dir()
    assert res["summary"]["cv_applied_fraction"] in (0.0, 0.5, 1.0)


def test_no_clip_leaves_scores_null_never_invented(tmp_path):
    res = run_variant(get("V0"), GpuFakeEngine(), PROMPTS[:1], [1], 1, 0, tmp_path, ENV_GPU, clock=Clock())
    assert all(r.get("clip_score") is None for r in res["runs"]) and res["summary"]["clip_score"] is None
    assert res["summary"]["peak_gpu_mb"]["median"] == 1000.0  # engine-reported value passes through unchanged


def test_oom_is_a_recorded_result_and_stops(tmp_path):
    res = run_variant(get("V0"), GpuFakeEngine(raise_on=3), PROMPTS, [1], 2, 0, tmp_path, ENV_GPU, clock=Clock())
    assert res["status"] == "oom" and "out of memory" in res["error"].lower()
    assert res["summary"]["n_ok"] == 2 and res["summary"]["n_failed"] == 1
    assert (tmp_path / "V0.json").exists()


def test_warmup_failure_is_recorded(tmp_path):
    res = run_variant(get("V0"), GpuFakeEngine(raise_on=1), PROMPTS, [1], 1, 1, tmp_path, ENV_GPU, clock=Clock())
    assert res["status"] == "oom" and res["runs"] == []


def test_blocked_and_invalid_inputs_refused(tmp_path):
    with pytest.raises(ValueError, match="blocked"):
        run_variant(get("V6"), GpuFakeEngine(), PROMPTS, [1], 1, 0, tmp_path, ENV_GPU)
    with pytest.raises(ValueError):
        run_variant(get("V0"), GpuFakeEngine(), [], [1], 1, 0, tmp_path, ENV_GPU)
    with pytest.raises(ValueError):
        run_variant(get("V0"), GpuFakeEngine(), PROMPTS, [1], 0, 0, tmp_path, ENV_GPU)


def test_synthetic_engine_is_flagged_and_deterministic(tmp_path):
    res = run_variant(get("V0"), SyntheticEngine(), PROMPTS[:1], [1], 1, 0, tmp_path, {"synthetic": True},
                      clock=Clock())
    assert res["synthetic"] is True
    a, b = SyntheticEngine().generate("p", 1, 32, 32, 4), SyntheticEngine().generate("p", 1, 32, 32, 4)
    assert list(a.image.getdata()) == list(b.image.getdata())
