# Use OpenResty as base (Nginx + Lua)
FROM openresty/openresty:alpine

# Install additional tools
RUN apk add --no-cache \
    curl \
    bash \
    openssl

# Install lua-resty-jwt for JWT validation
RUN /usr/local/openresty/luajit/bin/luarocks install lua-resty-jwt

# Create necessary directories
RUN mkdir -p /etc/nginx/lua \
    && mkdir -p /usr/share/nginx/html/swagger \
    && mkdir -p /usr/share/nginx/html/api-docs

# Copy Nginx configuration
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf

# Copy Lua scripts
COPY lua/ /etc/nginx/lua/

# Copy Swagger UI files (if you have them)
COPY swagger/ /usr/share/nginx/html/swagger/

# Copy API documentation files
COPY api-docs/ /usr/share/nginx/html/api-docs/

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start Nginx
CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]