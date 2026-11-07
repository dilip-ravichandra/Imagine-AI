# P4 quality-cost table

_Generated mechanically from raw result files by ai_engine/optimization/report.py. It contains no interpretation. 'Fidelity' is pixel deviation from B0, not perceptual quality. Memory is PyTorch allocated/reserved GPU memory, not nvidia-smi totals._

**P4 gate (>=2 measured single-variable strategies + measured baseline): MET** — measured strategies: ['E1', 'E2', 'E3', 'E4', 'E5', 'E6']; baseline measured: True; missing experiments: none.


| Exp | Changed | Status | n_ok | Latency median ms [min-max] (sd) | x vs B0 | Peak alloc MB (median) | Δ MB vs B0 | Peak reserved MB | Fidelity PSNR dB vs B0 (mean; identical/pairs) | CLIP mean (Δ vs B0) |
|---|---|---|---|---|---|---|---|---|---|---|
| B0 | - | ok | 44 | 866 [862-876] (3) | - | 6500.4 | - | 7670.0 | - | 0.301 (-) |
| E1 | precision | ok | 44 | 418 [415-432] (3) | 0.48 | 3677.7 | -2822.7 | 4228.0 | 9.4; 0/22 | 0.304 (0.003) |
| E2 | steps | ok | 44 | 581 [572-592] (4) | 0.67 | 6500.4 | 0.0 | 7670.0 | 17.2; 0/22 | 0.311 (0.010) |
| E3 | steps | ok | 44 | 433 [427-443] (3) | 0.50 | 6500.4 | 0.0 | 7670.0 | 14.8; 0/22 | 0.310 (0.009) |
| E4 | attention_slicing | ok | 44 | 891 [887-920] (8) | 1.03 | 6500.4 | 0.0 | 7222.0 | 61.2; 0/22 | 0.301 (0.000) |
| E5 | vae_slicing | ok | 44 | 857 [854-864] (2) | 0.99 (ranges overlap B0) | 6500.4 | 0.0 | 7670.0 | n/a; 22/22 | 0.301 (0.000) |
| E6 | offload | ok | 44 | 2794 [2719-3030] (90) | 3.23 | 4066.2 | -2434.2 | 4472.0 | n/a; 22/22 | 0.301 (0.000) |
| C1 | precision, steps (COMBINED) | ok | 44 | 288 [283-296] (2) | 0.33 | 3677.7 | -2822.7 | 4228.0 | 9.9; 0/22 | 0.311 (0.010) |

Failed experiments (OOM/error) are results; see each JSON's `error` field.
