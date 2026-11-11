# Acceptance Test Plan

1. Mocked API tests: auth, health, request schema, invalid upload, threshold/top-k, 527 labels and temporal responses.
2. One-shot setup: allowed release asset, expected byte size and externally verified production SHA256; manifest and cache reuse.
3. Real CPU checkpoint load with strict state dict and 527 finite logits; compare sample audio predictions to official upstream inference.
4. WAV/MP3/FLAC/WebM, corrupt and oversize files, short and >60s audio, duration and decoder timeout limits.
5. Docker Compose config/build; model-setup completion, API readiness, Nginx UI /healthz and authenticated /api proxy.
6. Benchmark MN10 and MN04 on 2 CPU cores with peak RSS, p50/p95 latency, accuracy on representative audio.
7. Check per-user access policy, SSH deployment configuration, resource limits, no leaked model weights/API token, and source/license provenance.

Mock tests do not validate model accuracy or full Docker runtime. CI is managed separately.

8. Validate APT signed primary/fallback, PyPI primary/fallback, official CPU wheel installation, Arvan base images and npm/APK mirrors on the actual GitLab runner/server.
9. CI owner verifies protected variables, pinned SSH host keys, deployment branch, and post-deploy readiness checks.
