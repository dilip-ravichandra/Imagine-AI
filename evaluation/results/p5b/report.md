# P5B before/after report (SYNTHETIC images)

> Thresholds were set while looking at images like these. A flag on its own degradation is a sanity check, not a detection rate. This says nothing about real SD-Turbo output. `cases.png` shows before (left) / after (right) per case.

| case | flags before | steps (accepted ✔ / rejected ✘) | flags after | key measurement before → after |
|---|---|---|---|---|
| clean scene | - | none | - | unchanged |
| blur sigma 1.5 | blur | ✘ sharpen (target measurement did not improve enough) | blur | unchanged |
| blur sigma 3 | blur | ✘ sharpen (target measurement did not improve enough) | blur | unchanged |
| noise sigma 8 | noise | ✔ denoise | - | noise_sigma 8.154 → 1.812; blur_ratio 0.237 → 0.219 |
| noise sigma 15 | noise | ✔ denoise | - | noise_sigma 15.073 → 4.201; blur_ratio 0.257 → 0.228 |
| dark x0.3 | dark, low_contrast | ✔ exposure; ✘ contrast (target measurement did not improve enough) | low_contrast | blur_ratio 0.212 → 0.21; brightness 0.169 → 0.296; colour_cast 0.097 → 0.064 |
| low contrast | low_contrast | ✘ contrast (target measurement did not improve enough) | low_contrast | unchanged |
| colour cast | colour_cast | ✔ white_balance | - | blur_ratio 0.209 → 0.21; brightness 0.528 → 0.548; colour_cast 0.267 → 0.116 |
| overexposed x1.8 | bright, clipped_highlights | ✔ exposure | bright, clipped_highlights | brightness 0.893 → 0.855; colour_cast 0.045 → 0.063 |
| oversharpened (halo) | halo | none | halo | unchanged |
| blur 2 + noise 8 | blur, noise | ✔ denoise; ✘ sharpen (target measurement did not improve enough) | blur | noise_sigma 7.907 → 1.977; blur_ratio 0.5 → 0.524 |
| dark + noise 6 | noise, dark, low_contrast | ✔ denoise; ✔ exposure; ✔ contrast | low_contrast | noise_sigma 5.93 → 2.389; blur_ratio 0.263 → 0.239; brightness 0.167 → 0.307; colour_cast 0.098 → 0.062 |
| night scene, prompt says night | - (suppressed: dark, low_contrast) | none | - | unchanged |
| same dark image, prompt silent | dark, low_contrast | ✔ exposure; ✘ contrast (target measurement did not improve enough) | low_contrast | blur_ratio 0.212 → 0.21; brightness 0.169 → 0.296; colour_cast 0.097 → 0.064 |
| blue underwater tint, prompt says underwater | - (suppressed: colour_cast) | none | - | unchanged |
| same tint, prompt silent | colour_cast | ✔ white_balance | colour_cast | blur_ratio 0.208 → 0.209; brightness 0.47 → 0.489; colour_cast 0.409 → 0.249 |
| INTENDED fine grain (sigma 8) | noise | ✔ denoise | - | noise_sigma 8.072 → 1.977; blur_ratio 0.236 → 0.219 |
