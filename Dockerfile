# Starter backend container (API + classical CV only; install requirements-ml.txt on top for real generation).
# GPU runtime configuration depends on host driver, CUDA/PyTorch compatibility, and deployment provider.
# Validate before use. NOT BUILT in the sandbox that hardened it (no Docker there).
# Safety: runs as an unprivileged user. Never bake secrets into the image: pass API_KEY / MODEL_REVISION at run time.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/app/.cache/huggingface

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend ./backend
COPY ai_engine ./ai_engine
COPY computer_vision ./computer_vision

RUN useradd --system --create-home --uid 10001 appuser \
    && mkdir -p /app/generated_images /app/.cache/huggingface \
    && chown -R appuser:appuser /app/generated_images /app/.cache
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
