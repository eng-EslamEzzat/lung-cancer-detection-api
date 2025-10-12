#!/usr/bin/env python3
"""
Unified deployment script for FastAPI Lung Cancer Detection API
Supports both local and Docker deployments with identical configuration
"""

import argparse
import subprocess
import sys
import time
import requests
import os

def run_command(cmd, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_api_health(url="http://127.0.0.1:8000/health", timeout=30):
    """Check if the API is healthy"""
    print(f"⏳ Checking API health at {url}...")
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API is healthy! Status: {data.get('status')}")
                return True
        except:
            pass
        
        if i < timeout - 1:  # Don't sleep on the last iteration
            time.sleep(1)
    
    print("❌ API health check failed")
    return False

def deploy_local():
    """Deploy locally using Python"""
    print("🚀 Deploying FastAPI locally...")
    print("📋 Prerequisites:")
    print("   1. Anaconda environment activated")
    print("   2. Dependencies installed (pip install -r requirements-local.txt)")
    print("   3. .env file configured")
    print()
    
    # Check if dependencies are installed
    try:
        import fastapi, uvicorn
        print("✅ Dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Run: pip install -r requirements-local.txt")
        return False
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("💡 Copy .env.example to .env and configure it")
        return False
    
    print("✅ .env file found")
    print()
    print("🏃 Starting local server...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("📖 API Documentation: http://127.0.0.1:8000/docs")
    print("🩺 Health Check: http://127.0.0.1:8000/health")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Run the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        return False
    
    return True

def deploy_docker():
    """Deploy using Docker"""
    print("🐳 Deploying FastAPI with Docker...")
    
    # Check if Docker is available
    success, output = run_command("docker --version")
    if not success:
        print("❌ Docker is not available")
        print("💡 Please install Docker Desktop")
        return False
    
    print(f"✅ Docker available: {output.strip()}")
    
    # Build Docker image
    print("🔨 Building Docker image...")
    success, output = run_command("docker build -t fastapi-lung-cancer .")
    if not success:
        print(f"❌ Docker build failed: {output}")
        return False
    
    print("✅ Docker image built successfully")
    
    # Stop and remove existing container
    run_command("docker stop fastapi-container", shell=True)
    run_command("docker rm fastapi-container", shell=True)
    
    # Run Docker container
    print("🏃 Starting Docker container...")
    success, output = run_command(
        "docker run -d -p 8000:8000 --name fastapi-container --env-file .env fastapi-lung-cancer"
    )
    
    if not success:
        print(f"❌ Docker container failed to start: {output}")
        return False
    
    container_id = output.strip()
    print(f"✅ Docker container started: {container_id[:12]}...")
    
    # Wait for container to be ready
    time.sleep(5)
    
    # Check if API is healthy
    if check_api_health():
        print("🎉 Docker deployment successful!")
        print("📍 Server available at: http://127.0.0.1:8000")
        print("📖 API Documentation: http://127.0.0.1:8000/docs")
        print("🩺 Health Check: http://127.0.0.1:8000/health")
        print("📋 View logs: docker logs fastapi-container")
        print("⏹️  Stop container: docker stop fastapi-container")
        return True
    else:
        print("❌ Docker deployment failed - API not healthy")
        return False

def deploy_docker_compose():
    """Deploy using Docker Compose"""
    print("🐳 Deploying FastAPI with Docker Compose...")
    
    # Check if docker-compose is available
    success, output = run_command("docker-compose --version")
    if not success:
        print("❌ Docker Compose is not available")
        return False
    
    print(f"✅ Docker Compose available: {output.strip()}")
    
    # Stop existing services
    print("🛑 Stopping existing services...")
    run_command("docker-compose down")
    
    # Start services
    print("🚀 Starting services with Docker Compose...")
    success, output = run_command("docker-compose up -d --build")
    
    if not success:
        print(f"❌ Docker Compose deployment failed: {output}")
        return False
    
    print("✅ Docker Compose services started")
    
    # Wait for services to be ready
    time.sleep(8)
    
    # Check if API is healthy
    if check_api_health():
        print("🎉 Docker Compose deployment successful!")
        print("📍 Server available at: http://127.0.0.1:8000")
        print("📖 API Documentation: http://127.0.0.1:8000/docs")
        print("🩺 Health Check: http://127.0.0.1:8000/health")
        print("📋 View logs: docker-compose logs fastapi-lung-cancer")
        print("⏹️  Stop services: docker-compose down")
        return True
    else:
        print("❌ Docker Compose deployment failed - API not healthy")
        return False

def test_deployment():
    """Test the deployed API"""
    print("🧪 Testing deployed API...")
    
    if not check_api_health():
        return False
    
    # Run test suite
    print("🏃 Running test suite...")
    try:
        result = subprocess.run([sys.executable, "tests/test_api.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            print(result.stdout)
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Deploy FastAPI Lung Cancer Detection API")
    parser.add_argument("method", choices=["local", "docker", "compose"], 
                       help="Deployment method")
    parser.add_argument("--test", action="store_true", 
                       help="Run tests after deployment")
    parser.add_argument("--no-health-check", action="store_true",
                       help="Skip health check")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔬 FastAPI Lung Cancer Detection API Deployment")
    print("=" * 60)
    print()
    
    # Deploy based on method
    success = False
    if args.method == "local":
        success = deploy_local()
    elif args.method == "docker":
        success = deploy_docker()
    elif args.method == "compose":
        success = deploy_docker_compose()
    
    if not success:
        print("\n❌ Deployment failed!")
        sys.exit(1)
    
    # Run tests if requested
    if args.test:
        print("\n" + "=" * 60)
        if not test_deployment():
            print("\n❌ Tests failed!")
            sys.exit(1)
    
    print("\n🎉 Deployment completed successfully!")

if __name__ == "__main__":
    main()