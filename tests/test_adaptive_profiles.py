"""P6 profile schema, loading and building from benchmark result files. Numbers are SYNTHETIC test data."""
import json

import pytest

from ai_engine.adaptive import (ProfileEntry, ProfileError, build_profile_set, load_profile_set,
                                profile_set_from_dict, save_profile_set)
from tests.adaptive_helpers import FIXTURE, profile


def _entry(**kw):
    base = dict(id="x", model_id="m", precision="fp16", steps=2, resolution=512)
    base.update(kw)
    return ProfileEntry(**base)


def test_fixture_loads_and_is_labelled_synthetic():
    ps = profile()
    assert ps.synthetic is True and "SYNTHETIC" in ps.note and len(ps.entries) >= 10
    assert any(e.status == "oom" for e in ps.entries) and any(e.location == "remote" for e in ps.entries)


def test_profile_id_is_stable_and_changes_with_content(tmp_path):
    a, b = profile(), profile()
    assert a.profile_id == b.profile_id
    path = tmp_path / "p.json"
    save_profile_set(a, path)
    assert load_profile_set(path).profile_id == a.profile_id  # round trip
    d = json.loads(FIXTURE.read_text())
    d["entries"][0]["latency_ms_median"] += 1
    assert profile_set_from_dict(d).profile_id != a.profile_id


def test_synthetic_flag_is_mandatory():
    d = json.loads(FIXTURE.read_text())
    del d["synthetic"]
    with pytest.raises(ProfileError, match="synthetic"):
        profile_set_from_dict(d)


@pytest.mark.parametrize("bad", [
    dict(precision="int4"), dict(offload="disk"), dict(steps=0), dict(steps=True), dict(resolution=500),
    dict(device="tpu"), dict(status="maybe"), dict(location="moon"), dict(latency_ms_median=-1.0),
    dict(latency_ms_median=float("nan")), dict(peak_gpu_mb_max=float("inf")), dict(n_runs=-1), dict(id=""),
])
def test_entry_validation_rejects(bad):
    with pytest.raises(ProfileError):
        _entry(**bad)


def test_duplicate_ids_empty_and_wrong_schema_rejected():
    d = json.loads(FIXTURE.read_text())
    d["entries"].append(dict(d["entries"][0]))
    with pytest.raises(ProfileError, match="duplicate"):
        profile_set_from_dict(d)
    d = json.loads(FIXTURE.read_text())
    d["entries"] = []
    with pytest.raises(ProfileError):
        profile_set_from_dict(d)
    d = json.loads(FIXTURE.read_text())
    d["schema"] = "adaptive_profile/99"
    with pytest.raises(ProfileError, match="schema"):
        profile_set_from_dict(d)
    d = json.loads(FIXTURE.read_text())
    d["entries"][0]["bogus"] = 1
    with pytest.raises(ProfileError, match="bad entry"):
        profile_set_from_dict(d)


def test_unreadable_file_is_a_profile_error(tmp_path):
    with pytest.raises(ProfileError):
        load_profile_set(tmp_path / "missing.json")
    (tmp_path / "bad.json").write_text("{not json")
    with pytest.raises(ProfileError):
        load_profile_set(tmp_path / "bad.json")


# ---- building from benchmark result files (fake files shaped like p4_experiment_result/1) --------------------
def _result(exp_id, status="ok", n_ok=12, device="cuda", gpu="SYNTH GPU", model="m/x", rev="r1",
            precision="fp16", steps=2, resolution=512, lat=(800.0, 900.0), mem=(3000.0, 3100.0), clip=None):
    summary = {"n_ok": n_ok, "latency_ms": {"median": lat[0], "p95": lat[1]} if n_ok else None,
               "peak_allocated_mb": {"median": mem[0], "max": mem[1]} if n_ok else None,
               "peak_process_ram_mb": 5000.0, "clip_score": {"mean": clip} if clip else None}
    return {"schema": "p4_experiment_result/1",
            "experiment": {"id": exp_id, "config": {"precision": precision, "steps": steps, "resolution": resolution,
                                                    "attention_slicing": False, "vae_slicing": False,
                                                    "offload": "none"}},
            "environment": {"gpu_name": gpu, "gpu_total_vram_mb": 8000.0, "model_id": model, "model_revision": rev},
            "status": status, "load_info": {"device": device}, "summary": summary}


def _write(tmp_path, *results):
    for r in results:
        (tmp_path / f"{r['experiment']['id']}.json").write_text(json.dumps(r))


def test_build_keeps_measured_oom_and_skips_unproven(tmp_path):
    _write(tmp_path, _result("ok1", clip=0.29), _result("oom1", status="oom", n_ok=0, resolution=768),
           _result("few", n_ok=3), _result("cpu1", device="cpu"))
    ps, skipped = build_profile_set([tmp_path], min_runs=10)
    by = {e.id: e for e in ps.entries}
    assert set(by) == {"ok1", "oom1"} and not ps.synthetic
    assert by["ok1"].latency_ms_median == 800.0 and by["ok1"].peak_gpu_mb_max == 3100.0
    assert by["ok1"].clip_mean == 0.29 and by["oom1"].status == "oom" and by["oom1"].latency_ms_median is None
    assert {s for s, _ in skipped} == {"few.json", "cpu1.json"}
    assert ps.hardware["gpu_name"] == "SYNTH GPU" and ps.model_revision == "r1"


def test_build_refuses_mixed_machines_and_empty(tmp_path):
    _write(tmp_path, _result("a"), _result("b", gpu="OTHER GPU"))
    with pytest.raises(ProfileError, match="gpu_name"):
        build_profile_set([tmp_path])
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ProfileError, match="no usable"):
        build_profile_set([empty])
