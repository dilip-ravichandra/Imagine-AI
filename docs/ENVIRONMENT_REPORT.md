# Environment report
## A. Build sandbox (where this P0 scaffold was created and tested — NOT the team's machine)
| Item | Value |
|---|---|
| OS | Ubuntu 24.04.5 LTS (Linux 6.18) |
| Python | 3.12.3 |
| FastAPI / Pydantic / Uvicorn / httpx / pytest | 0.162.0 / 2.14.3 / 0.54.0 / 0.28.1 / 9.2.0 |
| JDK | OpenJDK 21.0.12 |
| Gradle / Android SDK / AGP | not installed / ANDROID_HOME unset / not verified |
| GPU / CUDA / PyTorch | no NVIDIA GPU, no nvidia-smi / not installed |
| CPU / RAM | 1 core / ~3 GB |

## B. Team development machine (from project brief; UNVERIFIED)
RTX 5050 Laptop GPU (~8 GB VRAM), 24 GB RAM. OS, Python, JDK, Gradle, AGP, PyTorch/CUDA, phone model: **TO BE RECORDED by team**.
Run on the laptop and paste results here:
```
python --version; java -version; nvidia-smi; git --version
python -c "import torch;print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```
Note: RTX 50-series (Blackwell) may need a recent PyTorch/CUDA build; verify before pinning (P1A).

## C. Team-reported facts (P1A session, stated by the developer; not machine-verified)
| Item | Value |
|---|---|
| Development OS | Windows (edition/version not given) |
| Test phone | 16 GB RAM (model not given) |
| GitHub repo URL | none yet |
Still missing: Python/JDK/Android Studio versions, `nvidia-smi` and the torch/CUDA output from the RTX 5050 laptop.
