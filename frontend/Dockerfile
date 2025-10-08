# =============================================================================
# Stage 1: Development (Vite Dev Server)
# =============================================================================
FROM node:22-slim AS development

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# =============================================================================
# Stage 2: Build (Production Assets)
# =============================================================================
FROM node:22-slim AS build

WORKDIR /app

# Copy package files and install ALL dependencies (including devDependencies for build)
COPY package*.json ./
RUN npm ci && npm cache clean --force

# Copy application files
COPY . .

# Build the application (requires devDependencies like vite, rolldown, etc.)
RUN npm run build

# =============================================================================
# Stage 3: Production (Nginx + Static Files)
# =============================================================================
FROM nginx:alpine AS production

# Install gettext for envsubst (environment variable substitution)
RUN apk add --no-cache gettext

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy nginx template configuration
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy built static files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Create startup script that performs envsubst and starts nginx
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Substitute environment variables in nginx config' >> /docker-entrypoint.sh && \
    echo 'echo "Substituting environment variables in nginx configuration..."' >> /docker-entrypoint.sh && \
    echo 'envsubst "$(env | sed -e "s/=.*//" -e "s/^/\$/g")" < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Display the generated config for debugging' >> /docker-entrypoint.sh && \
    echo 'echo "Generated nginx configuration:"' >> /docker-entrypoint.sh && \
    echo 'cat /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Test nginx configuration' >> /docker-entrypoint.sh && \
    echo 'nginx -t' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Start nginx' >> /docker-entrypoint.sh && \
    echo 'echo "Starting nginx..."' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

EXPOSE 80

CMD ["/docker-entrypoint.sh"]