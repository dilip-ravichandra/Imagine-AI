# Safety and phase audit — combined tree v0.3 (2026-11-07)

Method: re-ran everything runnable in a no-GPU Linux sandbox (Python 3.12.3, no torch, no Docker, no Android toolchain). Nothing here is a GPU measurement.
Legend: **VERIFIED** = observed this session · **FIXED** = changed in this session, with tests · **OPEN** = needs a human/GPU/device · **NOT CHECKED** = could not be.

## 1. Test status (the handoff's "first action")
| Check | Result |
|---|---|
| `pip install -r requirements.txt && python -m pytest -q` before changes | **666 passed, 1 skipped** (confirms the earlier merge-session figure, now observed) |
| After this session's changes | **698 passed, 1 skipped** (+32 safety tests in `tests/test_safety.py`) |
| Mutation checks on the new safety tests (auth route unprotected, weak key compare, wrong static dir, key in repr, CLIP pin removed, Docker `USER` removed) | each made a test fail; code restored |
| Real `uvicorn` process, probed with curl (auth off and on) | health/capabilities/prompt-analysis OK; generate returns a clean 503 without torch; traversal probes 404; 600 KB body 422; key never in server log; short `API_KEY` rejected at startup |
| P7 dry-run → analyzer | gate **NOT MET**, synthetic excluded, as designed |
| P6/P5A/P5B demo scripts regenerated into temp dirs | decisions/metrics/report **identical** to the committed files (timings excluded) → committed results were not hand-edited, all labelled SYNTHETIC |
| Parser suite recomputed in memory | 87 cases; **hold-out 12/20** matches the claim; dev 67/67 is the tuning set, not independent evidence |

## 2. Phase check: tracker claim vs what was found
| Phase | Tracker | Evidence found | Verdict |
|---|---|---|---|
| P0 | PARTIAL | backend + tests run; Android never built (no Gradle here); no `.git` | agrees |
| P1A | PARTIAL, real run NOT RUN | engine/service/API tested with fakes; live server starts; **no real image was ever generated** | agrees |
| P1B | not delivered | `MainActivity.kt` skeleton only; manifest has no `INTERNET` permission, no UI/Retrofit | agrees |
| P2 | COMPLETE | 87-prompt suite, hold-out 12/20 recomputed | agrees (parsing only; no generation evidence) |
| P3A/P3B | PARTIAL, DL-02 open | training/compare/approve code, gated loader, tests; **no adapter trained or approved** | agrees |
| P4 | PARTIAL | harness + tests; **no measured result** | agrees |
| P5A/P5B | COMPLETE for code+tests | tests pass; results synthetic and reproducible; thresholds provisional | agrees |
| P6 | COMPLETE for code+tests | controller/fallback/simulated tests; **no measured profile**; not reachable remote fallback | agrees |
| P7A/P7B | PARTIAL | harness + generators; report content not written | agrees, **but generators contained stale text (see F4)** |
| P8 | BLOCKED | nothing to check | agrees |
| P9 | PARTIAL, gate NOT MET | docs only | agrees |
No status was upgraded by this audit.

## 3. Requirement status (docs/02), by kind of evidence
No requirement is yet evidenced by **real measurements or a reviewed result**; everything depending on the GPU laptop, a phone, hosting or team review is open.
| Evidence level | Requirements |
|---|---|
| Code + tests (synthetic/fakes only), real evidence still missing | CV-01..CV-05, DL-01, DL-04, OPT-01/02, ADV-02..ADV-06, EVAL-01, EVAL-03..EVAL-06, APP-02 (backend side), DEL-06 (generators) |
| Partly evidenced by a real measurement | ADV-01 (prompt *parsing* hold-out 12/20; no generated images) |
| Metric cannot currently be computed | EVAL-02 (FID gate refuses: no real reference set / extractor) |
| Docs/drafts only | DEL-03 (`docs/diagrams/` absent; text architecture in `docs/P9_FINAL/ARCHITECTURE.md`), DEL-04, DEL-05 (draft, no USNs), DEL-07 |
| Not started / blocked | **DL-02 (no adapter)**, DL-03 (no profiling report), OPT-03, APP-01, APP-03 (UI), DEL-01, DEL-02 (no git, clean clone untested) |

