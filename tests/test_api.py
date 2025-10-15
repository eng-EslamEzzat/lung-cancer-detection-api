#!/usr/bin/env python3
"""
Test script for FastAPI Lung Cancer Detection Microservice
"""

import pytest
import requests
import os
import time
import tempfile
import io
from pathlib import Path
from PIL import Image
import numpy as np

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
PREDICT_ENDPOINT = f"{API_BASE_URL}/predict"
MODEL_INFO_ENDPOINT = f"{API_BASE_URL}/model/info"


class TestLungCancerAPI:
    """Test class for the Lung Cancer Detection API"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        cls.test_image_path = None
        cls.wait_for_api()
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test class"""
        if cls.test_image_path and os.path.exists(cls.test_image_path):
            os.remove(cls.test_image_path)
    
    @classmethod
    def wait_for_api(cls, max_retries=30):
        """Wait for the API to become available"""
        print("⏳ Waiting for API to become available...")
        
        for i in range(max_retries):
            try:
                response = requests.get(HEALTH_ENDPOINT, timeout=5)
                if response.status_code == 200:
                    print("✅ API is ready!")
                    return True
            except:
                pass
            
            print(f"   Retry {i+1}/{max_retries}...")
            time.sleep(1)
        
        raise Exception("❌ API did not become available in time")
    
    def create_test_image(self):
        """Create a test image for testing"""
        if self.test_image_path is None:
            # Create a temporary test image
            test_array = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
            test_image = Image.fromarray(test_array)
            
            # Save to temporary file
            fd, self.test_image_path = tempfile.mkstemp(suffix='.jpg')
            os.close(fd)
            test_image.save(self.test_image_path, "JPEG")
        
        return self.test_image_path
    
    def test_health_check(self):
        """Test the health check endpoint"""
        print("🔍 Testing health check endpoint...")
        
        response = requests.get(HEALTH_ENDPOINT, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        
        print(f"✅ Health check passed: {data}")
    
    def test_model_info(self):
        """Test the model info endpoint"""
        print("🔍 Testing model info endpoint...")
        
        response = requests.get(MODEL_INFO_ENDPOINT, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "model_loaded" in data
        assert "supported_formats" in data
        assert "max_file_size_mb" in data
        assert "model_input_size" in data
        
        print(f"✅ Model info retrieved: {data}")
    
    def test_prediction_success(self):
        """Test successful image prediction"""
        print("🔍 Testing prediction endpoint...")
        
        test_image_path = self.create_test_image()
        
        with open(test_image_path, 'rb') as f:
            files = {'file': (os.path.basename(test_image_path), f, 'image/jpeg')}
            
            response = requests.post(PREDICT_ENDPOINT, files=files, timeout=60)
            assert response.status_code == 200
            
            data = response.json()
            
            # Validate response structure
            required_fields = [
                'status', 'filename', 'image_info', 'prediction_result', 'message'
            ]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
            
            # Validate image_info structure
            image_info = data['image_info']
            assert 'width' in image_info
            assert 'height' in image_info
            assert isinstance(image_info['width'], int)
            assert isinstance(image_info['height'], int)
            
            # Validate prediction_result structure
            prediction_result = data['prediction_result']
            assert 'prediction' in prediction_result
            assert 'confidence' in prediction_result
            assert isinstance(prediction_result['confidence'], (int, float))
            assert 0.0 <= prediction_result['confidence'] <= 1.0
            
            print(f"✅ Prediction successful: {data['prediction_result']}")
    
    def test_prediction_invalid_file_type(self):
        """Test prediction with invalid file type"""
        print("🔍 Testing with invalid file type...")
        
        # Create a text file
        fd, invalid_file_path = tempfile.mkstemp(suffix='.txt')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write("This is not an image file")
            
            with open(invalid_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                
                response = requests.post(PREDICT_ENDPOINT, files=files, timeout=30)
                assert response.status_code == 400
                
                data = response.json()
                assert "error" in data["status"] or "Invalid" in data.get("detail", "")
                
            print("✅ Invalid file type correctly rejected")
        
        finally:
            if os.path.exists(invalid_file_path):
                os.remove(invalid_file_path)
    
    def test_prediction_no_file(self):
        """Test prediction without file"""
        print("🔍 Testing without file...")
        
        response = requests.post(PREDICT_ENDPOINT, timeout=30)
        assert response.status_code == 422  # Validation error
        
        print("✅ No file correctly rejected")
    
    def test_prediction_empty_file(self):
        """Test prediction with empty file"""
        print("🔍 Testing with empty file...")
        
        # Create an empty file
        fd, empty_file_path = tempfile.mkstemp(suffix='.jpg')
        try:
            os.close(fd)  # Close the file descriptor, leaving empty file
            
            # Read the empty file and send it
            with open(empty_file_path, 'rb') as f:
                file_content = f.read()  # This will be empty bytes
            
            # Use requests with data instead of files parameter for empty file
            files = {'file': ('empty.jpg', io.BytesIO(file_content), 'image/jpeg')}
            response = requests.post(PREDICT_ENDPOINT, files=files, timeout=30)
            
            # Empty file should be treated as a bad request
            assert response.status_code == 400
                
            print("✅ Empty file correctly rejected")
        
        finally:
            if os.path.exists(empty_file_path):
                os.remove(empty_file_path)


def run_tests():
    """Run all tests manually (without pytest)"""
    print("🚀 Starting FastAPI Lung Cancer Detection API Tests")
    print(f"   API URL: {API_BASE_URL}")
    print("-" * 50)
    
    test_instance = TestLungCancerAPI()
    test_instance.setup_class()
    
    tests = [
        test_instance.test_health_check,
        test_instance.test_model_info,
        test_instance.test_prediction_success,
        test_instance.test_prediction_invalid_file_type,
        test_instance.test_prediction_no_file,
        test_instance.test_prediction_empty_file
    ]
    
    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)
    
    test_instance.teardown_class()
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    
    print(f"   ✅ Passed: {passed}/{total}")
    if passed == total:
        print("   🎉 All tests passed!")
    else:
        print(f"   ❌ Failed: {total - passed}/{total}")


if __name__ == "__main__":
    # Run tests manually to see detailed output
    run_tests()
