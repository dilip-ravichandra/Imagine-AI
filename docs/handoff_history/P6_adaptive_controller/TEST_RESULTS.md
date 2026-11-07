# TEST_RESULTS (P6) — build sandbox: Ubuntu 24.04, Python 3.12.3, no GPU, no network, **no pytest / pydantic / fastapi installed**
| Command | Status | Notes |
|---|---|---|
| P6 tests (`tests/test_adaptive_{profiles,policy_resources,controller,executor,service,scripts}.py`) | PASSED 95/95 | run with a throwaway minimal pytest shim (supports assert, raises, parametrize, tmp_path) and, for service/script tests, a throwaway pydantic STUB without validation. NOT real pytest/pydantic. |
| `tests/test_adaptive_api.py` (2 tests, real HTTP layer) | NOT RUN | needs fastapi + pydantic |
| Earlier 355 tests (P0-P5A) with real pytest | NOT RUN here | unchanged code paths except `generation.py`/`main.py`/`config.py`/`errors.py` (opt-in additions); the `test_api.py` explanation string "No adaptive controller" is preserved |
| `python evaluation/scripts/demo_p6_controller.py` | PASSED | synthetic fixture; decisions + simulated OOM; output in `evaluation/results/p6/` |
| Controller purity (no torch/fastapi/pydantic/backend import) | PASSED | subprocess check inside the test file |
| Real GPU profile, real OOM, SystemMonitor on CUDA, sweep script on SD-Turbo | NOT RUN | needs the RTX 5050 laptop |
| Windows / Android | NOT RUN | unchanged |
During development 3 first-draft *test* premises were wrong and were fixed (error-code precedence for a known-bad 768px entry; a helper constructor; a 32-hex request id); controller code was not changed because of them.
