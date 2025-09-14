## Run this script with: python main.py (Windows)
"""
Main Load Balancer Application
"""

import time
import signal
import sys
from flask import Flask, request, jsonify, render_template_string
from load_balancer import LoadBalancer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import time
import signal
import sys
from flask import Flask, request, jsonify, render_template_string
from load_balancer import LoadBalancer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Landing page template with navigation buttons
LANDING_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Load Balancer Portal</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 0; }
        .container { max-width: 400px; margin: 100px auto; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 40px 32px 32px 32px; text-align: center; }
        h1 { color: #5a67d8; font-size: 2em; margin-bottom: 30px; }
        .nav-btn { display: block; width: 100%; background: #667eea; color: #fff; border: none; border-radius: 8px; padding: 18px 0; font-size: 1.1em; font-weight: 600; margin-bottom: 18px; cursor: pointer; transition: background 0.2s; text-decoration: none; }
        .nav-btn:last-child { margin-bottom: 0; }
        .nav-btn:hover { background: #5a67d8; }
        .icon { font-size: 1.3em; margin-right: 10px; vertical-align: middle; }
    </style>
</head>
<body>
    <div class='container'>
        <h1>Load Balancer Portal</h1>
        <a href='/user' class='nav-btn'><span class='icon'>👤</span>User Status Page</a>
        <a href='/admin/dashboard' class='nav-btn'><span class='icon'>🛠️</span>Admin Dashboard</a>
    </div>
</body>
"""

# User status template
USER_STATUS_TEMPLATE = """
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>User Status</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 60px auto; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 40px 32px 32px 32px; text-align: center; }
        h1 { color: #5a67d8; font-size: 2em; margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px 16px; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; color: #5a67d8; font-weight: 600; }
        tr:last-child td { border-bottom: none; }
    </style>
</head>
<body>
    <div class='container'>
        <h1>Backend Server Status</h1>
        <table>
            <thead>
                <tr><th>Server</th><th>Status</th><th>Active Connections</th><th>Total Requests</th></tr>
            </thead>
            <tbody>
            {% for server in stats.servers %}
                <tr>
                    <td>{{ server.name }}</td>
                    <td>{{ 'Healthy' if server.healthy else 'Unhealthy' }}</td>
                    <td>{{ server.active_connections }}</td>
                    <td>{{ server.total_requests }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</body>
"""

class LoadBalancerApp:
    def __init__(self, config_file="config.yaml"):
        self.load_balancer = LoadBalancer(config_file)
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/', methods=['GET'])
        def landing_page():
            return render_template_string(LANDING_PAGE_TEMPLATE)

        @self.app.route('/user', methods=['GET'])
        def user_status():
            return render_template_string(USER_STATUS_TEMPLATE, stats=self.load_balancer.get_server_stats())

        @self.app.route('/admin/dashboard')
        def dashboard():
            return render_template_string(DASHBOARD_TEMPLATE)

        @self.app.route('/admin/stats')
        def get_stats():
            return jsonify(self.load_balancer.get_server_stats())

        @self.app.route('/admin/algorithm/<algorithm>', methods=['POST'])
        def change_algorithm(algorithm):
            self.load_balancer.update_algorithm(algorithm)
            return jsonify({'message': f'Algorithm changed to {algorithm}'})

        @self.app.route('/admin/server/<server_name>/<action>', methods=['POST'])
        def manage_server(server_name, action):
            if action == 'enable':
                success = self.load_balancer.toggle_server(server_name, True)
            elif action == 'disable':
                success = self.load_balancer.toggle_server(server_name, False)
            else:
                return jsonify({'error': 'Invalid action'}), 400
            if success:
                return jsonify({'message': f'Server {server_name} {action}d'})
            else:
                return jsonify({'error': 'Server not found'}), 404


    def run(self, host="0.0.0.0", port=8080):
        """Run the load balancer"""
        logger.info(f"Starting Load Balancer on {host}:{port}")
        logger.info(f"Algorithm: {self.load_balancer.algorithm.value}")
        logger.info(f"Backend servers: {len(self.load_balancer.servers)}")
        try:
            self.app.run(host=host, port=port, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            logger.info("Shutting down load balancer...")
            self.load_balancer.shutdown()

# HTML Dashboard Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Load Balancer Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .servers-table {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        .status {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status.healthy {
            background-color: #d4edda;
            color: #155724;
        }
        .status.unhealthy {
            background-color: #f8d7da;
            color: #721c24;
        }
        .status.disabled {
            background-color: #e2e3e5;
            color: #383d41;
        }
        .controls {
            margin: 20px 0;
            text-align: center;
        }
        .btn {
            background-color: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background-color: #5a6fd8;
        }
        .btn.danger {
            background-color: #dc3545;
        }
        .btn.danger:hover {
            background-color: #c82333;
        }
        .refresh-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #28a745;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Load Balancer Dashboard</h1>
            <p>Real-time monitoring and management</p>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Stats will be populated by JavaScript -->
        </div>
        
        <div class="controls">
            <h3>Load Balancing Algorithm</h3>
            <button class="btn" onclick="changeAlgorithm('round_robin')">Round Robin</button>
            <button class="btn" onclick="changeAlgorithm('weighted_round_robin')">Weighted Round Robin</button>
            <button class="btn" onclick="changeAlgorithm('least_connections')">Least Connections</button>
            <button class="btn" onclick="changeAlgorithm('random')">Random</button>
        </div>
        
        <div class="servers-table">
            <table>
                <thead>
                    <tr>
                        <th>Server</th>
                        <th>URL</th>
                        <th>Status</th>
                        <th>Weight</th>
                        <th>Active Connections</th>
                        <th>Total Requests</th>
                        <th>Avg Response Time</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="serversTable">
                    <!-- Server data will be populated by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄</button>
    
    <script>
        function refreshData() {
            fetch('/admin/stats')
                .then(response => response.json())
                .then(data => {
                    updateStats(data);
                    updateServersTable(data);
                })
                .catch(error => console.error('Error:', error));
        }
        
        function updateStats(data) {
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${data.algorithm}</div>
                    <div class="stat-label">Current Algorithm</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.total_servers}</div>
                    <div class="stat-label">Total Servers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.healthy_servers}</div>
                    <div class="stat-label">Healthy Servers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.servers.reduce((sum, s) => sum + s.total_requests, 0)}</div>
                    <div class="stat-label">Total Requests</div>
                </div>
            `;
        }
        
        function updateServersTable(data) {
            const tbody = document.getElementById('serversTable');
            tbody.innerHTML = data.servers.map(server => `
                <tr>
                    <td><strong>${server.name}</strong></td>
                    <td>${server.url}</td>
                    <td>
                        <span class="status ${getStatusClass(server)}">
                            ${getStatusText(server)}
                        </span>
                    </td>
                    <td>${server.weight}</td>
                    <td>${server.active_connections}</td>
                    <td>${server.total_requests}</td>
                    <td>${server.avg_response_time.toFixed(3)}s</td>
                    <td>
                        ${server.enabled ? 
                            `<button class="btn danger" onclick="toggleServer('${server.name}', 'disable')">Disable</button>` :
                            `<button class="btn" onclick="toggleServer('${server.name}', 'enable')">Enable</button>`
                        }
                    </td>
                </tr>
            `).join('');
        }
        
        function getStatusClass(server) {
            if (!server.enabled) return 'disabled';
            return server.healthy ? 'healthy' : 'unhealthy';
        }
        
        function getStatusText(server) {
            if (!server.enabled) return 'Disabled';
            return server.healthy ? 'Healthy' : 'Unhealthy';
        }
        
        function changeAlgorithm(algorithm) {
            fetch(`/admin/algorithm/${algorithm}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshData();
                })
                .catch(error => console.error('Error:', error));
        }
        
        function toggleServer(serverName, action) {
            fetch(`/admin/server/${serverName}/${action}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshData();
                })
                .catch(error => console.error('Error:', error));
        }
        
        // Initial data load
        refreshData();
    </script>
</html>
"""

if __name__ == "__main__":
    app = LoadBalancerApp()
    app.run()
"""

if __name__ == "__main__":
    app = LoadBalancerApp()
    app.run()
"""
