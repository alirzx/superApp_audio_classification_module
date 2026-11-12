from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]

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
    # GitLab CI is teammate-owned and retained unchanged by the prebuild hardening.
    assert (ROOT/".gitlab-ci.yml").is_file()
    ci=(ROOT/".gitlab-ci.yml").read_text()
    assert "only:" in ci and "- master" in ci
    assert "audio-classification/.env" in ci

def test_nginx_proxy_does_not_expose_client_api_key():
    nginx=(ROOT/"ops/nginx.conf.template").read_text()
    assert 'proxy_set_header X-API-Key "${API_TOKEN}"' in nginx
    assert "proxy_pass http://$api_backend;" in nginx
    assert 'resolver 127.0.0.11' in nginx
    frontend=(ROOT/"frontend/src/App.tsx").read_text()
    assert "X-API-Key" not in frontend
    assert "fetch('/api/v1/classify'" in frontend

def test_tmpfs_mounts_are_structured_and_absolute():
    compose=yaml.safe_load((ROOT/"docker-compose.yml").read_text())
    api_mounts=compose["services"]["api"]["volumes"]
    ui_mounts=compose["services"]["ui"]["volumes"]
    api_tmpfs=[m for m in api_mounts if isinstance(m,dict) and m.get("type")=="tmpfs"]
    ui_tmpfs=[m for m in ui_mounts if isinstance(m,dict) and m.get("type")=="tmpfs"]
    assert [m["target"] for m in api_tmpfs]==["/tmp"]
    assert [m["target"] for m in ui_tmpfs]==["/tmp"]
    assert ui_tmpfs[0]["tmpfs"]["size"]>=32*1024*1024
    for mount in api_tmpfs + ui_tmpfs:
        assert mount["target"].startswith("/")
        assert mount["tmpfs"]["size"]>0
        # Omitted mode uses Docker default 01777. Numeric 1777 is decimal and
        # can mount as 03361, leaving non-root users unable to write.
        assert "mode" not in mount["tmpfs"]
    assert not any("nosuid" in str(m) for m in api_mounts + ui_mounts)

def test_nginx_scratch_paths_inside_writable_tmpfs():
    compose=yaml.safe_load((ROOT/"docker-compose.yml").read_text())
    ui=compose["services"]["ui"]
    assert ui["read_only"] is True
    assert ui["cap_drop"]==["ALL"]
    assert all(
        isinstance(m,dict) and m["target"]=="/tmp"
        for m in ui["volumes"]
    )
    nginx=(ROOT/"ops/nginx.conf.template").read_text()
    for temp_path in ("client_body","proxy","fastcgi","uwsgi","scgi"):
        assert f"/tmp/nginx-temp/{temp_path}" in nginx
    assert "/var/cache/nginx" not in nginx
    assert "proxy_request_buffering off;" in nginx
    assert "pid /tmp/nginx.pid;" in nginx
    entrypoint=(ROOT/"ops/nginx-entrypoint.sh").read_text()
    assert "mkdir -p /tmp/nginx-temp/client_body" in entrypoint
    assert "nginx -t -c /tmp/nginx.conf" in entrypoint
