# Clean clone / setup test — procedure and log

**Status: NOT RUN.** Do this on a second machine or fresh folder (Windows PowerShell):
```
git clone <repo-url> imagineai-clean; cd imagineai-clean; git checkout develop
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/api/v1/capabilities
```
Then with GPU: `pip install -r requirements-ml.txt`, set `MODEL_REVISION`, POST `/api/v1/generate`, open the image URL. Phone: `http://<LAN-IP>:8000/health` in the phone browser. Android: open `android/` in Android Studio, sync, run.

| Check | Date | Machine | Result (paste real output) |
|---|---|---|---|
| pytest | | | |
| /health | | | |
| real generate | | | |
| phone browser to server | | | |
| Android build/run | | | |
| Docker build (optional, never built) | | | |
