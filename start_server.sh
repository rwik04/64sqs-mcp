#!/bin/bash

# MCP Server Startup Script
echo "Starting MCP Server..."

# Check if server is already running
if pgrep -f "python src/server.py" > /dev/null; then
    echo "Server is already running!"
    echo "Killing existing server..."
    pkill -f "python src/server.py"
    sleep 2
fi

# Start the server in background
echo "Starting MCP server on port 8000 with 5-minute timeout..."
cd /home/rwik/code/mcp_server

# Set timeout environment variables
export UVICORN_TIMEOUT_KEEP_ALIVE=300
export UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN=30

poetry run python src/server.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Check if server started successfully
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ MCP Server started successfully (PID: $SERVER_PID)"
    echo "Server is running on: http://localhost:8000/mcp"
    echo ""
    echo "To expose to the world, run:"
    echo "  ngrok http 8000"
    echo ""
    echo "Or use nginx with the provided config:"
    echo "  sudo cp nginx.conf /etc/nginx/sites-available/mcp-server"
    echo "  sudo ln -s /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/"
    echo "  sudo nginx -t && sudo systemctl reload nginx"
else
    echo "❌ Failed to start MCP server"
    exit 1
fi

