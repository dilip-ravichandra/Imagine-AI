# Viva preparation — topics (docs/10 section 10.3) and where the answer is in the repo

| Topic | Be able to explain | Repo pointer | Honest gap |
|---|---|---|---|
| Diffusion + text conditioning | tokenize, encode, latent noise by seed, denoise, VAE decode | `docs/03_SYSTEM_ARCHITECTURE.md`, `services/engine.py` | — |
| Why SD-Turbo | few-step distilled model fits ~8 GB | `docs/11_RISKS_AND_DECISIONS.md` | not compared with other models |
| What was adapted | LoRA plan, data prep, approval gate | `docs/ADAPTATION.md` | **no adapter trained** |
| Optimization strategies | precision, slicing, offload, steps; trade-offs | `docs/P4_OPTIMIZATION.md` | no measured results |
| Five CV modules | resize, enhancement, edge-aware, quality, artifacts | `docs/P5A_CV.md`, `docs/P5B_CV.md` | synthetic only; thresholds provisional |
| Controller | inputs, ranking, fallback ladder, OOM retry | `docs/P6_ADAPTIVE.md` | no measured profile, defaults uncalibrated |
| CLIP vs FID | CLIP = prompt alignment, FID = distribution distance, needs large sample | `docs/P7A_EVAL.md`, `ai_engine/evaluation/metrics.py` | FID not computable here |
| Latency/memory method | warm-up, repeats, median/p95, peak GPU | `ai_engine/evaluation/harness.py` | none run |
| Deployment choice | on-device vs hybrid vs cloud | `docs/09_MOBILE_DEPLOYMENT.md` | Android not built |
| A real failure case | one from human review | `evaluation/reports/failure_analysis.md` | does not exist yet |

Both members: high-level whole system + own modules in depth (Person 1: backend/ai_engine/CV/evaluation; Person 2: android).
