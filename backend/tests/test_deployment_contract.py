from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[3]

def test_service_names_and_volume_contract():
    compose=yaml.safe_load((ROOT/"docker-compose.yml").read_text())
    assert set(compose["services"])=={"model-setup","api","ui"}
    assert "model_cache:/models" in compose["services"]["model-setup"]["volumes"]
    assert "model_cache:/models:ro" in compose["services"]["api"]["volumes"]
    assert compose["services"]["api"]["depends_on"]["model-setup"]["condition"]=="service_completed_successfully"

def test_lan_ui_and_loopback_api():
    production=(ROOT/".env.production.example").read_text()
    assert "UI_BIND_IP=192.168.4.209" in production
    assert "UI_PORT=8088" in production
    assert "API_BIND_IP=127.0.0.1" in production
    assert "API_PORT=8007" in production
    assert "API_TOKEN=\n" in production
    assert not (ROOT/".gitlab-ci.yml").exists()

def test_nginx_proxy_does_not_expose_client_api_key():
    nginx=(ROOT/"ops/nginx.conf.template").read_text()
    assert 'proxy_set_header X-API-Key "${API_TOKEN}"' in nginx
    assert "proxy_pass http://$api_backend;" in nginx
    assert 'resolver 127.0.0.11' in nginx
    frontend=(ROOT/"frontend/src/App.tsx").read_text()
    assert "X-API-Key" not in frontend
    assert "fetch('/api/v1/classify'" in frontend
