# REST API v1

All `/v1/*` and `/metrics` require `X-API-Key` when configured. Production settings reject missing or short tokens.

| Method | Path | Purpose |
|---|---|---|
| GET | /health/live | Process liveness |
| GET | /health/ready | Model initialized |
| GET | /v1/models | Allowlisted model information |
| GET | /v1/labels | 527 AudioSet labels |
| POST | /v1/classify | Multipart upload and audio classification |
| GET | /metrics | Prometheus metrics when enabled |

`POST /v1/classify` takes multipart `file`, optional `threshold` (0–1), optional `top_k` (1–50). Returns `schema_version=superapp.audio-classification.v1`, request ID, model/device, audio metadata, clip-level predictions, temporal segments, duration, processing time, warnings. Predictions contain `label_id`, `label`, and sigmoid `score` [0,1]. Scores are not calibrated probabilities or a softmax distribution. Final audio window is zero padded; segment timing references original audio duration.

Errors: 401 missing/invalid token, 413 declared oversize request, 422 invalid upload/controls, 503 queue timeout, 500 inference failure. Nginx independently enforces 22 MB upload bodies. No user audio is persisted.
