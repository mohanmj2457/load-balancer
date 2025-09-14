@echo off
REM Load Balancer Demo Script for Windows
REM This script starts the test servers and load balancer for demonstration

echo Starting Load Balancer Demo
echo ================================

REM Start the backend servers in new windows
start cmd /k "python server.py server1 8001"
start cmd /k "python server.py server2 8002"
start cmd /k "python server.py server3 8003"

REM Wait a moment for servers to start
timeout /t 5

REM Start the load balancer
python main.py
