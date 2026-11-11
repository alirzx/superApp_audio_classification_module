# Deployment

Use `docker compose --env-file .env config --quiet` then `docker compose --env-file .env up --build -d`. The one-shot model-setup must complete before API. UI starts independently and shows an offline indicator when API cannot initialize. Avoid `docker compose down -v` unless deliberately discarding the model volume.

Local: API 127.0.0.1:8007, UI 127.0.0.1:8088. Production template's `192.168.4.209` UI bind is an example that **must match the target server**. Keep API loopback-only. Protect UI with LAN/VPN firewall or authenticated HTTPS ingress and a strong unique API_TOKEN. Nginx's API token does not provide per-user auth.

Production `EXPECTED_MODEL_SHA256` must be populated from independently verified official checkpoint bytes because upstream release metadata does not publish a digest. First bootstrap requires GitHub release download access. Docker image builds require accessible Docker base images, Python package mirrors, PyTorch CPU wheel index and npm registry. Runtime needs no checkpoint network. API defaults to 2 CPUs, 1200 MB RAM, one Uvicorn worker, read-only filesystem and bounded tmpfs. UI defaults to 0.5 CPU, 256 MB RAM, non-root Nginx.

Verification: `docker compose ps -a`, logs for model-setup/API/UI, API `/health/ready`, UI `/healthz`, and real classification via Nginx. Run peak memory, p50/p95 wall time, accuracy, malformed audio and large-file tests on target hardware. No GitLab CI file is provided; deployment team owns its implementation.
