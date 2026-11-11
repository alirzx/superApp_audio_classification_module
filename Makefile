.PHONY: doctor build up model ps logs ready down test frontend-build smoke
COMPOSE=docker compose --env-file .env
doctor:
	$(COMPOSE) config --quiet
build:
	$(COMPOSE) build
model:
	$(COMPOSE) run --rm model-setup
up:
	$(COMPOSE) up --build -d
ps:
	$(COMPOSE) ps -a
logs:
	$(COMPOSE) logs --tail=150 model-setup api ui
ready:
	curl -fsS http://127.0.0.1:${API_PORT:-8007}/health/ready
down:
	$(COMPOSE) down
test:
	PYTHONPATH=backend pytest -q backend/tests
frontend-build:
	cd frontend && npm install && npm run build
smoke:
	PYTHONPATH=backend python -m scripts.smoke "$(AUDIO)"
