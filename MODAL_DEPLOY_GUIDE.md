# Modal Deployment Guide for ImagineAI
# =====================================

## Step 1 — Install Modal SDK
```bash
pip install modal
modal token new
```
This opens a browser window to authenticate with your Modal account.

---

## Step 2 — (Optional) Create a secrets group in Modal dashboard
If you want API key protection on your deployed endpoint:
1. Go to https://modal.com/secrets
2. Click "New secret group"
3. Name it: `imagineai-secrets`
4. Add key: `API_KEY` = any random string you choose

---

## Step 3 — Pre-download model weights (run once)
This downloads SD-Turbo + SD 1.5 + LCM-LoRA weights (~10 GB) into a
persistent Modal volume so they survive between deployments and cold starts.

```bash
modal run modal_deploy.py
```

---

## Step 4 — Deploy the web endpoint
```bash
modal deploy modal_deploy.py
```

Modal will print something like:
```
✓ Created web endpoint: https://dilip-ravichandra--imagineai-p3-fastapi-app.modal.run
```

**That URL is your live public dashboard and API.**

---

## Step 5 — Test the deployment
```bash
# Health check
curl https://<your-app>.modal.run/api/v1/health

# Web Dashboard
open https://<your-app>.modal.run/

# API Docs
open https://<your-app>.modal.run/docs
```

---

## Step 6 — Update Android app to use the Modal URL
In android/app/src/main/java/.../api/ApiClient.kt, change:
```kotlin
private const val BASE_URL = "http://192.168.1.4:8000/"
```
to:
```kotlin
private const val BASE_URL = "https://<your-app>.modal.run/"
```

---

## GPU specs on Modal (A10G)
| Spec | Modal A10G | Your RTX 5050 |
|------|-----------|---------------|
| VRAM | 24 GB | 8 GB |
| CUDA | 12.4 | 12.8 |
| FP16 Tensor | Yes | Yes |
| SD-Turbo latency | ~180 ms | ~345 ms |

The A10G has 3× more VRAM, so all 4 models can stay resident simultaneously.

---

## Cost estimate (Modal pricing)
| Usage | Cost |
|-------|------|
| 30 GPU-hr free/month | \$0 |
| A10G on-demand | ~\$1.10/hr |
| Idle (keep_warm=0) | \$0 (auto scale-to-zero) |
| Idle (keep_warm=1) | ~\$26.40/month |

**Recommendation:** Set `keep_warm=0` after the hackathon to avoid charges.
