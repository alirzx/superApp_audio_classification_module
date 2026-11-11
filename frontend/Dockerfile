# syntax=docker/dockerfile:1.6
FROM docker.arvancloud.ir/node:22-alpine AS build
ARG NPM_REGISTRY_URL=https://package-mirror.liara.ir/repository/npm/
ARG NPM_FALLBACK_REGISTRY_URL=https://registry.npmjs.org/
WORKDIR /app
COPY frontend/package*.json ./
RUN set -eu; \
    if npm install --registry="$NPM_REGISTRY_URL" --fetch-retries=2 --fetch-timeout=90000 --no-audit --no-fund; then \
      echo 'npm primary mirror succeeded'; \
    else \
      rm -rf node_modules package-lock.json; \
      npm install --registry="$NPM_FALLBACK_REGISTRY_URL" --fetch-retries=2 --fetch-timeout=90000 --no-audit --no-fund; \
    fi
COPY frontend/ ./
RUN npm run build

FROM docker.arvancloud.ir/nginx:1.27-alpine
ARG APK_PRIMARY_MIRROR_URL=https://linux-mirror.liara.ir/repository/alpine
ARG APK_FALLBACK_MIRROR_URL=https://mirrors.huaweicloud.com/alpine
RUN set -eu; \
    version="$(cut -d. -f1-2 /etc/alpine-release)"; \
    for mirror in "$APK_PRIMARY_MIRROR_URL" "$APK_FALLBACK_MIRROR_URL"; do \
      case "$mirror" in https://*) ;; *) echo 'APK mirrors must use HTTPS' >&2; exit 2;; esac; \
      printf '%s/v%s/main\n%s/v%s/community\n' "$mirror" "$version" "$mirror" "$version" > /etc/apk/repositories; \
      if apk add --no-cache gettext; then break; fi; \
    done; \
    command -v envsubst >/dev/null || { echo 'gettext installation failed' >&2; exit 1; }; \
    mkdir -p /tmp /var/cache/nginx /var/run && chown -R nginx:nginx /tmp /var/cache/nginx /var/run
COPY --from=build /app/dist /usr/share/nginx/html
COPY ops/nginx.conf.template /etc/nginx/nginx.conf.template
COPY ops/nginx-entrypoint.sh /entrypoint.sh
RUN chmod 0555 /entrypoint.sh
USER nginx
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
