# Final checklist (docs/12) with evidence — `[x]` only where evidence exists in the repo

Legend: `[x]` done with evidence; `[~]` code/tests exist, not run on real data; `[ ]` not done.

## Foundation
- [ ] Repo created/protected, `main`/`develop` (no .git supplied)
- [ ] OS/toolchain versions recorded (`docs/ENVIRONMENT_REPORT.md` is a sandbox report)
- [~] API contract agreed (written, v1.0.0; **no sign-off**)
- [ ] Android skeleton builds (never built)
- [x] FastAPI skeleton starts (real `uvicorn` start + curl, and 698 tests, 2026-11-07; see `docs/SAFETY_AND_PHASE_AUDIT.md`)
- [x] Secrets and model/data files excluded (`.gitignore`; scan in `LICENSE_AND_SECRETS_AUDIT.md`)
## Baseline
- [~] Pipeline loads / API generates (code only; real SD-Turbo run NOT RUN)
- [ ] Android sends prompt and shows image
- [ ] Baseline latency/memory recorded
## Prompt and adaptation
- [x] Prompt suite (87 prompts) and parser, tested earlier (hold-out 12/20)
- [~] Dataset licence recorded (process documented; no dataset used)
- [~] Train/val split tooling (no real run)
- [ ] Meaningful adaptation trained (DL-02 open)
- [ ] Base/adapted comparison
## Optimization
- [~] Precision, steps, slicing, offload implemented; [ ] benchmarked; [ ] quality-cost comparison
## Classical CV
- [~] Resize, enhancement, edge-aware, quality assessment, artifact detection, per-stage tests (synthetic only); [ ] ablation on real output
## Adaptive controller
- [~] Monitor, quick/balanced/best, fallback, constrained-resource tests (simulated); [ ] benchmark profiles (none measured); [ ] UI explanation (no UI)
## Evaluation
- [~] CLIP protocol, latency, peak memory, model-size code; [ ] FID (not computable); [ ] ablation; [ ] failure analysis; [ ] unseen-prompt evaluation (all code-only)
## Mobile and final
- [ ] Deployment mode labelled with evidence; [ ] physical Android test; [ ] full-pipeline feasibility; [ ] hosted URL tested; [ ] clean clone test
- [x] Architecture and design docs written (`ARCHITECTURE.md`, `DESIGN_DOCUMENT.md`); [ ] reviewed by both members
- [ ] `eval_P3_TeamID.md` complete with USNs (draft skeleton only)
- [ ] Demo rehearsed; [ ] both members viva-ready