## 4. Safety findings
### FIXED this session
| # | Finding | Fix |
|---|---|---|
| F1 | `ClipScorer` (used by P4/P6/P7 `--clip`) downloaded CLIP **unpinned** (bandit B615, Medium): violates the project's pin-every-model rule and is a supply-chain/reproducibility risk | Requires `CLIP_REVISION` (or `--allow-unpinned`); the revision is recorded in the result label. Test added |
| F2 | Public API had **no access control** while a hosted URL is planned (anyone could consume GPU time) | Optional `API_KEY` env → `X-API-Key` required on `/api/v1/*` (constant-time compare, checked before validation and before the GPU, never logged/echoed, ≥16 chars, `repr` hidden). **Default OFF: behaviour unchanged.** `/health` and `/images/*` stay open. New error code `UNAUTHORIZED` (additive; see API contract) |
| F3 | Dockerfile ran as **root**, no healthcheck | Non-root user, healthcheck, no bytecode. **Not built** (no Docker here) |
| F4 | P7/P7B generators and docs said "P6 skipped / no controller", "P3A/P3B skipped", "P5B NOT DONE": **inaccurate in the final report** (the code exists; only measured evidence is missing) | Wording corrected in `variants.py`, `p7b.py`, `docs/P7A_EVAL.md`, `docs/P6_ADAPTIVE.md`, `docs/P4_OPTIMIZATION.md`, and the 2 tests that asserted the old text |

### VERIFIED OK
No secrets/keys/tokens in the tree (regex scan); no weights, APKs, keystores or `.env`; `.gitignore` covers them. Image ids are server-generated uuid4 hex; static route not traversable or listable (tested with encoded/`..`/real-file probes); errors do not leak paths/traces; prompts are not written to the decision log. `pip-audit` on `requirements.txt`: **no known vulnerabilities**. Bandit (excl. vendored trainer): 0 High; remaining Low items are `subprocess` with a fixed argv list (no shell, no user input), non-crypto `random` for dataset sampling, and a guarded cache-clear `except`. Adapter loading is gated: fixed `.safetensors` filename (no pickle), SHA-256 bound to approval, base-revision match. Vendored trainer hash-checked, Apache-2.0 header kept.

### OPEN (human decision or infrastructure)
| # | Risk | Recommendation |
|---|---|---|
| O1 | **No content moderation anywhere in the serving path** (only a check inside the training compare script). A public text-to-image URL can be used to generate harmful content, and the model's acceptable-use terms still apply to the team. Whether the loaded pipeline includes a safety checker is **unverified** | Decide before hosting: restrict the demo (API key, small audience), and/or add a prompt/safety filter |
| O2 | No rate limiting, no request-body size limit (uvicorn default). Only one generation runs at a time (429 for others) | Put the hosted service behind a reverse proxy/tunnel with per-IP rate and body-size limits |
| O3 | **TLS/cleartext:** the Android app will call a LAN or hosted HTTP backend | Hosted: HTTPS only. Cleartext only for dev via a network-security config. Manifest also needs `INTERNET` and should set `allowBackup="false"` (Person 2) |
| O4 | SD-Turbo licence. Copies on the Hub show differing wording (research-only vs non-commercial vs "commercial: see Stability AI licence"); I could not read the official card at your pinned revision | Read it at the pinned revision, record it in `eval_P3_TeamID.md`; treat hosting as non-commercial coursework unless the licence says otherwise |
| O5 | CLIP, COCO (per-image licences vary), project licence file (none), Python/Android dependency licences | `pip-licenses` on the final venv; choose a project licence or "all rights reserved" |
| O6 | ML/training dependencies (torch, diffusers, transformers, peft, …) are floors, not pinned, and **not audited** (not installable here) | Pin after the first successful run, then `pip-audit` that venv |
| O7 | Git history never scanned (no `.git` supplied) | Run gitleaks/`git log -p` scan before making the repo public |
| O8 | `Host`-header-derived `image_url` when `PUBLIC_BASE_URL` is unset | Set `PUBLIC_BASE_URL` for any hosted/proxied run |
| O9 | The adapter approval is an integrity check, not a security boundary (anyone with write access to the adapter folder can forge it) | Keep the adapter folder write-protected on the server |
| O10 | Dockerfile has no adaptive-profile/adapter wiring (needs mounted files) and installs `pytest`/`matplotlib` from `requirements.txt` | Split runtime vs dev requirements before the final deployment |

## 5. NOT CHECKED
GPU behaviour, any real generation, Windows/PowerShell run, Android build, Docker build, hosted URL, phone, the official model cards/licences, ML dependency vulnerabilities, Git history.
