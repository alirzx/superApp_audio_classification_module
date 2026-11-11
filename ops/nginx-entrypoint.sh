#!/bin/sh
set -eu
envsubst '${API_TOKEN}' < /etc/nginx/nginx.conf.template > /tmp/nginx.conf
exec nginx -c /tmp/nginx.conf -g 'daemon off;'
