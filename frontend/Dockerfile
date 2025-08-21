FROM node:20-slim AS build

WORKDIR /app

# Set environment variables for production build
ENV NODE_ENV=production \
    EXPO_USE_STATIC=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./
RUN npm ci --no-audit

# Copy source code
COPY . .

# Build the web application
RUN npx expo export --platform web --output-dir dist

# Production stage with nginx
FROM nginx:alpine

# Copy built application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy runtime configuration template
COPY public/config.js.template /usr/share/nginx/html/config.js.template

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy configuration generation script to nginx's entrypoint.d
COPY 40-generate-config.sh /docker-entrypoint.d/40-generate-config.sh
RUN chmod +x /docker-entrypoint.d/40-generate-config.sh

# Note: Running as root to allow entrypoint.d scripts to execute
# nginx will handle dropping privileges internally

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]