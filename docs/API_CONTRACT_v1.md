# Imagine AI API Contract — v1.0.0 (FROZEN)
Source of truth in code: `backend/app/schemas/v1.py`. Changes need a version bump, a note here, and agreement of both developers.

## GET /health -> 200 `{"status":"ok","api_version":"1.0.0"}`
## GET /api/v1/capabilities -> 200
`{api_version, quality_modes:["quick","balanced","best"], min_resolution:256, max_resolution:1024, generation_available:bool, deployment_mode:"hybrid/cloud"}`

## POST /api/v1/generate
Request: `{"prompt":"A red robot beside a blue submarine underwater","quality_mode":"balanced","resolution":512,"seed":42}`
- prompt: 1-500 chars; quality_mode: quick|balanced|best (default balanced); resolution: 256-1024 (default 512); seed: optional int 0..2^32-1.

Success 200: `status:"success"`, `request_id`, `image_url` (URL only, never a file path),
`generation{model,model_revision,precision,scheduler,steps,width,height,seed}`,
`performance{model_load_ms,prompt_encode_ms,denoise_ms,decode_ms,cv_ms,end_to_end_ms,peak_gpu_mb,peak_process_ram_mb}` (null if unavailable),
`quality{clip_score,sharpness,brightness,contrast,artifact_flags}` (null if unavailable; FID is offline),
`resource_decision{fallback_used,reason,explanation}`.

Error: `{"status":"error","request_id":?, "error":{"code","message","retryable","suggested_action"}}`
Codes: INVALID_REQUEST (422), NOT_IMPLEMENTED (501, P0 only), RESOURCE_EXHAUSTED, INTERNAL_ERROR (500). No paths/stack traces.

Deployment label: "hybrid/cloud" while inference is server-side. Never "on-device" unless the full pipeline runs on the phone.

## P1A clarifications (no schema change; version stays 1.0.0 — both developers must confirm)
- `POST /api/v1/generate` now returns 200 with a real image when the model is available. `NOT_IMPLEMENTED` is retired (never emitted by P1A).
- `image_url` = `<server base URL>/images/<request_id>.png` (request_id is 32 hex chars). Base URL comes from the request Host header, or `PUBLIC_BASE_URL` if set. Images are PNG, served over HTTP, never a path; the server keeps only the newest `MAX_STORED_IMAGES`.
- `GET /api/v1/capabilities`: `min_resolution`/`max_resolution` now report the server's *supported* range (default 256–768, native 512), and `generation_available` is false if ML dependencies are missing.
- Request validation unchanged (256–1024). A resolution that passes the schema but is not in the server's supported set (default 256,384,512,640,768) -> 422 `INVALID_REQUEST`, with the allowed values in `suggested_action`.
- Error mapping: busy (another generation/load in progress) -> 429 `RESOURCE_EXHAUSTED`, retryable; out of memory -> 503 `RESOURCE_EXHAUSTED`, retryable; model failed to load -> 500 `INTERNAL_ERROR`, retryable; ML dependencies missing -> 503 `INTERNAL_ERROR`, not retryable. Every error body from the generate endpoint carries `request_id` except schema-validation 422s.
- `performance`: `end_to_end_ms` = encode+denoise+decode+PNG save, **excluding** model load. `model_load_ms` is non-null only on the request that triggered the load. `peak_gpu_mb` = PyTorch peak allocated (CUDA only). `peak_process_ram_mb` = peak of the whole server process since start (includes model load). `prompt_encode_ms`, `denoise_ms`, `decode_ms`, `cv_ms` are null (not measured yet). `quality` is null.
- First request can take long if the model is not preloaded: Android HTTP read timeout should be generous (>= 120 s) until measured.
- Quality-mode -> steps (quick 1, balanced 2, best 4) is a provisional mapping, not benchmarked.

