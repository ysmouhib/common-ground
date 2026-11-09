# syntax=docker/dockerfile:1
# Self-contained image: built from source, no secret inside, runs as an unprivileged user.
# Configuration is given at run time:  docker run --env-file .env -p 3000:3000 common-ground
# (not yet built in CI: check it once on your machine before relying on it)

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:22-alpine
ENV NODE_ENV=production PORT=3000
WORKDIR /app
COPY --from=build /app/package.json ./
COPY --from=build /app/dist ./dist
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:3000/api/trpc/ping || exit 1
CMD ["node", "dist/boot.js"]
