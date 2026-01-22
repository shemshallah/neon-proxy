#!/bin/bash
# start.sh
echo "🚀 Starting Neon Proxy..."
echo "Environment variables:"
printenv | grep -E "(NEON|PORT|RAILWAY)" || echo "No env vars found"

# Wait a moment for environment to be ready
sleep 2

# Start the application
exec gunicorn neon_proxy:app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug