#!/bin/bash
# This script runs as part of nginx's entrypoint.d system

set -e

echo "40-generate-config.sh: Starting configuration generation..."

# Generate runtime configuration from template
if [ -f /usr/share/nginx/html/config.js.template ]; then
    echo "40-generate-config.sh: Generating runtime configuration..."
    echo "40-generate-config.sh: API_URL: ${API_URL:-http://localhost:8000/api/v1}"
    echo "40-generate-config.sh: NODE_ENV: ${NODE_ENV:-production}"
    
    # Use envsubst to replace environment variables in template
    envsubst '${API_URL} ${NODE_ENV}' < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js
    
    echo "40-generate-config.sh: Runtime configuration generated successfully"
    echo "40-generate-config.sh: Generated config.js content:"
    cat /usr/share/nginx/html/config.js
    
    # Inject config script into HTML files
    for html_file in /usr/share/nginx/html/*.html; do
        if [ -f "$html_file" ]; then
            echo "40-generate-config.sh: Injecting config script into $html_file"
            # Add config script before closing </head> tag
            sed -i 's|</head>|<script src="/config.js"></script></head>|g' "$html_file"
        fi
    done
else
    echo "40-generate-config.sh: No config template found, using build-time defaults"
fi

echo "40-generate-config.sh: Configuration generation complete"