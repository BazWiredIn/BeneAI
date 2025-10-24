#!/bin/bash
# Run frontend with HTTPS for testing

echo "Generating self-signed certificate..."
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=BeneAI/CN=localhost"

echo ""
echo "Starting HTTPS server on https://localhost:8443"
echo "Note: Browser will show security warning - click 'Advanced' → 'Proceed to localhost'"
echo ""

python3 server.py 8443
