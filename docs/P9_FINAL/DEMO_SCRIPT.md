# 3-minute demo script (from docs/10 section 10.2)

**Cannot be rehearsed yet**: no real generation, no Android UI, no hosted URL exist. Fill the TODOs after P8.

Rules: use **new unseen prompts** (the frozen 20 hold-out prompts are seen). Say aloud which deployment mode you are in. Never present backup/recorded output as live.

| Time | Step | What to show | Source / TODO |
|---|---|---|---|
| 0:00-0:25 | Problem + product | Imagine AI, resource limits | `docs/01_PROJECT_CHARTER.md` |
| 0:25-1:05 | Live unseen prompt | Complex prompt with multiple objects + a spatial relation; show `/api/v1/prompt/analysis` output | TODO(team) write 3 new prompts, none from `prompt_suite_v1.json` |
| 1:05-1:40 | Generation | Model, revision, resolution, precision, steps, `resource_decision.explanation` | needs a real profile; if still synthetic, say so |
| 1:40-2:10 | CV + quality | `quality` flags; before/after of `CV_MODE=correct` | only if CV was run on real output |
| 2:10-2:40 | Evidence | Baseline vs optimized latency/memory/CLIP from `evaluation/reports/p7_report.md` | **does not exist yet**; do not show synthetic numbers as results |
| 2:40-3:00 | Mobile + limits | Phone UI; state "hybrid: phone to laptop server" (or cloud if hosted); name one failure case | needs P8; one failure from `p7_human_review.csv` |

Backup: pre-record a run, label it "recording"; keep a cached PNG; test phone-to-laptop Wi-Fi (`http://<LAN-IP>:8000`, firewall allowed) beforehand. Pre-load the model (`PRELOAD_MODEL=true`).
