# 11. Risks, Decisions, and Open Questions

## 11.1 Key risks

| Risk | Impact | Mitigation |
|---|---|---|
| GPU memory exhaustion | Generation/training fails | One pipeline at a time, conservative resolution, profile memory, offload only if useful |
| Model/scheduler mismatch | Invalid or poor generation | Pin revisions; validate model card and scheduler compatibility |
| Free AI usage limits | Code generation interrupted | Small task cards, source of truth in Git, maintain local progress notes |
| ZIP overwrites/conflicts | Lost or incompatible code | Feature branches, inspect diff, module ownership, tests before merge |
| Dataset license issue | Cannot publish/use data | Check and record license/terms before download/use |
| Tiny FID sample | Misleading metric | Adequate dataset-level sample or justify alternative |
| CLIP overinterpretation | False semantic claims | Human review for counts/relations; explain metric limits |
| CV degrades image | Lower quality | Conservative conditional processing, bypass and ablation |
| Mobile runtime incompatibility | No true on-device generation | Test full pipeline; present hybrid honestly if needed |
| Scope creep | Core requirements unfinished | Mandatory-vs-optional separation; phase gates |
| Unreproducible results | Weak evaluation | Fixed prompts/seeds/configs, pinned versions, logs |

## 11.2 Model decision process
Benchmark candidates rather than selecting by name or parameter count. Start with one model (SD-Turbo is a practical first candidate), then test BK-SDM-Tiny or SD 1.5 + LCM-LoRA if time/compatibility allows. SSD-1B is lower priority for the constrained GPU. Record model license and exact revision.

## 11.3 Open decisions to settle in Phase 0
- Development OS: Windows 11, Windows + WSL2 Ubuntu, or native Ubuntu.
- Repository: new or existing GitHub repository.
- Android testing: physical device, emulator, or both.
- Git collaboration: GitHub branches/PRs (recommended) or another workflow.
- Phone model and available RAM/storage.
- Backend host: laptop for development; choose permitted deployment host for final demo.
- Dataset selection and license.
- Model selection after baseline profiling.
- Whether full on-device export is feasible; decide only after testing.

## 11.4 Version policy
Pin working versions after successful integration. Do not let separate AI sessions independently upgrade core dependencies. Person 1 owns Python/AI dependencies; Person 2 owns Android Gradle/JDK dependencies. Update versions through a reviewed PR with regression tests.
