#!/usr/bin/env python3
"""
REAgent - AI Real Estate Concierge
Quick start script for development
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    """Run the REAgent application"""
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found. Creating a template...")
        create_env_template()
        print("✅ Created .env file. Please configure your API keys before running again.")
        print("📝 At minimum, set your OPENAI_API_KEY in the .env file.")
        return
    
    # Check for OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        print("❌ OpenAI API key not configured!")
        print("📝 Please set your OPENAI_API_KEY in the .env file")
        print("🔗 Get your API key from: https://platform.openai.com/api-keys")
        return
    
    print("🚀 Starting REAgent - AI Real Estate Concierge")
    print("🌐 Web interface will be available at: http://localhost:8000")
    print("📋 API documentation: http://localhost:8000/docs")
    print("💬 Ready to help you find your perfect home!")
    print("-" * 60)
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )

def create_env_template():
    """Create a template .env file"""
    env_content = """# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./reagent.db

# Property Platform APIs (Optional - will work without these)
ZOOPLA_API_KEY=your_zoopla_api_key_here
RIGHTMOVE_API_KEY=your_rightmove_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Application Settings
SECRET_KEY=reagent-dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
"""
    
    with open(".env", "w") as f:
        f.write(env_content)

if __name__ == "__main__":
    main() 