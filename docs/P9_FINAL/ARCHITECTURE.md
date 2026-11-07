# Architecture (as implemented in this repo)

Deployment label today: **hybrid / laptop-hosted backend** at most. Nothing runs on the phone. No cloud host exists. Do not present generation as "on-device".

```mermaid
flowchart TD
    A[Android app - skeleton only, no network layer yet] -.planned.-> B
    B[FastAPI backend/app/main.py] --> V[Pydantic validation schemas/v1.py]
    V --> G[services/generation.py]
    G --> PA[Prompt analysis ai_engine/prompt - deterministic parser]
    G --> AC{ADAPTIVE_PROFILE set?}
    AC -- yes --> CT[ai_engine/adaptive controller + fallback executor]
    AC -- no --> FX[Fixed steps quick 1 / balanced 2 / best 4]
    CT --> EN
    FX --> EN
    EN[services/engine.py - SD-Turbo via diffusers] --> LO[Optional approved LoRA adapter, gated]
    EN --> CVH{CV_MODE}
    CVH -- off --> ST
    CVH -- assess/correct --> CV[computer_vision/pipeline: resize, enhance, edge-aware, quality, artifacts]
    CV --> ST[services/storage.py - PNG + URL]
    ST --> R[GenerateResponse + resource_decision + quality + performance]
    RM[SystemMonitor torch.cuda + psutil] --> CT
    PF[Measured profile JSON - none exists yet] --> CT
    EV[evaluation/ P4 benchmarks, P7 harness, P7B report] --> EN
```

## Endpoints (API v1.0.0, not yet signed off by both developers)
`GET /health`, `GET /api/v1/capabilities`, `GET /api/v1/model`, `POST /api/v1/generate`, `POST /api/v1/prompt/analysis`.

## Order of operations in `generate()`
controller (or fixed steps) -> engine -> optional CV hook -> save once -> response. Hand-merged during the combined-tree merge (`MERGE_NOTES.md` section 2); exercised only with fakes.

## Opt-in switches (all default to the P1A baseline)
`PRECISION, ATTENTION_SLICING, VAE_SLICING, OFFLOAD, WEIGHTS_VARIANT` (P4); `CV_MODE=off|assess|correct` (P5B); `ADAPTIVE_PROFILE/POLICY/ALLOW_SYNTHETIC/DECISION_LOG` (P6); `ADAPTER_PATH` (P3B); `MODEL_REVISION`, `PRELOAD_MODEL`.
