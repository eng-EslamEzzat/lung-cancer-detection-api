#!/usr/bin/env python3
"""
Script to start FastAPI server for testing
"""

import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting FastAPI Lung Cancer Detection Server for Testing...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs")
    print("Health Check: http://127.0.0.1:8000/health")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable reload for testing
        log_level="info"
    )