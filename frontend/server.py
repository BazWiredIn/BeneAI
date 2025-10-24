#!/usr/bin/env python3
"""
HTTPS Server for BeneAI Frontend
Serves static files over HTTPS for Chrome extension development
"""

import http.server
import ssl
import sys
import os

def run_https_server(port=8443, certfile='cert.pem', keyfile='key.pem'):
    """
    Run an HTTPS server with SSL support

    Args:
        port: Port to listen on (default 8443)
        certfile: Path to SSL certificate file
        keyfile: Path to SSL private key file
    """

    # Check if certificate files exist
    if not os.path.exists(certfile):
        print(f"Error: Certificate file '{certfile}' not found")
        print("Run ./run_https.sh to generate certificates")
        sys.exit(1)

    if not os.path.exists(keyfile):
        print(f"Error: Key file '{keyfile}' not found")
        print("Run ./run_https.sh to generate certificates")
        sys.exit(1)

    # Create HTTP server
    server_address = ('localhost', port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)

    # Wrap with SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    print(f"Serving HTTPS on https://localhost:{port}")
    print(f"Certificate: {certfile}")
    print(f"Key: {keyfile}")
    print("\nNote: Browser will show security warning - click 'Advanced' → 'Proceed to localhost'")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    # Parse command line arguments
    port = 8443
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            print("Usage: python3 server.py [port]")
            sys.exit(1)

    run_https_server(port=port)
