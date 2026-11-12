#!/bin/sh
set -eu
# Only replace the secret token; preserve Nginx runtime variables such as $host.
: "${API_TOKEN:?API_TOKEN must be set for Nginx API proxy}"
# All scratch paths are beneath the one writable tmpfs mount, /tmp.
# Create them as the unprivileged nginx user before validating the config.
mkdir -p /tmp/nginx-temp/client_body /tmp/nginx-temp/proxy \
  /tmp/nginx-temp/fastcgi /tmp/nginx-temp/uwsgi /tmp/nginx-temp/scgi
# Fail early with an actionable error if the host runtime denies tmpfs writes.
test -w /tmp/nginx-temp/client_body || { echo 'Nginx /tmp scratch directory is not writable' >&2; exit 1; }
envsubst '${API_TOKEN}' < /etc/nginx/nginx.conf.template > /tmp/nginx.conf
nginx -t -c /tmp/nginx.conf
exec nginx -c /tmp/nginx.conf -g 'daemon off;'
