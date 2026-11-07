import json

import pytest

from ai_engine.training.data import (DataError, Exclusions, assert_no_leakage, build_manifest, caption_level,
                                     clean_caption, load_coco, load_exclusions, norm_caption, select_pairs,
                                     split_rows, write_imagefolder)
from tests.coco_fixture import PLAIN, RICH, make_coco, make_eval


def run_select(tmp_path, n=20, seed=1, eval_entries=None, **kw):
    ann, img_dir, _ = make_coco(tmp_path)
    ev = load_exclusions([make_eval(tmp_path, eval_entries or [{"prompt": "nothing relevant here at all"}])])
    images, caps, lic, sha = load_coco(ann)
    rows, stats = select_pairs(images, caps, lic, img_dir, ev, n_total=n, seed=seed, **kw)
    return rows, stats, ev, (ann, sha)


# ---- captions
def test_clean_caption_rules():
    assert clean_caption("  A   red\n cup   on a table. ") == "A red cup on a table."
    assert clean_caption("two words") is None  # too short
    assert clean_caption("word " * 51) is None  # too long
    assert clean_caption("a caf\u00e9 table with a cup") is None  # non-ascii
    assert clean_caption(None) is None and clean_caption(5) is None


def test_parser_levels_used_for_stratification_are_as_expected():
    assert all(caption_level(c) in ("moderate", "complex") for c in RICH)
    assert all(caption_level(c) == "simple" for c in PLAIN)


# ---- COCO loading
def test_load_coco_reads_licences_and_hash(tmp_path):
    ann, _, _ = make_coco(tmp_path)
    images, caps, lic, sha = load_coco(ann)
    assert lic[4] == "Attribution License" and len(sha) == 64
    assert len(images) == 40 and all(len(v) == 2 for v in caps.values())


def test_load_coco_rejects_non_coco(tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"hello": 1}))
    with pytest.raises(DataError):
        load_coco(p)
    with pytest.raises(DataError):
        load_coco(tmp_path / "missing.json")


# ---- leakage guard
def test_excluded_image_id_removes_all_its_captions(tmp_path):
    # image 1000 is rich; exclude it by id only, with a caption that matches nothing
    rows, stats, _, _ = run_select(tmp_path, n=30, eval_entries=[{"source_image_id": "1000", "prompt": "zzz qqq www xxx"}])
    assert 1000 not in {r["image_id"] for r in rows}
    assert stats["rejects"]["excluded_image_id"] == 1


def test_excluded_filename_and_caption_both_block(tmp_path):
    rows, stats, _, _ = run_select(tmp_path, n=30, eval_entries=[
        {"source_filename": "COCO_train2014_000000001001.jpg", "prompt": "zzz qqq www xxx"}])
    assert 1001 not in {r["image_id"] for r in rows}
    # caption match (case/punctuation-insensitive) excludes the image even with a different id
    rows2, stats2, _, _ = run_select(tmp_path / "b", n=30, eval_entries=[{"prompt": "a LARGE green apple!"}])
    assert all("large green apple" not in norm_caption(r["caption"]) for r in rows2)
    assert stats2["rejects"].get("excluded_caption", 0) >= 1


def test_assert_no_leakage_catches_a_planted_row(tmp_path):
    rows, _, ev, _ = run_select(tmp_path, n=10)
    assert_no_leakage(rows, ev)  # clean
    planted = dict(rows[0], caption="nothing relevant here at all")
    with pytest.raises(DataError, match="leakage"):
        assert_no_leakage([planted], ev)


def test_dataset_is_scoped_ids_do_not_cross_datasets(tmp_path):
    ann, img_dir, _ = make_coco(tmp_path)
    ev = load_exclusions([make_eval(tmp_path, [{"dataset": "Flickr30K", "source_image_id": "1000", "prompt": "q w e r t"}])])
    images, caps, lic, _ = load_coco(ann)
    rows, _ = select_pairs(images, caps, lic, img_dir, ev, n_total=40, seed=1)
    assert 1000 in {r["image_id"] for r in rows}  # a Flickr id must not block a COCO image


def test_exclusions_require_a_real_file(tmp_path):
    with pytest.raises(DataError):
        load_exclusions([tmp_path / "nope.json"])
    with pytest.raises(DataError):
        load_exclusions([])


# ---- selection behaviour
def test_selection_is_deterministic_and_seed_sensitive(tmp_path):
    a, _, _, _ = run_select(tmp_path / "1", n=16, seed=5)
    b, _, _, _ = run_select(tmp_path / "2", n=16, seed=5)
    c, _, _, _ = run_select(tmp_path / "3", n=16, seed=6)
    key = lambda rows: [(r["image_id"], r["caption_id"]) for r in rows]
    assert key(a) == key(b) and key(a) != key(c)


def test_one_caption_per_image_and_cleaned(tmp_path):
    rows, _, _, _ = run_select(tmp_path, n=30)
    assert len({r["image_id"] for r in rows}) == len(rows)
    assert all(r["caption"] == r["caption"].strip() and "\n" not in r["caption"] for r in rows)


