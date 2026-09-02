FROM node:22-alpine AS frontend

WORKDIR /build
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
COPY web/package.json web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY web/ ./web/
RUN cd web && pnpm build

FROM dojo:latest

COPY --from=frontend /build/web/dist/ /share/dojo/
