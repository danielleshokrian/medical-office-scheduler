# Build stage

FROM node:18-alpine AS build

 

WORKDIR /app

 

# Copy package files

COPY package*.json ./

 

# Install dependencies

RUN npm ci --only=production

 

# Copy source code

COPY . .

 

# Build argument for API URL

ARG REACT_APP_API_URL

ENV REACT_APP_API_URL=$REACT_APP_API_URL

 

# Build for production

RUN npm run build

 

# Production stage - use Nginx to serve static files

FROM nginx:alpine

 

# Copy built files from build stage

COPY --from=build /app/build /usr/share/nginx/html

 

# Copy nginx configuration

COPY nginx.conf /etc/nginx/conf.d/default.conf

 

# Create directory for SSL certificates

RUN mkdir -p /etc/nginx/ssl

 

# Expose ports

EXPOSE 80 443

 

# Health check

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \

    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

 

# Start Nginx

CMD ["nginx", "-g", "daemon off;"]