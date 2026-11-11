#!/bin/sh
set -eu
# Only replace the secret token; preserve Nginx runtime variables such as $host.
: "${API_TOKEN:?API_TOKEN must be set for Nginx API proxy}"
envsubst '${API_TOKEN}' < /etc/nginx/nginx.conf.template > /tmp/nginx.conf
nginx -t -c /tmp/nginx.conf
exec nginx -c /tmp/nginx.conf -g 'daemon off;'
