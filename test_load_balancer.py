#!/usr/bin/env python3
"""
Test script for the load balancer
"""

import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor

def test_basic_requests():
    """Test basic load balancer functionality"""
    print("🧪 Testing basic load balancer functionality...")
    
    # Test multiple requests
    for i in range(5):
        try:
            response = requests.get("http://localhost:8080/", timeout=5)
            data = response.json()
            print(f"Request {i+1}: {data['server']} - {data['message']}")
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    print("✅ Basic requests test completed\n")

def test_algorithm_switching():
    """Test switching between different algorithms"""
    print("🔄 Testing algorithm switching...")
    
    algorithms = ["round_robin", "weighted_round_robin", "least_connections", "random"]
    
    for algorithm in algorithms:
        print(f"Switching to {algorithm}...")
        try:
            response = requests.post(f"http://localhost:8080/admin/algorithm/{algorithm}")
            print(f"Response: {response.json()}")
            
            # Test a few requests with new algorithm
            for i in range(3):
                resp = requests.get("http://localhost:8080/")
                data = resp.json()
                print(f"  {algorithm}: {data['server']}")
            
        except Exception as e:
            print(f"Error switching to {algorithm}: {e}")
    
    print("✅ Algorithm switching test completed\n")

def test_server_management():
    """Test enabling/disabling servers"""
    print("🔧 Testing server management...")
    
    try:
        # Get initial stats
        stats = requests.get("http://localhost:8080/admin/stats").json()
        print(f"Initial healthy servers: {stats['healthy_servers']}")
        
        # Disable a server
        print("Disabling server1...")
        response = requests.post("http://localhost:8080/admin/server/server1/disable")
        print(f"Response: {response.json()}")
        
        # Check stats after disabling
        stats = requests.get("http://localhost:8080/admin/stats").json()
        print(f"Healthy servers after disabling: {stats['healthy_servers']}")
        
        # Re-enable the server
        print("Re-enabling server1...")
        response = requests.post("http://localhost:8080/admin/server/server1/enable")
        print(f"Response: {response.json()}")
        
        # Check stats after re-enabling
        stats = requests.get("http://localhost:8080/admin/stats").json()
        print(f"Healthy servers after re-enabling: {stats['healthy_servers']}")
        
    except Exception as e:
        print(f"Error in server management test: {e}")
    
    print("✅ Server management test completed\n")

def test_concurrent_requests():
    """Test concurrent requests to see load distribution"""
    print("⚡ Testing concurrent requests...")
    
    def make_request(request_id):
        try:
            response = requests.get("http://localhost:8080/", timeout=10)
            data = response.json()
            return f"Request {request_id}: {data['server']}"
        except Exception as e:
            return f"Request {request_id} failed: {e}"
    
    # Make 20 concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(20)]
        results = [future.result() for future in futures]
    
    # Count server distribution
    server_counts = {}
    for result in results:
        if "server" in result:
            server = result.split(": ")[1]
            server_counts[server] = server_counts.get(server, 0) + 1
    
    print("Server distribution:")
    for server, count in server_counts.items():
        print(f"  {server}: {count} requests")
    
    print("✅ Concurrent requests test completed\n")

def test_health_checking():
    """Test health checking functionality"""
    print("🏥 Testing health checking...")
    
    try:
        # Get initial stats
        stats = requests.get("http://localhost:8080/admin/stats").json()
        print("Initial server status:")
        for server in stats['servers']:
            print(f"  {server['name']}: {'Healthy' if server['healthy'] else 'Unhealthy'}")
        
        # Simulate server failure by toggling health
        print("\nSimulating server1 failure...")
        requests.get("http://localhost:8001/toggle-health")
        
        # Wait for health check to detect the failure
        print("Waiting for health check to detect failure...")
        time.sleep(6)
        
        # Check stats after failure
        stats = requests.get("http://localhost:8080/admin/stats").json()
        print("Server status after failure:")
        for server in stats['servers']:
            print(f"  {server['name']}: {'Healthy' if server['healthy'] else 'Unhealthy'}")
        
        # Restore server health
        print("\nRestoring server1 health...")
        requests.get("http://localhost:8001/toggle-health")
        
        # Wait for health check to detect recovery
        time.sleep(6)
        
        # Check stats after recovery
        stats = requests.get("http://localhost:8080/admin/stats").json()
        print("Server status after recovery:")
        for server in stats['servers']:
            print(f"  {server['name']}: {'Healthy' if server['healthy'] else 'Unhealthy'}")
        
    except Exception as e:
        print(f"Error in health checking test: {e}")
    
    print("✅ Health checking test completed\n")

def test_heavy_requests():
    """Test handling of heavy requests"""
    print("🏋️ Testing heavy requests...")
    
    def make_heavy_request(request_id):
        start_time = time.time()
        try:
            response = requests.get("http://localhost:8080/heavy", timeout=15)
            end_time = time.time()
            data = response.json()
            return f"Request {request_id}: {data['server']} (took {end_time - start_time:.2f}s)"
        except Exception as e:
            return f"Request {request_id} failed: {e}"
    
    # Make 3 concurrent heavy requests
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_heavy_request, i) for i in range(3)]
        results = [future.result() for future in futures]
    
    for result in results:
        print(f"  {result}")
    
    print("✅ Heavy requests test completed\n")

def main():
    """Run all tests"""
    print("🚀 Starting Load Balancer Tests\n")
    print("Make sure the load balancer and test servers are running!")
    print("Load balancer: http://localhost:8080")
    print("Test servers: http://localhost:8001, 8002, 8003\n")
    
    # Wait a moment for user to read
    time.sleep(2)
    
    try:
        # Test basic connectivity
        response = requests.get("http://localhost:8080/admin/stats", timeout=5)
        print("✅ Load balancer is accessible\n")
    except Exception as e:
        print(f"❌ Cannot connect to load balancer: {e}")
        print("Please make sure the load balancer is running on port 8080")
        return
    
    # Run all tests
    test_basic_requests()
    test_algorithm_switching()
    test_server_management()
    test_concurrent_requests()
    test_health_checking()
    test_heavy_requests()
    
    print("🎉 All tests completed!")
    print("\nYou can also:")
    print("- Visit http://localhost:8080/admin/dashboard for the web dashboard")
    print("- Use curl to test: curl http://localhost:8080/")
    print("- Check stats: curl http://localhost:8080/admin/stats")

if __name__ == "__main__":
    main()
