# Use node base for building
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy codebase
COPY . .

# Build the React static files
ARG VITE_API_URL
ARG VITE_API_KEY
ARG VITE_TENANT_NAME

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_KEY=$VITE_API_KEY
ENV VITE_TENANT_NAME=$VITE_TENANT_NAME

RUN npm run build

# Use Nginx to serve static files in production stage
FROM nginx:alpine

# Copy built static files to Nginx HTML directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
