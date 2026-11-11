#!/bin/sh
# Run on the Docker host after deployment; never prints API_TOKEN.
set -eu
: "${UI_BIND_IP:=192.168.4.209}"
: "${UI_PORT:=8088}"
: "${API_PORT:=8007}"

echo "Validating Compose configuration..."
docker compose --env-file .env config --quiet
echo "Checking containers..."
docker compose --env-file .env ps -a
echo "Checking API readiness (host loopback)..."
curl --fail --silent --show-error --max-time 10 "http://127.0.0.1:${API_PORT}/health/ready"
printf '\n'
echo "Checking UI Nginx health on configured LAN binding..."
curl --fail --silent --show-error --max-time 10 "http://${UI_BIND_IP}:${UI_PORT}/healthz"
printf '\n'
echo "Checking UI-to-API reverse proxy health..."
curl --fail --silent --show-error --max-time 10 "http://${UI_BIND_IP}:${UI_PORT}/api/health/ready"
printf '\n'
echo "Checks finished. Real classification, remote VPN reachability, and benchmark still require acceptance testing."
