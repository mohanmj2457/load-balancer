#!/bin/bash

# Load Balancer Demo Script
# This script starts the test servers and load balancer for demonstration

echo "🚀 Starting Load Balancer Demo"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import flask, requests, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing required packages..."
    pip3 install -r requirements.txt
fi

echo "✅ Dependencies ready"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down demo..."
    jobs -p | xargs -r kill
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo "🏗️  Starting test servers..."
python3 server.py &
SERVER_PID=$!

# Wait for servers to start
echo "⏳ Waiting for servers to start..."
sleep 3

echo ""
echo "🔄 Starting load balancer..."
python3 main.py &
LB_PID=$!

# Wait for load balancer to start
echo "⏳ Waiting for load balancer to start..."
sleep 2

echo ""
echo "✅ Demo is ready!"
echo "================================"
echo "🌐 Load Balancer: http://localhost:8080"
echo "📊 Dashboard: http://localhost:8080/admin/dashboard"
echo "📈 Stats API: http://localhost:8080/admin/stats"
echo ""
echo "🧪 Test servers running on:"
echo "   - http://localhost:8001"
echo "   - http://localhost:8002" 
echo "   - http://localhost:8003"
echo ""
echo "🔧 Quick tests:"
echo "   curl http://localhost:8080/"
echo "   curl http://localhost:8080/admin/stats"
echo ""
echo "Press Ctrl+C to stop the demo"

# Keep script running
wait
