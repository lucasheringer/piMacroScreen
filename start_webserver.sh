#!/bin/bash

# Macro Keyboard Web Server Startup Script

echo "Starting Macro Keyboard Web Server..."
echo "======================================="
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Flask is not installed. Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Get the IP address
IP=$(hostname -I | awk '{print $1}')

echo "Server will be available at:"
echo "  Local:   http://localhost:5000"
echo "  Network: http://$IP:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================="
echo ""

# Start the web server
python3 webserver.py
