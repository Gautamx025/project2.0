FROM node:24-alpine
WORKDIR /app
COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/package.json
RUN npm ci
COPY frontend ./frontend
ENV NEXT_TELEMETRY_DISABLED=1
ENV BACKEND_URL=http://backend:8000
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