## P2 additions (additive; version stays 1.0.0 — both developers must confirm)
- **New** `POST /api/v1/prompt/analysis` — body `{"prompt": "<1-500 chars, not blank>"}` -> 200 with the `PromptAnalysis` JSON (schema: `docs/prompt_analysis_schema_v1.json`, rules: `docs/PROMPT_PARSER.md`). 422 `INVALID_REQUEST` for empty, blank, >500 chars or wrong type. CPU only; never touches the model.
- **Tightened validation** (`POST /api/v1/generate`): a whitespace-only `prompt` now returns 422 `INVALID_REQUEST` (previously accepted because length >= 1). Non-blank prompts are passed to the model exactly as sent (no trimming).
- `GenerateResponse` is **unchanged**: it carries no prompt analysis. Android needs no change.

## P4 (inference optimization) — no API change
Schema, endpoints and error codes are unchanged; version stays 1.0.0. New server-side env settings only (`PRECISION`, `ATTENTION_SLICING`, `VAE_SLICING`, `OFFLOAD`, `WEIGHTS_VARIANT`; see `docs/P4_OPTIMIZATION.md`). `generation.precision` reports the precision actually used. Quality-mode -> steps is still the provisional P1A mapping.

## P5A / P5B note
No schema change. With `CV_MODE=off` (default) `quality` and `performance.cv_ms` are null. With `CV_MODE=assess|correct` the server fills `quality` (`sharpness` = Laplacian variance, unbounded; `brightness`/`contrast` = luma mean/std in 0..1; `artifact_flags` = list of strings; `clip_score` null) and `performance.cv_ms`. `artifact_flags` may contain `semantic_review_recommended` (prompt-derived risk, not an image detection). In `correct` mode the served image is the corrected one. See `docs/P5B_CV.md`.
## P6 note (no schema change; version stays 1.0.0 — both developers must confirm)
With `ADAPTIVE_PROFILE` set, `resource_decision` carries the controller's result (`fallback_used`, a stable `reason` code such as `RESOLUTION_REDUCED_FOR_RESOURCES` / `OOM_DURING_GENERATION`, and the explanation); `generation.width/height/steps` report what was actually used (resolution may be lower than requested). If no profiled configuration is safe: 503 `RESOURCE_EXHAUSTED`, retryable, with a suggested action. Without `ADAPTIVE_PROFILE` nothing changes.

## P5A note
No API change. The CV modules (`computer_vision/`) are not called by `/generate` yet, so `performance.cv_ms` and `quality` stay null until P5B wires the pipeline.
## P3B additions (additive; version stays 1.0.0 — both developers must confirm)
- **New** `GET /api/v1/model` -> 200 `{api_version, model, model_revision (configured pin or null), loaded, adapter{configured, active, reason, adapter_sha256, adapter_bytes, base_revision}}`. No paths, no GPU work. Before the model loads it reports the *pre-load verdict* ("Approved adapter will be applied…" or "Adapter will not be used: <reason>"); after load, the actual state.
- **Behaviour, not schema:** when an approved adapter is active, `generation.model_revision` becomes `<pinned-revision>+lora-<first 12 hex of adapter sha256>`. Same string field, so Android needs no change; it simply shows which weights made the image. With no adapter (the default) it is unchanged.
- `GET /api/v1/capabilities` and `POST /api/v1/generate` request/response **schemas are unchanged** (a test asserts the exact key sets).
- Env: `ADAPTER_PATH` (optional folder). Used only if approved (see `docs/ADAPTATION.md`) **and** `MODEL_REVISION` equals the adapter's base revision; otherwise the base model is served and the reason is logged at startup and shown by `/api/v1/model`. An adapter problem never fails a request or crashes the server.

## Safety addition — optional API key (additive; version stays 1.0.0 — both developers must confirm)
If the server sets `API_KEY`, every `/api/v1/*` request must carry `X-API-Key: <key>`; otherwise **401** `{"status":"error","error":{"code":"UNAUTHORIZED","message":"A valid API key is required.","retryable":false,"suggested_action":"Send the server's API key in the X-API-Key header."}}`. The check runs before body validation and before any generation. `/health` and `/images/*` are not protected (image ids are unguessable). When `API_KEY` is unset (default) nothing changes. Android: read the key from build config / local properties, never commit it; this is a shared secret, not user authentication.
