# 6. Team, Git, Claude, and Antigravity Workflow

## 6.1 Human ownership

### Person 1 — AI/ML and backend lead
Owns:
- `backend/`
- `ai_engine/`
- `computer_vision/`
- `evaluation/`

Responsibilities:
- FastAPI and schemas.
- Prompt parser.
- Diffusion model integration.
- LoRA adaptation and training records.
- Optimization and model compatibility.
- Resource controller and monitoring.
- CV pipeline.
- Evaluation scripts and benchmark evidence.

### Person 2 — Android and product lead
Owns:
- `android/`

Responsibilities:
- Kotlin/Compose/MVVM.
- Prompt and quality-mode UI.
- Loading/progress/error states.
- Retrofit/OkHttp integration.
- Result display, save/share and history if implemented.
- Actual phone/emulator testing.
- User-facing resource explanation and UX.

### Shared responsibilities
- Agree API contract.
- Review each other's pull requests.
- Build prompt suite and failure-case review.
- Test integration.
- Prepare demo and viva.
- Both understand the system architecture and evaluation results.

## 6.2 Tool responsibilities
The team has ordinary/free accounts. The workflow must remain useful within normal usage limits; do not assume paid features, unlimited agent calls, or simultaneous capacity. Use only accounts and access permitted by each provider.

- **Claude:** primary code drafting for a bounded module; can also explain or review.
- **Antigravity:** inspect ZIP, open project, run code, debug, integrate and verify.
- **ChatGPT:** architecture, task decomposition, interface contracts, debugging guidance, requirements audits, benchmark interpretation, and review prompts.
- **GitHub:** source of truth. Chat conversations and ZIPs are not the source of truth.

## 6.3 ZIP handoff protocol
Every generated module ZIP must include:
- Source files.
- README with exact setup/run commands.
- Dependencies and versions.
- Tests.
- Expected test outcomes.
- Files created/modified.
- Integration points and API/schema assumptions.
- Known limitations.
- Changelog/version.
- No secrets, tokens, or private credentials.

ZIP naming:
`ImagineAI_<module>_v<major>.<minor>_<YYYYMMDD>.zip`

Before accepting:
1. Inspect archive contents.
2. Check for unexpected paths and secrets.
3. Extract into a clean feature branch/worktree, not over the only copy.
4. Review diffs.
5. Install dependencies in a clean environment.
6. Run tests and manual acceptance steps.
7. Run integration tests.
8. Commit only after acceptance.

Never blindly replace the whole repository with a ZIP. Apply only the module's owned files. Keep a backup/branch before integration.

## 6.4 Git branching
- `main`: stable demo/release.
- `develop`: integration branch.
- `feature/diffusion-engine`
- `feature/backend-api`
- `feature/prompt-intelligence`
- `feature/cv-pipeline`
- `feature/evaluation`
- `feature/adaptive-router`
- `feature/android-app`

Rules:
1. No direct work on `main`.
2. One owner per module.
3. Pull latest `develop` before creating/updating a branch.
4. PR into `develop`; tests required.
5. Other developer reviews.
6. Merge to `main` only after integrated app test.
7. Never resolve unfamiliar conflicts by accepting all incoming/current changes without inspecting them.

## 6.5 Task-card format for every AI request
- Objective.
- Context and relevant spec IDs.
- Allowed files.
- Files that must not be changed.
- Inputs/outputs and exact interface.
- Environment/version constraints.
- Acceptance tests.
- Required documentation.
- Explicit instruction not to fabricate test results.

Use prompts in `ai_handoff/`.
