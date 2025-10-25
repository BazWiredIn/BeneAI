#!/usr/bin/env python3
"""
BeneAI Environment Setup Script
Creates .env file with API key placeholders
"""

import os

def create_env_file():
    """Create .env file with template values"""
    
    env_content = """# BeneAI Environment Configuration
# Add your actual API keys below

# OpenAI Configuration (REQUIRED for AI coaching)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=100
OPENAI_TEMPERATURE=0.7

# Hume AI Configuration (REQUIRED for emotion detection)
HUME_API_KEY=your-hume-api-key-here
HUME_ENABLE_FACE=true
HUME_ENABLE_PROSODY=true
HUME_ENABLE_LANGUAGE=true
HUME_FRAME_RATE=3.0

# Google Cloud Speech-to-Text (OPTIONAL - for better speech transcription)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-credentials.json
# GOOGLE_SPEECH_LANGUAGE=en-US

# Server Configuration
ENVIRONMENT=development
LOG_LEVEL=info
PORT=8000
ALLOWED_ORIGINS=*

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
CACHE_MAX_SIZE=1000

# Advice Settings
ADVICE_MAX_LENGTH=50
ADVICE_UPDATE_INTERVAL=3
"""

    env_file_path = ".env"
    
    if os.path.exists(env_file_path):
        print(f"WARNING: {env_file_path} already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    try:
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        
        print(f"SUCCESS: Created {env_file_path}")
        print("\nNext steps:")
        print("1. Edit .env file and add your API keys:")
        print("   - Get OpenAI key: https://platform.openai.com/api-keys")
        print("   - Get Hume AI key: https://beta.hume.ai/")
        print("2. Run: python main.py")
        print("3. Open: http://localhost:8080")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error creating .env file: {e}")
        return False

if __name__ == "__main__":
    print("BeneAI Environment Setup")
    print("=" * 40)
    create_env_file()
