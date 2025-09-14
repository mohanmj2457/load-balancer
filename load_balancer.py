#!/usr/bin/env python3
"""
Advanced Load Balancer Implementation
Supports multiple algorithms: Round Robin, Weighted Round Robin, Least Connections
"""

import time
import threading
import yaml
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import random
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoadBalancingAlgorithm(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"

@dataclass
class Server:
    name: str
    host: str
    port: int
    weight: int = 1
    health_check_path: str = "/health"
    enabled: bool = True
    healthy: bool = True
    active_connections: int = 0
    total_requests: int = 0
    last_health_check: float = 0.0
    response_times: List[float] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def health_url(self) -> str:
        return f"{self.url}{self.health_check_path}"
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

class LoadBalancer:
    def __init__(self, config_file: str = "config.yaml"):
        self.config = self._load_config(config_file)
        self.servers: List[Server] = []
        self.current_index = 0
        self.algorithm = LoadBalancingAlgorithm(self.config['load_balancer']['algorithm'])
        self.health_check_interval = self.config['load_balancer']['health_check_interval']
        self.timeout = self.config['load_balancer']['timeout']
        self.health_check_thread = None
        self.running = False
        
        self._initialize_servers()
        self._start_health_checking()
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
    
    def _initialize_servers(self):
        """Initialize servers from configuration"""
        for server_config in self.config['servers']:
            server = Server(
                name=server_config['name'],
                host=server_config['host'],
                port=server_config['port'],
                weight=server_config.get('weight', 1),
                health_check_path=server_config.get('health_check_path', '/health'),
                enabled=server_config.get('enabled', True)
            )
            self.servers.append(server)
            logger.info(f"Added server: {server.name} at {server.url}")
    
    def _start_health_checking(self):
        """Start health checking in a separate thread"""
        self.running = True
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
        logger.info("Health checking started")
    
    def _health_check_loop(self):
        """Continuous health checking loop"""
        while self.running:
            for server in self.servers:
                if server.enabled:
                    self._check_server_health(server)
            time.sleep(self.health_check_interval)
    
    def _check_server_health(self, server: Server):
        """Check health of a single server"""
        try:
            start_time = time.time()
            response = requests.get(server.health_url, timeout=5)
            response_time = time.time() - start_time
            
            server.healthy = response.status_code == 200
            server.last_health_check = time.time()
            
            # Track response time (keep last 10 measurements)
            server.response_times.append(response_time)
            if len(server.response_times) > 10:
                server.response_times.pop(0)
            
            status = "healthy" if server.healthy else "unhealthy"
            logger.debug(f"Health check for {server.name}: {status} (response time: {response_time:.3f}s)")
            
        except requests.RequestException as e:
            server.healthy = False
            server.last_health_check = time.time()
            logger.warning(f"Health check failed for {server.name}: {e}")
    
    def get_healthy_servers(self) -> List[Server]:
        """Get list of healthy and enabled servers"""
        return [server for server in self.servers if server.enabled and server.healthy]
    
    def select_server(self) -> Optional[Server]:
        """Select a server based on the configured algorithm"""
        healthy_servers = self.get_healthy_servers()
        
        if not healthy_servers:
            logger.warning("No healthy servers available")
            return None
        
        if len(healthy_servers) == 1:
            return healthy_servers[0]
        
        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin_selection(healthy_servers)
        elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(healthy_servers)
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_servers)
        elif self.algorithm == LoadBalancingAlgorithm.RANDOM:
            return random.choice(healthy_servers)
        else:
            return self._round_robin_selection(healthy_servers)
    
    def _round_robin_selection(self, servers: List[Server]) -> Server:
        """Round robin server selection"""
        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server
    
    def _weighted_round_robin_selection(self, servers: List[Server]) -> Server:
        """Weighted round robin server selection"""
        # Create a list with servers repeated according to their weight
        weighted_servers = []
        for server in servers:
            weighted_servers.extend([server] * server.weight)
        
        server = weighted_servers[self.current_index % len(weighted_servers)]
        self.current_index += 1
        return server
    
    def _least_connections_selection(self, servers: List[Server]) -> Server:
        """Select server with least active connections"""
        return min(servers, key=lambda s: s.active_connections)
    
    def forward_request(self, method: str, path: str, headers: Dict, data: Optional[bytes] = None) -> tuple:
        """Forward request to selected server"""
        server = self.select_server()
        
        if not server:
            return None, 503, "No healthy servers available"
        
        try:
            # Increment connection count
            server.active_connections += 1
            server.total_requests += 1
            
            # Prepare request
            url = f"{server.url}{path}"
            request_headers = dict(headers)
            
            # Remove hop-by-hop headers
            hop_by_hop_headers = [
                'connection', 'keep-alive', 'proxy-authenticate',
                'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade'
            ]
            for header in hop_by_hop_headers:
                request_headers.pop(header, None)
            
            # Forward request
            start_time = time.time()
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                data=data,
                timeout=self.timeout,
                allow_redirects=False
            )
            response_time = time.time() - start_time
            
            # Track response time
            server.response_times.append(response_time)
            if len(server.response_times) > 10:
                server.response_times.pop(0)
            
            logger.info(f"Request forwarded to {server.name}: {method} {path} -> {response.status_code} ({response_time:.3f}s)")
            
            return response, response.status_code, response.text
            
        except requests.RequestException as e:
            logger.error(f"Request failed to {server.name}: {e}")
            return None, 502, f"Bad Gateway: {str(e)}"
        
        finally:
            # Decrement connection count
            server.active_connections = max(0, server.active_connections - 1)
    
    def get_server_stats(self) -> Dict:
        """Get statistics for all servers"""
        stats = {
            'algorithm': self.algorithm.value,
            'total_servers': len(self.servers),
            'healthy_servers': len(self.get_healthy_servers()),
            'servers': []
        }
        
        for server in self.servers:
            server_stats = {
                'name': server.name,
                'url': server.url,
                'enabled': server.enabled,
                'healthy': server.healthy,
                'weight': server.weight,
                'active_connections': server.active_connections,
                'total_requests': server.total_requests,
                'avg_response_time': server.avg_response_time,
                'last_health_check': server.last_health_check
            }
            stats['servers'].append(server_stats)
        
        return stats
    
    def update_algorithm(self, algorithm: str):
        """Update load balancing algorithm"""
        try:
            self.algorithm = LoadBalancingAlgorithm(algorithm)
            self.current_index = 0  # Reset round robin index
            logger.info(f"Load balancing algorithm changed to: {algorithm}")
        except ValueError:
            logger.error(f"Invalid algorithm: {algorithm}")
    
    def toggle_server(self, server_name: str, enabled: bool):
        """Enable or disable a server"""
        for server in self.servers:
            if server.name == server_name:
                server.enabled = enabled
                logger.info(f"Server {server_name} {'enabled' if enabled else 'disabled'}")
                return True
        logger.warning(f"Server {server_name} not found")
        return False
    
    def shutdown(self):
        """Shutdown the load balancer"""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        logger.info("Load balancer shutdown complete")
