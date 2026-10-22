FROM node:24.22.0-bookworm-slim
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm install --global pnpm@11.25.0
WORKDIR /app/apps/web
RUN chown node:node /app/apps/web
USER node
COPY --chown=node:node apps/web/package.json apps/web/pnpm-lock.yaml apps/web/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY --chown=node:node apps/web/ ./
RUN pnpm build
EXPOSE 3000
CMD ["node", "node_modules/next/dist/bin/next", "start", "--hostname", "0.0.0.0", "--port", "3000"]
