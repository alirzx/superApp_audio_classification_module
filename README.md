# SuperApp Module 07 | CPU Audio Classification

Independent CPU-first acoustic event classification service using **EfficientAT MN10** by default and configurable MN04 fallback. Follows previous SuperApp modules: FastAPI, React/TypeScript/Vite, Nginx, Docker Compose, one-shot model setup, CPU inference, model verification, tests, and deployment docs.

## Scope

- 527 AudioSet multi-label acoustic event classes (speech, music, animals, machinery, environment, and more).
- MP3, WAV, FLAC, OGG, M4A, AAC, and WebM through FFmpeg.
- 32 kHz mono, 10-second windows, original EfficientAT log-mel preprocessing, sigmoid outputs, threshold/top-K results, segment timeline.
- No transcription, speaker identification, database, saved recordings, GPU, or user-supplied model URLs.
- One model loaded per service; `MODEL_NAME=mn10_as` default, `mn04_as` lightweight alternative.

## Run

Copy `.env.example` to `.env` for development or `.env.production.example` for deployment. Generate a unique service token with `openssl rand -hex 32`. The default ports are API **8007** (loopback) and UI **8088** (loopback or approved LAN).

```bash
docker compose --env-file .env config --quiet
docker compose --env-file .env up --build -d
docker compose ps -a
docker compose logs --tail=150 model-setup api ui
curl -fsS http://127.0.0.1:8007/health/ready
curl -fsS -H "X-API-Key: $API_TOKEN" -F "file=@sample.wav" http://127.0.0.1:8007/v1/classify
```

The one-shot model setup downloads from the pinned official EfficientAT `v0.0.1` release, checks asset size, and creates an integrity manifest. **Upstream release metadata does not contain a SHA256 digest.** Development bootstrapping can use trust-on-first-use; **production setup requires an independently verified `EXPECTED_MODEL_SHA256`**. The API checks SHA256 on every startup and uses `torch.load(weights_only=True)` with strict model state loading. Do not download arbitrary checkpoints.

The server production template binds `UI_BIND_IP=192.168.4.209` on port `8088`, so approved LAN/VPN users can open `http://192.168.4.209:8088` while the API stays bound to loopback `127.0.0.1:8007`. Ensure that IP exists on the Docker host, that the host firewall permits TCP/8088 from your approved networks, and that VPN routing allows reaching the subnet. Set the real `API_TOKEN` and separately verified `EXPECTED_MODEL_SHA256` in the server-only `.env` stored securely by the deployment team. Never commit credentials.

The frontend Nginx proxy injects `X-API-Key` server-side and proxies `/api/*` to the API. **This is service authentication, not per-user authentication.** Restrict ingress to approved LAN/VPN clients or use authenticated HTTPS ingress.

## Tests and rollout

```bash
python -m pip install -r backend/requirements-test.txt
PYTHONPATH=backend pytest -q backend/tests
cd frontend && npm install && npm run build
```

Model/CPU smoke tests require installing the matching CPU-only PyTorch stack and downloading weights. Test actual model loading, accuracy, p50/p95 latency, peak RSS and UI behavior on the target server before declaring production readiness. CPU: 2 cores and 1200 MB memory are provisional budgets.

See `docs/API.md`, `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, `docs/MODEL_PROVENANCE.md`, and `docs/TEST_PLAN.md`.

**CI is intentionally excluded.** Your deployment teammate owns `.gitlab-ci.yml`, server branches, runner, SSH credentials, and protected environment delivery.
