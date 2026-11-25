# Multi-stage Docker build for InsightIQ AI React Frontend
# Stage 1: Build production static files with Vite
FROM node:20-alpine as builder

WORKDIR /app

COPY frontend/package.json ./
# If package-lock.json exists, copy it as well
COPY frontend/package*.json ./

RUN npm install

COPY frontend/ .

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL:-http://localhost:8000}

RUN npm run build

# Stage 2: Serve optimized assets with Nginx
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
