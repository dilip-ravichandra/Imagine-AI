def test_root_serves_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Imagine AI" in r.text
    assert "Model comparison" in r.text


def test_dashboard_alias(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_static_assets(client):
    r_css = client.get("/static/styles.css")
    assert r_css.status_code == 200
    assert "var(--bg-main)" in r_css.text

    r_js = client.get("/static/app.js")
    assert r_js.status_code == 200
    assert "initModelComparisonChart" in r_js.text


def test_metrics_summary(client):
    r = client.get("/api/v1/metrics/summary")
    assert r.status_code == 200
    data = r.json()
    assert "summary_cards" in data
    assert data["summary_cards"]["best_clip_alignment"] == 0.333
    assert data["summary_cards"]["inference_speedup_x"] == 3.01


def test_sd15_comparison(client):
    r = client.get("/api/v1/models/sd15-comparison")
    assert r.status_code == 200
    data = r.json()
    assert "baseline" in data
    assert "adapted" in data
    assert "optimized" in data
    assert "sd_turbo" in data
    assert data["baseline"]["steps"] == 30
    assert data["optimized"]["steps"] == 8
    assert data["optimized"]["precision"] == "fp16"
