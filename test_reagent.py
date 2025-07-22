#!/usr/bin/env python3
"""
Simple test script for REAgent functionality
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_health_check():
    """Test that the application starts and health check works"""
    try:
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "REAgent"
        
        print("✅ Health check passed")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_web_interface():
    """Test that the web interface loads"""
    try:
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        assert "REAgent" in response.text
        assert "AI Real Estate Concierge" in response.text
        
        print("✅ Web interface loads correctly")
        return True
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are accessible"""
    try:
        from app.main import app
        client = TestClient(app)
        
        # Test preferences endpoint
        response = client.get("/api/preferences/test_session")
        assert response.status_code == 200
        
        # Test properties search endpoint
        response = client.get("/api/properties/")
        assert response.status_code == 200
        
        print("✅ API endpoints accessible")
        return True
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

def test_database_models():
    """Test that database models can be imported"""
    try:
        from app.database.models import User, Conversation, UserPreference, Property, PropertyRecommendation
        from app.database.database import Base, engine
        
        # Try to create tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database models work correctly")
        return True
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def test_agent_imports():
    """Test that agent components can be imported"""
    try:
        from app.agents.core_agent import REAgent
        from app.agents.preference_learner import PreferenceLearner
        from app.integrations.property_platforms import PropertyPlatformManager
        
        print("✅ Agent components import successfully")
        return True
    except Exception as e:
        print(f"❌ Agent imports test failed: {e}")
        return False

def run_basic_tests():
    """Run all basic tests"""
    print("🧪 Running REAgent Basic Tests")
    print("=" * 50)
    
    tests = [
        ("Database Models", test_database_models),
        ("Agent Imports", test_agent_imports),
        ("Health Check", test_health_check),
        ("Web Interface", test_web_interface),
        ("API Endpoints", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! REAgent is ready to go!")
        print("\n🚀 To start the application, run:")
        print("   python run.py")
        print("\n🌐 Then visit: http://localhost:8000")
    else:
        print("⚠️  Some tests failed. Please check your setup.")
        print("\n📋 Common issues:")
        print("   - Missing dependencies: pip install -r requirements.txt")
        print("   - Python path issues: run from the project root directory")
        print("   - Import errors: check that all files are present")
    
    return passed == total

if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1) 