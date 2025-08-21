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
COPY 30-generate-config.sh /docker-entrypoint.d/30-generate-config.sh
RUN chmod +x /docker-entrypoint.d/30-generate-config.sh

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Set proper permissions (must be done before switching user)
RUN chown -R nextjs:nodejs /usr/share/nginx/html && \
    chown -R nextjs:nodejs /var/cache/nginx && \
    chown -R nextjs:nodejs /var/log/nginx && \
    chown -R nextjs:nodejs /etc/nginx/conf.d && \
    chown -R nextjs:nodejs /docker-entrypoint.d/
    
# Create pid file directory
RUN touch /var/run/nginx.pid && \
    chown -R nextjs:nodejs /var/run/nginx.pid

USER nextjs

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]