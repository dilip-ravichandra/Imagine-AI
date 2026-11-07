# Branching and PR rules
- Branches: `main` (release/demo only), `develop` (integration). Never commit directly to either.
- Feature branches from `develop`: `feature/p1a-backend-baseline`, `feature/p1b-android-slice`, `fix/<short-desc>`, `docs/<short-desc>`. Pattern: `<type>/<phase-id>-<kebab-desc>`.
- Ownership: Person 1 = backend/, ai_engine/, computer_vision/, evaluation/. Person 2 = android/. Cross-owner changes need the owner's review.
- PR rules: target `develop`; one phase per PR; tests run and results pasted in PR; reviewer is the other developer; squash merge; no secrets, model weights, datasets or APKs.
- API contract changes: separate PR, version bump in `schemas/v1.py` + `docs/API_CONTRACT_v1.md`, both devs approve.
- Commit style: `p1a: add baseline generation service`.
