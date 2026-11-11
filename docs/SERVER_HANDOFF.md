# SuperApp Module 07: Deployment handoff (server 192.168.4.209)

## Server `.env` contract

Keep the real `.env` out of Git. The deployment teammate controls GitLab CI and protected secrets. Begin from `.env.production.example` and set:

```dotenv
APP_ENV=production
API_BIND_IP=127.0.0.1
API_PORT=8007
UI_BIND_IP=192.168.4.209
UI_PORT=8088
MODEL_NAME=mn10_as
API_TOKEN=<32-byte-random-hex-token>
EXPECTED_MODEL_SHA256=<independently-verified-64-hex-checkpoint-digest>
```

Generate a unique token using `openssl rand -hex 32` on a trusted machine. Do **not** share production secrets in chat, terminal command arguments or repository history. The deployed UI is reachable at `http://192.168.4.209:8088` from approved LAN and VPN networks **only if** that address is configured on the server NIC, TCP port 8088 is allowed by host/network firewalls and the VPN routes into the server network. Consider authenticated HTTPS reverse-proxy ingress for wider use.

The API is bound to host loopback `127.0.0.1:8007`, reachable to Nginx through Docker service DNS `api:8000`. The browser talks to `/api/` on the UI origin; Nginx injects the service API key server-side. This is **not user login**. Anyone with permitted network access to the UI can access the inference service.

## Model initialization and cache

1. Named Docker volume `model_cache` persists across container updates and `docker compose down` (without `-v`). Do not delete it unless intentionally forcing model bootstrap.
2. `model-setup` runs as a one-shot privileged-volume initializer with all capabilities dropped and `no-new-privileges`. It downloads the allowlisted EfficientAT `v0.0.1` MN10 asset once, validates expected asset length and production SHA256, writes a manifest, and exits successfully. The API uses UID 10001 and mounts `model_cache:/models:ro`; cache files are readable by that UID.
3. On later deployments `model-setup` verifies the cached checksum and exits without network download. If cached artifacts are corrupted or mismatch the configured model/digest, startup fails closed. Do not automatically delete the volume or replace checkpoint bytes on error.
4. MN04 uses a separate filename and manifest; switching `MODEL_NAME` requires the associated independent checksum and a deployment restart.
5. Upstream GitHub release metadata does not publish SHA256. Obtain the digest through a separately trusted verification process before production bootstrap. Merely hashing a newly downloaded untrusted file is **not independent provenance verification**.

## Validation on the server

```bash
cp .env.production.example .env
# Edit .env privately to set APP_ENV, independent SHA256 and API_TOKEN; permissions 600
chmod 600 .env
docker compose --env-file .env config --quiet
docker compose --env-file .env up --build -d
docker compose --env-file .env ps -a
docker compose --env-file .env logs --tail=150 model-setup api ui
# From project root, with .env loaded into the current shell for nonsecret network values:
set -a; . ./.env; set +a
sh ops/verify-deployment.sh
# Run a real inference sample via the UI proxy:
curl --fail --show-error -F file=@sample.wav "http://192.168.4.209:8088/api/v1/classify"
```

Verify logs show `model-setup` exited zero, API `/health/ready` 200, UI `/healthz` 200, and a real known audio file produces a sensible response. Check a second `docker compose up -d` performs **no new download**. Check from an approved remote LAN/VPN client rather than only the server. Measure p50/p95 inference latency and peak RSS on actual host CPU; 1200 MB API memory is provisional.

## Supply chain and open work

Only the code and configuration are committed. No real checkpoint weights or credentials are stored. Docker builds, full PyTorch model loading, frontend npm install, and real CPU benchmark must run in a networked deployment environment. A frontend npm lockfile is not yet committed. Do not claim production acceptance before these checks pass.

The GitLab CI pipeline is tracked in `.gitlab-ci.yml` and owned by the deployment teammate. The prebuild hardening preserves its contents unchanged. The existing CI uses `sshpass` password-based SSH and dynamically collected `ssh-keyscan` host keys; these are operational security risks. Before broader deployment, the CI owner should move to pinned host keys, SSH key-based authentication, and an explicit post-deployment readiness gate. The deployed checkout path is `/home/deb/new-aiservices/audio-classification` and the deploy branch is `master`. Never print `.env` or credentials in logs. Runtime configuration remains distinct from CI variables. Do not copy CI assumptions from another module.
