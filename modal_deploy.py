"""
ImagineAI — Modal Labs Deployment Script
=========================================
Deploys the full FastAPI backend with SD-Turbo on a Modal A10G GPU.

Setup (run once):
    pip install modal
    modal token new          # authenticate with your Modal account

Deploy:
    modal deploy modal_deploy.py

The public URL printed after deploy is the base URL for:
  - Web Dashboard : https://<your-app>.modal.run/
  - API Docs      : https://<your-app>.modal.run/docs
  - Android Client: set SERVER_URL = "https://<your-app>.modal.run"
"""

import modal

# ---------------------------------------------------------------------------
# 1. Container Image
#    We build one Docker-style image: CUDA 12.4 + PyTorch 2.3 + all our deps.
# ---------------------------------------------------------------------------

cuda_version = "12.4.0"
flavor = "devel"
os_ver = "ubuntu22.04"
tag = f"{cuda_version}-{flavor}-{os_ver}"

imagine_image = (
    modal.Image.from_registry(f"nvidia/cuda:{tag}", add_python="3.12")
    # System packages
    .apt_install("git", "libgl1", "libglib2.0-0")
    # Base Python deps
    .pip_install(
        "fastapi>=0.110",
        "pydantic>=2.5",
        "uvicorn>=0.27",
        "httpx>=0.27",
        "pillow>=10.0",
        "psutil>=5.9",
        "numpy>=1.26",
        "opencv-python-headless>=4.9",
        "matplotlib>=3.8",
    )
    # ML / GPU deps — install torch CUDA build first, then diffusers stack
    .pip_install(
        "torch>=2.3",
        "torchvision>=0.18",
        extra_index_url="https://download.pytorch.org/whl/cu124",
    )
    .pip_install(
        "diffusers>=0.30",
        "transformers>=4.40",
        "accelerate>=0.30",
        "safetensors>=0.4",
        "peft>=0.11",
    )
)

# ---------------------------------------------------------------------------
# 2. Modal App & GPU Config
# ---------------------------------------------------------------------------

app = modal.App("imagineai-p3", image=imagine_image)

# Persistent volume to cache the downloaded HuggingFace model weights (~7 GB).
# Without this, each cold-start would re-download everything.
model_volume = modal.Volume.from_name("imagineai-model-cache", create_if_missing=True)
MODEL_CACHE_DIR = "/root/.cache/huggingface"

# ---------------------------------------------------------------------------
# 3. Model Pre-Download (runs once at build time, stored in the volume)
# ---------------------------------------------------------------------------

@app.function(
    gpu="A10G",
    volumes={MODEL_CACHE_DIR: model_volume},
    timeout=1800,  # 30 min for first-time downloads
    secrets=[modal.Secret.from_name("imagineai-secrets")],
)
def download_models():
    """Pre-warms the model cache volume with SD-Turbo and SD 1.5 weights."""
    from diffusers import AutoPipelineForText2Image, StableDiffusionPipeline
    import torch

    print("Downloading SD-Turbo (fp16)...")
    AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
    )

    print("Downloading SD 1.5 (fp32 for Baseline/Adapted)...")
    StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float32,
    )

    print("Downloading LCM-LoRA weights...")
    StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
    )
    from diffusers import DiffusionPipeline
    pipe = DiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
    )
    pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")

    model_volume.commit()
    print("All model weights cached to volume.")


# ---------------------------------------------------------------------------
# 4. ASGI FastAPI App (served as a Modal web endpoint)
# ---------------------------------------------------------------------------

@app.function(
    gpu="A10G",
    # Keep one container warm to avoid cold-start on the first request.
    # Set to 0 for pure pay-per-use (slower first request).
    keep_warm=1,
    volumes={MODEL_CACHE_DIR: model_volume},
    timeout=300,
    # Allow extra time for model loading on cold start
    container_idle_timeout=120,
    secrets=[modal.Secret.from_name("imagineai-secrets")],
    # Mount the full project source into the container
    mounts=[
        modal.Mount.from_local_dir(
            ".",
            remote_path="/app",
            # Exclude large local artifacts that don't belong in the cloud
            condition=lambda path: not any(
                skip in path for skip in [
                    ".venv", ".git", "__pycache__", "generated_images",
                    ".gradle", "build", ".idea", "node_modules",
                    "models_cache", "adapters", "training_data",
                ]
            ),
        )
    ],
)
@modal.asgi_app()
def fastapi_app():
    """Entry point: returns the ImagineAI FastAPI application."""
    import sys
    import os

    # Ensure the project root is on the Python path
    sys.path.insert(0, "/app")

    # Point model cache at the Modal volume
    os.environ.setdefault("HF_HOME", MODEL_CACHE_DIR)
    os.environ.setdefault("HF_DATASETS_CACHE", MODEL_CACHE_DIR)
    os.environ.setdefault(
        "MODEL_REVISION", "b261bac6fd2cf515557d5d0707481eafa0485ec2"
    )
    # Use the A10G adaptive profile (40 GB VRAM, so budget is relaxed)
    os.environ.setdefault("PRELOAD_MODEL", "true")

    from backend.app.main import create_app
    return create_app()


# ---------------------------------------------------------------------------
# 5. Local entrypoint — invoke with:  modal run modal_deploy.py
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main():
    """
    Run this once to pre-download all model weights into the Modal volume.
    After this, cold starts load from disk (~15s) instead of downloading.

    Usage:
        modal run modal_deploy.py        # pre-download weights
        modal deploy modal_deploy.py     # deploy the web endpoint
    """
    print("Pre-downloading models into Modal volume...")
    download_models.remote()
    print("\nDone! Now deploy the web endpoint with:")
    print("  modal deploy modal_deploy.py")
