# P5A — Classical CV: resize, colour, edge-aware

Status: **code + 61 unit tests complete. Effect on real SD-Turbo output NOT evaluated** (no real generation exists yet). Covers mandatory CV items 1-3 of 5 (resize/resolution, colour correction/enhancement, edge-aware processing). Quality assessment and artifact detection are P5B. **Nothing is wired into `/generate` yet** (`performance.cv_ms` stays null); orchestration with per-stage toggles is a P5B task.
Dependencies: `numpy`, `opencv-python-headless` (tested with OpenCV 5.0.0 only). No torch, no backend imports.

## 1. Common contract (`computer_vision/common.py`)
Image = numpy `uint8`, shape `(H, W, 3)`, **RGB**. Anything else raises `ValueError` (no silent coercion). Every stage returns `CVResult(image, applied, stage, params, notes)`, so stages chain via `result.image`. Stages never mutate the input. **Bypass:** `enabled=False`, or identity parameters, returns an unchanged copy with `applied=False` and a note saying why. `to_array(pil)` / `to_pil(arr)` convert from/to PIL (alpha dropped).

## 2. Interfaces and defaults
| Module | Function | Key parameters (defaults) |
|---|---|---|
| `computer_vision.resize` | `resize_image(image, width, height, mode, ...)` | `mode="fit"` (`stretch`/`fit`/`pad`/`fill`), `interpolation="auto"`, `multiple_of=1`, `pad_color=(0,0,0)`, `allow_upscale=True` |
| | `fit_to_resolution(image, resolution, mode="pad")` | square output, aspect ratio kept |
| | `nearest_supported_resolution(value, supported, prefer="nearest")` | `nearest`/`down`/`up` |
| | `choose_interpolation(src_wh, dst_wh)` | down -> `area`, up -> `lanczos`, mixed -> `cubic` |
| `computer_vision.enhancement` | `adjust_brightness_contrast(image, brightness=0, contrast=1)` | brightness in [-1,1], contrast pivot at 128 |
| | `adjust_gamma(image, gamma=1)` | `gamma>1` brightens |
| | `white_balance_gray_world(image, strength=1, max_gain=1.5)` | gains clamped to [1/max_gain, max_gain] |
| | `adjust_saturation(image, factor=1)` | HSV saturation scale |
| | `apply_clahe(image, clip_limit=2, tile_grid=(8,8), channel="lab_l", strength=1)` | lightness only; `hsv_v` option |
| | `auto_enhance(image, EnhanceConfig())` | guarded: white balance -> exposure gamma -> mild CLAHE, each only outside a dead band |
| `computer_vision.edge_aware` | `edge_map(image, method="canny"\|"sobel")`, `edge_density(image)` | analysis only; Canny thresholds from grey median unless given |
| | `bilateral_smooth(image, d=7, sigma_color=30, sigma_space=5, strength=1)` | edge-preserving denoise |
| | `guided_filter_smooth(image, radius=4, eps=0.01, guide=None, strength=1)` | own box-filter implementation, no opencv-contrib |
| | `edge_preserving_sharpen(image, amount=0.6, radius=1.0, edge_threshold=0.2, halo_guard=True, max_amount=2.0)` | unsharp mask weighted by edge strength |

## 3. Design decisions
- Resize: `area` for shrinking (averages source pixels, no aliasing), `lanczos` for enlarging (sharper than bicubic, may ring on hard edges). Resolution *policy* (which size to generate at) is P6's job; P5A only provides snapping and aspect-safe resizing.
- `auto_enhance` is dead-banded so an acceptable image comes back untouched; exposure moves the mean toward the band edge, never past it; gamma clamped to [1/1.6, 1.6]; white-balance gain clamped to 1.25 and blended at 0.6.
- `edge_preserving_sharpen` only acts near clear edges, so flat regions and low-contrast noise stay (nearly) unchanged. `halo_guard` clips each pixel to the min..max of its 3x3 input neighbourhood: no ringing beyond local values, **but it also caps how much an edge can steepen** (wider blur needs a larger `radius`; turning the guard off allows overshoot).

## 4. Limits and observed behaviour (read before enabling anything)
- **All `EnhanceConfig` thresholds are provisional and untuned.** None has been checked against real model output.
- Gray-world white balance is wrong for scenes dominated by one colour (e.g. underwater). The clamp and strength bound the damage; they do not remove it.
- CLAHE amplifies noise. Measured on the synthetic demo scene (noise proxy = std of image minus its Gaussian blur, flat sky patch, 4.28 at input): `auto_enhance` alone raised it to 5.91; bilateral at strength 0.5 around it left 3.4-3.5 (order made little difference); bilateral at strength 1.0 gave 1.27. Visual check of `strip.png`: the enhance step also pulled the intentionally blue sky toward grey and made grain visible. So on this synthetic scene the result is mixed, not an improvement. **Synthetic image only: it says nothing about SD-Turbo output.**
- Sharpen on a Gaussian-blurred step edge: steepening is real but bounded (peak gradient 40 -> 52 at blur sigma 1.0, radius 1; 20 -> 22 at sigma 2.0, radius 1).
- Timings in the demo (~5-116 ms per stage, 512x512, 1-core sandbox CPU) are not representative of the laptop.
- Semantic defects (wrong object, count, anatomy) cannot be fixed by these filters (P5B must flag them instead).

## 5. Demo and tests
```
python evaluation/scripts/demo_cv_p5a.py                       # synthetic degraded scene
python evaluation/scripts/demo_cv_p5a.py --input <your own generated PNG>
python -m pytest -q tests/test_cv_resize.py tests/test_cv_enhance.py tests/test_cv_edge.py tests/test_cv_compose.py
```
Outputs `before.png`, `after.png`, `strip.png`, `metrics.json` (measurements only, no verdict) in `evaluation/results/p5a/`. The committed copies come from the synthetic scene. Tests use only procedural images (no photos, nothing copyrighted); `test_cv_compose.py` checks stages chain, bypass is identity, and the three modules do not import each other or torch/backend.
