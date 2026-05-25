FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .

ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

# Lock NODE_ENV to production at build time so dev-only UI branches are stripped from the bundle.
ENV NODE_ENV=production

RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
