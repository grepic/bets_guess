FROM node:20-alpine

WORKDIR /app

COPY apps/web/package.json /app/package.json
RUN npm install

COPY apps/web/ /app/

ENV NEXT_PUBLIC_API_URL=http://localhost:8000

EXPOSE 3000

CMD ["npm", "run", "dev"]
