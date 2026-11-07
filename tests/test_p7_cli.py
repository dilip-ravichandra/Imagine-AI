import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation" / "scripts"))

import analyze_p7_results as analyze  # noqa: E402
import run_p7_eval as runner  # noqa: E402


def test_list_shows_blocked(capsys):
    assert runner.main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "V6" in out and "BLOCKED" in out and "COMBINED" in out


def test_nothing_to_do_returns_2(capsys):
    assert runner.main([]) == 2


def test_dry_run_end_to_end_is_flagged_and_gate_fails(tmp_path, capsys):
    res, rep = tmp_path / "res", tmp_path / "rep"
    rc = runner.main(["--only", "V0", "--only", "V2", "--only", "V6", "--dry-run", "--split", "dev", "--limit", "3",
                      "--seeds", "1,2", "--repeats", "2", "--warmup", "1", "--out", str(res)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SKIPPED" in out and "synthetic=True" in out
    d = json.loads((res / "V0.json").read_text())
    assert d["synthetic"] is True and d["protocol"]["suite"]["subset"] is True
    assert not (res / "V6.json").exists()
    rc = analyze.main(["--results", str(res), "--out-dir", str(rep)])
    assert rc == 1  # a dry run can never satisfy the gate
    md = (rep / "p7_report.md").read_text()
    assert "NOT MET" in md and "SYNTHETIC" in md
    assert (rep / "p7_runs.csv").exists() and (rep / "p7_failure_cases_TEMPLATE.md").exists()


def test_unpinned_real_run_is_refused(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("MODEL_REVISION", raising=False)
    rc = runner.main(["--only", "V0", "--out", str(tmp_path)])
    assert rc == 2 and "MODEL_REVISION" in capsys.readouterr().out
