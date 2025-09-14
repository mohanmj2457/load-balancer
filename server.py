#!/usr/bin/env python3
"""
Simple HTTP Server for testing load balancer
"""

import time
import random
from flask import Flask, jsonify, request
import threading
import signal
import sys

class TestServer:
    def __init__(self, name, port, delay_range=(0.1, 0.5)):
        self.name = name
        self.port = port
        self.delay_range = delay_range
        self.app = Flask(name)
        self.setup_routes()
        self.healthy = True
        
    def setup_routes(self):
        @self.app.route('/')
        def home():
            # Simulate some processing time
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)
            
            return jsonify({
                'server': self.name,
                'port': self.port,
                'message': f'Hello from {self.name}!',
                'timestamp': time.time(),
                'delay': delay
            })
        
        @self.app.route('/health')
        def health():
            status = 'healthy' if self.healthy else 'unhealthy'
            return jsonify({
                'server': self.name,
                'status': status,
                'timestamp': time.time()
            }), 200 if self.healthy else 503
        
        @self.app.route('/toggle-health')
        def toggle_health():
            self.healthy = not self.healthy
            return jsonify({
                'server': self.name,
                'status': 'healthy' if self.healthy else 'unhealthy',
                'message': f'Health status toggled to {"healthy" if self.healthy else "unhealthy"}'
            })
        
        @self.app.route('/heavy')
        def heavy_task():
            # Simulate heavy processing
            time.sleep(2)
            return jsonify({
                'server': self.name,
                'message': 'Heavy task completed',
                'timestamp': time.time()
            })
    
    def run(self):
        print(f"Starting {self.name} on port {self.port}")
        self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)

def create_test_servers():
    """Create and start test servers"""
    servers = []
    
    # Create 3 test servers
    for i in range(1, 4):
        port = 8000 + i
        server = TestServer(f"server{i}", port)
        servers.append(server)
    
    # Start servers in separate threads
    threads = []
    for server in servers:
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(0.5)  # Stagger server starts
    
    return servers, threads

def signal_handler(sig, frame):
    print('\nShutting down servers...')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Creating test servers for load balancer...")
    servers, threads = create_test_servers()
    
    print("\nTest servers started:")
    print("- Server 1: http://127.0.0.1:8001")
    print("- Server 2: http://127.0.0.1:8002") 
    print("- Server 3: http://127.0.0.1:8003")
    print("\nEndpoints available on each server:")
    print("- GET / - Main endpoint")
    print("- GET /health - Health check")
    print("- GET /toggle-health - Toggle health status")
    print("- GET /heavy - Heavy task simulation")
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
