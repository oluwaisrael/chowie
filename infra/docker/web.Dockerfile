FROM node:24-slim AS build
WORKDIR /app
RUN npm install -g pnpm@11.11.0
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml turbo.json ./
COPY apps/storefront ./apps/storefront
RUN pnpm install --frozen-lockfile
ARG API_INTERNAL_URL=http://api:8000
ENV API_INTERNAL_URL=$API_INTERNAL_URL
RUN pnpm build
FROM node:24-slim
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
COPY --from=build --chown=node:node /app/apps/storefront/.next/standalone ./
COPY --from=build --chown=node:node /app/apps/storefront/.next/static ./apps/storefront/.next/static
COPY --from=build --chown=node:node /app/apps/storefront/public ./apps/storefront/public
USER node
EXPOSE 3000
CMD ["node", "apps/storefront/server.js"]
