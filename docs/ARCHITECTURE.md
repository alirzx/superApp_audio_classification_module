# Architecture

Browser → React + Vite → Nginx :8080 → /api proxy (inject server-side X-API-Key) → FastAPI :8000 → validate upload → FFmpeg decode 32kHz mono PCM → fixed 10s windows (zero-pad final) → upstream EfficientAT evaluation preprocessing: preemphasis, 1024-point STFT, 800-sample Hann window, 320-sample hop, 128 mel bands, log + normalization → MobileNetV3 MN10 or MN04 → 527 logits → sigmoid → threshold/top-K → clip mean score and per-segment output → JSON/React timeline.

One-shot model setup downloads a fixed allowlisted release asset from EfficientAT GitHub `v0.0.1`, validates byte count and optional external digest, writes a cache integrity manifest. Runtime verifies the manifest and local checkpoint, then uses safe tensor-only loading and strict state dict validation. No network or model download at inference. Two long-running containers, API and UI, plus one-shot model-setup. No user data persistence, database, broker, or GPU.
