"""Synthetic COCO-format fixture: real image files, real JSON layout, parser-verified caption levels."""
import json
from pathlib import Path

from PIL import Image

RICH = ["A red cup beside a blue plate on a wooden table",
        "Two cats sitting on a sofa next to a lamp",
        "A blue bicycle leaning against a white wall"]
PLAIN = ["A large green apple", "A tall glass vase", "A bowl of fresh fruit", "The big yellow bus"]
LICENCES = [{"id": 1, "name": "Attribution-NonCommercial-ShareAlike License"},
            {"id": 4, "name": "Attribution License"}]


def make_coco(tmp: Path, n: int = 40, size=(400, 400), licence_cycle=(1, 4)):
    """n images alternating rich/plain captions. Returns (ann_path, images_dir, rows)."""
    img_dir = tmp / "train2014"
    img_dir.mkdir(parents=True, exist_ok=True)
    images, anns, rows = [], [], []
    for i in range(n):
        iid = 1000 + i
        fname = f"COCO_train2014_{iid:012d}.jpg"
        Image.new("RGB", size, ((i * 37) % 256, (i * 91) % 256, (i * 53) % 256)).save(img_dir / fname, quality=95)
        # unique pixel so no two files are byte-identical even if colours collide
        im = Image.open(img_dir / fname).convert("RGB")
        im.putpixel((0, 0), (i % 256, (i // 256) % 256, 7))
        im.save(img_dir / fname, quality=95)
        lic = licence_cycle[i % len(licence_cycle)]
        images.append({"id": iid, "file_name": fname, "width": size[0], "height": size[1], "license": lic})
        pool = RICH if i % 2 == 0 else PLAIN
        caps = [pool[i % len(pool)], pool[(i + 1) % len(pool)]]
        for j, c in enumerate(caps):
            anns.append({"id": iid * 10 + j, "image_id": iid, "caption": c + ".\n"})
        rows.append((iid, fname, caps))
    ann = tmp / "captions_train2014.json"
    ann.write_text(json.dumps({"images": images, "annotations": anns, "licenses": LICENCES}))
    return ann, img_dir, rows


def make_eval(tmp: Path, entries):
    """entries: list of dicts with any of source_image_id/source_filename/prompt/split/dataset/id."""
    rows = []
    for k, e in enumerate(entries):
        rows.append({"id": f"E{k}", "dataset": "COCO", "split": "test", **e})
    p = tmp / "eval.json"
    p.write_text(json.dumps(rows))
    return p