def test_complex_fraction_controls_mix(tmp_path):
    rows, stats, _, _ = run_select(tmp_path, n=20, complex_fraction=0.5)
    assert stats["rich_selected"] == 10 and stats["plain_selected"] == 10
    rows, stats, _, _ = run_select(tmp_path / "all", n=10, complex_fraction=1.0)
    assert stats["plain_selected"] == 0 and all(r["level"] in ("moderate", "complex") for r in rows)


def test_stratum_shortfall_is_topped_up_and_reported(tmp_path):
    # only 20 rich images exist; ask for 36 at 100% rich -> 16 must come from plain
    rows, stats, _, _ = run_select(tmp_path, n=36, complex_fraction=1.0)
    assert stats["selected"] == 36 and stats["rich_selected"] == 20 and stats["plain_selected"] == 16


def test_true_shortfall_is_reported_not_hidden(tmp_path):
    _, stats, _, _ = run_select(tmp_path, n=60)
    assert stats["selected"] == 40 and stats["shortfall"] == 20


def test_licence_filter_and_labels(tmp_path):
    rows, stats, _, _ = run_select(tmp_path, n=10, license_ids={4})
    assert all(r["license"] == "Attribution License" for r in rows)
    assert stats["rejects"]["licence_not_allowed"] == 20


def test_small_missing_and_corrupt_images_are_rejected_and_counted(tmp_path):
    ann, img_dir, rows0 = make_coco(tmp_path)
    (img_dir / rows0[0][1]).unlink()  # missing
    (img_dir / rows0[1][1]).write_bytes(b"not an image")  # corrupt
    ev = load_exclusions([make_eval(tmp_path, [{"prompt": "nothing relevant here at all"}])])
    images, caps, lic, _ = load_coco(ann)
    rows, stats = select_pairs(images, caps, lic, img_dir, ev, n_total=40, seed=1)
    assert stats["rejects"]["image_file_missing"] == 1 and stats["rejects"]["unreadable"] == 1
    assert stats["selected"] == 38
    rows, stats = select_pairs(images, caps, lic, img_dir, ev, n_total=10, seed=1, min_side=500)
    assert stats["selected"] == 0 and stats["rejects"]["too_small"] > 0


def test_identical_image_bytes_are_not_selected_twice(tmp_path):
    ann, img_dir, rows0 = make_coco(tmp_path)
    (img_dir / rows0[3][1]).write_bytes((img_dir / rows0[2][1]).read_bytes())
    ev = load_exclusions([make_eval(tmp_path, [{"prompt": "nothing relevant here at all"}])])
    images, caps, lic, _ = load_coco(ann)
    rows, stats = select_pairs(images, caps, lic, img_dir, ev, n_total=40, seed=1)
    assert len({r["sha256"] for r in rows}) == len(rows)
    assert stats["rejects"]["duplicate_image_bytes"] == 1


def test_bad_arguments(tmp_path):
    ann, img_dir, _ = make_coco(tmp_path)
    ev = load_exclusions([make_eval(tmp_path, [{"prompt": "x y z w v"}])])
    images, caps, lic, _ = load_coco(ann)
    for kw in (dict(n_total=1), dict(n_total=10, complex_fraction=1.5)):
        with pytest.raises(DataError):
            select_pairs(images, caps, lic, img_dir, ev, seed=1, **kw)


# ---- split
def test_split_is_disjoint_deterministic_and_sized(tmp_path):
    rows, _, _, _ = run_select(tmp_path, n=20)
    tr, va = split_rows(rows, 5, seed=3)
    tr2, va2 = split_rows(rows, 5, seed=3)
    assert len(tr) == 15 and len(va) == 5 and [r["image_id"] for r in va] == [r["image_id"] for r in va2]
    assert not {r["image_id"] for r in tr} & {r["image_id"] for r in va}
    for bad in (0, 20, 25):
        with pytest.raises(DataError):
            split_rows(rows, bad, seed=3)


# ---- output
def test_imagefolder_output_manifest_and_no_overwrite(tmp_path):
    rows, stats, ev, (ann, sha) = run_select(tmp_path, n=20)
    tr, va = split_rows(rows, 4, seed=1)
    man = build_manifest(params={"seed": 1}, annotations_path=ann, annotations_sha=sha, exclusions=ev,
                         stats=stats, train=tr, val=va)
    out = tmp_path / "ds"
    write_imagefolder(out, tr, va, man)
    meta = [json.loads(x) for x in (out / "train" / "metadata.jsonl").read_text().splitlines()]
    assert len(meta) == 16 and all((out / "train" / m["file_name"]).is_file() and m["text"] for m in meta)
    assert len(list((out / "validation").glob("*.jpg"))) == 4
    m = json.loads((out / "manifest.json").read_text())
    assert m["schema"] == "p3a-dataset-1" and m["counts"]["train"] == 16 and m["counts"]["validation"] == 4
    assert m["source"]["annotations_sha256"] == sha and m["leakage_guard"]["captions_checked"] >= 1
    assert sum(m["licences"].values()) == 20 and m["limitations"]
    assert all("path" not in r for r in m["train"] + m["validation"])  # no local absolute paths in the manifest
    assert str(tmp_path) not in (out / "manifest.json").read_text()
    with pytest.raises(DataError):
        write_imagefolder(out, tr, va, man)
