# 7. API Contract

This is the initial agreed contract proposal. Person 1 owns the canonical schema. Freeze it before Person 2 implements the client. Version changes deliberately.

## 7.1 Generate request

`POST /api/v1/generate`

```json
{
  "prompt": "A red robot standing beside a blue submarine underwater, sunlight entering from above",
  "quality_mode": "balanced",
  "resolution": 512,
  "seed": 42
}
```

Fields:
- `prompt`: required non-empty string.
- `quality_mode`: `quick`, `balanced`, or `best`.
- `resolution`: requested target; backend may select a supported size and must report the actual size.
- `seed`: optional integer for reproducibility.

## 7.2 Successful response

```json
{
  "status": "success",
  "request_id": "generated-request-id",
  "image_url": "/outputs/generated_example.png",
  "generation": {
    "model_id": "actual-model-id-and-revision",
    "precision": "fp16",
    "scheduler": "actual-scheduler",
    "steps": 4,
    "width": 512,
    "height": 512,
    "seed": 42
  },
  "performance": {
    "model_load_seconds": null,
    "prompt_encode_seconds": null,
    "denoise_seconds": null,
    "decode_seconds": null,
    "cv_seconds": null,
    "end_to_end_seconds": 0.0,
    "peak_gpu_memory_mb": null,
    "peak_process_memory_mb": null
  },
  "quality": {
    "clip_similarity": null,
    "fid": null,
    "quality_indicators": {}
  },
  "resource_decision": {
    "fallback_used": false,
    "reason": null,
    "explanation": "Actual explanation of selected configuration"
  }
}
```

All example values are placeholders. Replace with actual measured values or `null` when unavailable. FID is generally an offline dataset-level evaluation, not a per-image metric.

## 7.3 Endpoints
- `GET /health` — service health and readiness.
- `GET /api/v1/capabilities` — supported models, resolutions, modes, and deployment type.
- `POST /api/v1/generate` — generation request.
- `GET /api/v1/jobs/{job_id}` — optional asynchronous job status if implemented.
- `GET /outputs/{filename}` — generated image retrieval, with safe path validation.

## 7.4 Error response

```json
{
  "status": "error",
  "request_id": "request-id",
  "error": {
    "code": "RESOURCE_LIMIT",
    "message": "The requested configuration exceeds available resources.",
    "retryable": true,
    "suggested_action": "Choose Quick mode or a smaller resolution."
  }
}
```

## 7.5 Contract rules
- Do not return local filesystem paths to clients.
- Use a safe URL or controlled file-serving endpoint.
- Do not expose stack traces.
- Validate prompt length, dimensions, file types and request parameters.
- Use `null` for unavailable metrics; never fabricate.
- Include actual generation configuration and fallback explanation.
- Document whether inference is local to phone, laptop-hosted, or cloud-hosted.
