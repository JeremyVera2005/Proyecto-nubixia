# syntax=docker/dockerfile:1
FROM node:24-alpine AS build
WORKDIR /build
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY angular.json tsconfig*.json ./
COPY src ./src
COPY public ./public
RUN npm run build -- --configuration production --base-href /

FROM nginx:stable-alpine AS runtime
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /build/dist/nubixia-web/browser /usr/share/nginx/html
COPY docker/config.json /usr/share/nginx/html/config.json
RUN chown -R nginx:nginx /etc/nginx/conf.d
ENV NGINX_ENVSUBST_FILTER="^NUBIXIA_API_KEY$"
USER nginx
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
