# 9. Mobile Deployment and Resource Feasibility

## 9.1 Be precise about deployment labels
- **On-device:** the full required generation path executes on the Android device.
- **Hybrid:** Android app uses a separate laptop/edge server for inference or part of the pipeline.
- **Cloud:** remote hosted backend performs generation.

If Android sends a prompt to FastAPI on the laptop or cloud, it is not on-device generation. Label it accurately in the UI, architecture and report.

## 9.2 Full pipeline requirement
For on-device claims, validate the full generation path:
- Tokenizer and text encoder.
- Denoiser / UNet or equivalent.
- Scheduler operations.
- VAE decoder.
- Image post-processing.
- Model files and runtime dependencies.

Exporting only one component does not prove full on-device generation.

## 9.3 Candidate deployment route
Investigate ONNX Runtime Mobile, Android NNAPI, or a supported accelerator/runtime only after checking compatibility for every required model component and operator. Validate output correctness against reference inference.

## 9.4 Device tests
On an actual Android phone, measure:
- App install size and model download size.
- Model storage/cache.
- Startup and model-load time.
- Peak memory.
- Generation latency.
- Thermal/sustained performance if measurable.
- Behavior under low memory.
- Network loss for hybrid/cloud.
- Permission, image save/share, and lifecycle behavior.

Use emulator for UI/integration, but do not treat emulator performance as a physical-device benchmark.

## 9.5 Development laptop
Target system noted by team: RTX 5050 Laptop GPU (~8 GB VRAM), 24 GB system RAM. Begin with one pipeline loaded and one generation at a time. Use low/moderate resolution while establishing the baseline. Monitor GPU use with `nvidia-smi`. Training may need Colab or another GPU environment.

## 9.6 LAN development
For phone-to-laptop testing:
- Both devices need a reachable network path.
- Use laptop LAN IP in Android configuration, not `localhost`.
- Ensure backend binds to an accessible interface.
- Configure firewall appropriately.
- Use development-only cleartext traffic configuration only when necessary.
- Do not put LAN addresses or secrets into release builds.
