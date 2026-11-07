# Claude task — Android Imagine AI client

## Objective
Implement Android UI and API integration using Kotlin, Jetpack Compose, MVVM and Retrofit/OkHttp.

## Allowed files
`android/ImagineAI/` only, unless explicitly agreed.

## Screens/states
- Prompt entry.
- Quick/Balanced/Best mode.
- Generate action.
- Loading/progress state.
- Result image.
- Generation configuration/resource explanation.
- Retry and actionable error state.
- Save/share if feasible and permissions are handled.

## Requirements
- Use the agreed API contract in `docs/07_API_CONTRACT.md`.
- Do not hardcode localhost for physical-device backend access; make base URL configurable.
- Handle null metrics and remote/hybrid inference honestly.
- Avoid blocking the main thread.
- Include previews or tests where practical.

## Acceptance
- Gradle build succeeds in stated environment.
- API parsing tested against success and error fixtures.
- UI handles loading, success, empty prompt and failure.
- Provide device/emulator test instructions.

## Return
ZIP-ready Android module or patch, README, files changed, build/test log and known limitations.
