#!/bin/sh
# This script runs as part of nginx's entrypoint.d system

set -e

echo "🔧 Starting configuration generation..."

# Generate runtime configuration from template
if [ -f /usr/share/nginx/html/config.js.template ]; then
    echo "🔧 Generating runtime configuration..."
    echo "API_URL: ${API_URL:-http://localhost:8000/api/v1}"
    echo "NODE_ENV: ${NODE_ENV:-production}"
    
    # Use envsubst to replace environment variables in template
    envsubst '${API_URL} ${NODE_ENV}' < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js
    
    echo "✅ Runtime configuration generated successfully"
    cat /usr/share/nginx/html/config.js
    
    # Inject config script into HTML files
    for html_file in /usr/share/nginx/html/*.html; do
        if [ -f "$html_file" ]; then
            echo "🔧 Injecting config script into $html_file"
            # Add config script before closing </head> tag
            sed -i 's|</head>|<script src="/config.js"></script></head>|g' "$html_file"
        fi
    done
else
    echo "⚠️  No config template found, using build-time defaults"
fi

echo "✅ Configuration generation complete"