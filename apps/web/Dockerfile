FROM node:20-alpine AS base

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* /app/
RUN npm install

COPY apps/web/ /app/

ENV NEXT_PUBLIC_API_URL=http://localhost:8000

EXPOSE 3000

# Development target (default)
FROM base AS dev
CMD ["npm", "run", "dev"]

# Production target
FROM base AS prod
RUN npm run build
CMD ["npm", "start"]
