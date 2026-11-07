"""Multi-model generation engine supporting:
1. SD-Turbo (ADD Distilled, 2 steps, fp16)
2. SD 1.5 Final Optimized (LCM-LoRA, 8 steps, fp16, LCMScheduler)
3. SD 1.5 Adapted (LCM-LoRA, 30 steps, fp32)
4. SD 1.5 Baseline (Unchanged, 30 steps, fp32)
"""
import time
import uuid
import logging
from typing import Optional
from PIL import Image

log = logging.getLogger("imagineai.multimodel")

_PIPELINES = {}

def get_pipeline(model_choice: str):
    import torch
    from diffusers import StableDiffusionPipeline, LCMScheduler, AutoPipelineForText2Image

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if model_choice == "sd_turbo":
        if "sd_turbo" not in _PIPELINES:
            log.info("Loading SD-Turbo into memory...")
            pipe = AutoPipelineForText2Image.from_pretrained(
                "stabilityai/sd-turbo",
                torch_dtype=torch.float16,
                variant="fp16",
                local_files_only=True,
                safety_checker=None
            ).to(device)
            _PIPELINES["sd_turbo"] = pipe
        return _PIPELINES["sd_turbo"], device, "fp16", 2, 0.0

    elif model_choice == "sd15_optimized":
        if "sd15_optimized" not in _PIPELINES:
            log.info("Loading SD 1.5 Final Optimized (LCM-LoRA + fp16)...")
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16,
                local_files_only=True,
                safety_checker=None
            ).to(device)
            pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
            pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
            _PIPELINES["sd15_optimized"] = pipe
        return _PIPELINES["sd15_optimized"], device, "fp16", 8, 1.5

    elif model_choice == "sd15_adapted":
        if "sd15_adapted" not in _PIPELINES:
            log.info("Loading SD 1.5 Adapted (LoRA, fp32)...")
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float32,
                local_files_only=True,
                safety_checker=None
            ).to(device)
            pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
            _PIPELINES["sd15_adapted"] = pipe
        return _PIPELINES["sd15_adapted"], device, "fp32", 30, 7.5

    else:  # sd15_baseline
        if "sd15_baseline" not in _PIPELINES:
            log.info("Loading SD 1.5 Baseline (fp32)...")
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float32,
                local_files_only=True,
                safety_checker=None
            ).to(device)
            _PIPELINES["sd15_baseline"] = pipe
        return _PIPELINES["sd15_baseline"], device, "fp32", 30, 7.5


def generate_with_model(
    prompt: str,
    model_choice: str = "sd_turbo",
    seed: Optional[int] = None,
    resolution: int = 512,
    custom_steps: Optional[int] = None
) -> dict:
    import torch

    pipe, device, precision, default_steps, guidance = get_pipeline(model_choice)
    steps = custom_steps or default_steps
    seed_val = seed if seed is not None and seed >= 0 else int(torch.randint(0, 2**31 - 1, (1,)).item())
    generator = torch.Generator(device).manual_seed(seed_val)

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    t0 = time.perf_counter()
    image = pipe(
        prompt=prompt,
        num_inference_steps=steps,
        guidance_scale=guidance,
        width=resolution,
        height=resolution,
        generator=generator
    ).images[0]

    if device == "cuda":
        torch.cuda.synchronize()
    latency_ms = (time.perf_counter() - t0) * 1000

    peak_vram = 0.0
    if device == "cuda":
        peak_vram = torch.cuda.max_memory_allocated() / (1024 * 1024)

    return {
        "image": image,
        "model": "runwayml/stable-diffusion-v1-5" if "sd15" in model_choice else "stabilityai/sd-turbo",
        "model_choice": model_choice,
        "precision": precision,
        "steps": steps,
        "seed": seed_val,
        "resolution": resolution,
        "latency_ms": latency_ms,
        "peak_vram_mb": peak_vram
    }
