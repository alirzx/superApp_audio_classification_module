# syntax=docker/dockerfile:1.6
FROM node:22-alpine AS build
ARG NPM_REGISTRY_URL=https://registry.npmjs.org/
WORKDIR /app
COPY frontend/package*.json ./
RUN npm config set registry "$NPM_REGISTRY_URL" && npm install
COPY frontend/ ./
RUN npm run build
FROM nginx:1.29-alpine
RUN apk add --no-cache gettext && mkdir -p /tmp /var/cache/nginx /var/run && chown -R nginx:nginx /tmp /var/cache/nginx /var/run
COPY --from=build /app/dist /usr/share/nginx/html
COPY ops/nginx.conf.template /etc/nginx/nginx.conf.template
COPY ops/nginx-entrypoint.sh /entrypoint.sh
RUN chmod 0555 /entrypoint.sh
USER nginx
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
