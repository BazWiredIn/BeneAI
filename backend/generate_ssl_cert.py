#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for HTTPS development
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_certificates():
    """Generate self-signed SSL certificates for localhost"""
    
    cert_file = "cert.pem"
    key_file = "key.pem"
    
    # Check if certificates already exist
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"✅ SSL certificates already exist:")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        return True
    
    print("Generating self-signed SSL certificates...")
    
    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa", "-out", key_file, "2048"
        ], check=True)
        
        # Generate certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", key_file, 
            "-out", cert_file, "-days", "365", "-subj",
            "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ], check=True)
        
        print(f"SSL certificates generated successfully!")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        print(f"   Valid for: 365 days")
        print(f"   Subject: localhost")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error generating certificates: {e}")
        print("   Make sure OpenSSL is installed and in your PATH")
        return False
    except FileNotFoundError:
        print("OpenSSL not found!")
        print("   Please install OpenSSL:")
        print("   - Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("   - Or use WSL/Linux subsystem")
        return False

if __name__ == "__main__":
    success = generate_ssl_certificates()
    if success:
        print("\nYou can now run the backend with HTTPS!")
        print("   python main.py")
        print("\nNote: Browser will show security warning - click 'Advanced' -> 'Proceed to localhost'")
    else:
        print("\nFailed to generate certificates. Using HTTP fallback.")
        sys.exit(1)
