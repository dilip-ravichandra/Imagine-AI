# Imagine AI — Phase Tracker

| Order | Phase | Owner | Status | Commit/ZIP | Next handoff checked |
|---|---|---|---|---|---|
| 1 | P0 Foundation | Both | PARTIAL (backend tested; Android build + team env pending) | ImagineAI_P0_Foundation.zip | Yes |
| 2 | P1A Backend baseline | Person 1 | PARTIAL (code + 35 unit tests pass; real SD-Turbo run NOT RUN) | ImagineAI_P1A_Backend.zip | Yes |
| 3 | P1B Android vertical slice | Person 2 | READY (API stable; real image pending laptop smoke test) | | |
| 4 | P2 Prompt intelligence | Person 1 | COMPLETE (244 tests pass; unseen hold-out 12/20 first run; Windows run NOT RUN) | ImagineAI_P2_Prompt_Intelligence.zip | Yes |
| 5 | P3A Adaptation prep/train | Person 1 | BLOCKED BY P1A laptop smoke test (revision pin, license, scheduler) | | |
| 6 | P3B Adapter integration | Person 1 | BLOCKED BY P3A | | |
| 7 | P4 Optimization | Person 1 | BLOCKED BY baseline | | |
| 8 | P5A CV resize/colour/edge | Person 1 | BLOCKED BY image interface | | |
| 9 | P5B CV quality/artifacts | Person 1 | BLOCKED BY P5A | | |
| 10 | P6 Adaptive controller | Person 1 | BLOCKED BY profiles | | |
| 11 | P7A Metrics harness | Person 1 | BLOCKED BY generation | | |
| 12 | P7B Ablation/failure report | Both | BLOCKED BY P7A | | |
| 13 | P8 Mobile/deployment | Person 2 + Person 1 | BLOCKED BY stable app/API | | |
| 14 | P9 Final submission/demo | Both | BLOCKED BY P7B/P8 | | |

Status values: NOT STARTED / IN PROGRESS / PARTIAL / COMPLETE / BLOCKED.
COMPLETE requires tests/evidence, not just generated code.
