#!/usr/bin/env python3
"""
Create self-signed SSL certificates using Python's cryptography library
"""

import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta

def create_self_signed_cert():
    """Create a self-signed certificate for localhost"""
    
    cert_file = "cert.pem"
    key_file = "key.pem"
    
    # Check if certificates already exist
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"SSL certificates already exist:")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        return True
    
    print("Creating self-signed SSL certificates...")
    
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"SSL certificates created successfully!")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        print(f"   Valid for: 365 days")
        print(f"   Subject: localhost")
        
        return True
        
    except ImportError:
        print("cryptography library not found!")
        print("Install it with: pip install cryptography")
        return False
    except Exception as e:
        print(f"Error creating certificates: {e}")
        return False

if __name__ == "__main__":
    success = create_self_signed_cert()
    if success:
        print("\nYou can now run the backend with HTTPS!")
        print("   python main.py")
        print("\nNote: Browser will show security warning - click 'Advanced' -> 'Proceed to localhost'")
    else:
        print("\nFailed to create certificates. Using HTTP fallback.")
