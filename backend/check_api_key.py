#!/usr/bin/env python3
"""Check OpenAI API key configuration"""

import os
from app.config import settings

print("=" * 60)
print("OpenAI API Key Diagnostics")
print("=" * 60)

# Get key from both sources
env_key = os.getenv('OPENAI_API_KEY', '')
settings_key = settings.openai_api_key

print(f"\n1. Environment Variable:")
print(f"   Exists: {bool(env_key)}")
print(f"   Length: {len(env_key)}")
print(f"   First 15 chars: {env_key[:15] if env_key else 'N/A'}")
print(f"   Last 10 chars: ...{env_key[-10:] if env_key else 'N/A'}")

print(f"\n2. Settings (pydantic):")
print(f"   Exists: {bool(settings_key)}")
print(f"   Length: {len(settings_key)}")
print(f"   First 15 chars: {settings_key[:15] if settings_key else 'N/A'}")
print(f"   Last 10 chars: ...{settings_key[-10:] if settings_key else 'N/A'}")

print(f"\n3. Key Format Checks:")
print(f"   Starts with 'sk-': {settings_key.startswith('sk-')}")
print(f"   Starts with 'sk-proj-': {settings_key.startswith('sk-proj-')}")
print(f"   Has whitespace: {settings_key != settings_key.strip()}")
print(f"   Has newlines: {'\\n' in settings_key or '\\r' in settings_key}")
print(f"   Has spaces: {' ' in settings_key}")

if settings_key != settings_key.strip():
    print(f"\n   ⚠️  WARNING: Key has whitespace!")
    print(f"   Original length: {len(settings_key)}")
    print(f"   Stripped length: {len(settings_key.strip())}")

print(f"\n4. OpenAI Library:")
try:
    import openai
    print(f"   Version: {openai.__version__}")
except Exception as e:
    print(f"   Error: {e}")

print(f"\n5. Test API Key Format:")
# New OpenAI keys (project-based) are longer
if len(settings_key) > 100:
    print(f"   ✓ Length looks good for project key (164 chars expected)")
else:
    print(f"   ⚠️  Key seems short ({len(settings_key)} chars)")

print("\n" + "=" * 60)
