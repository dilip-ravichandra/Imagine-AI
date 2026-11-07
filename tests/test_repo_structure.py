import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
DIRS = ["android", "backend/app/api", "backend/app/schemas", "backend/app/services",
        "ai_engine/prompt", "ai_engine/models", "ai_engine/optimization", "ai_engine/adaptive",
        "ai_engine/training", "computer_vision/resize", "computer_vision/enhancement",
        "computer_vision/edge_aware", "computer_vision/quality", "computer_vision/artifacts",
        "evaluation/prompts", "evaluation/scripts", "evaluation/results", "evaluation/reports",
        "tests", "docs", "ai_handoff"]


def test_tree():
    for d in DIRS:
        assert (ROOT / d).is_dir(), d
    for f in [".gitignore", ".env.example", "README.md"]:
        assert (ROOT / f).is_file(), f


def test_no_binaries_or_secrets():
    bad = {".safetensors", ".ckpt", ".pt", ".pth", ".onnx", ".apk"}
    for p in ROOT.rglob("*"):
        assert p.suffix not in bad, p
    assert not (ROOT / ".env").exists()
