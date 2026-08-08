#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# generate-ssl.sh — Generate a self-signed SSL certificate for local dev.
#
# Usage:  bash infra/nginx/ssl/generate-ssl.sh
# Output: server.key and server.crt in this directory
#
# This is for LOCAL DEVELOPMENT ONLY. In production, use Let's Encrypt.
# Your browser will show a security warning — that's expected for self-signed.
# ──────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔐 Generating self-signed SSL certificate for Prompt Polisher..."
echo ""

# Generate a 2048-bit RSA private key and self-signed certificate
# Valid for 365 days, with Subject fields for local dev
openssl req -x509 -nodes \
    -days 365 \
    -newkey rsa:2048 \
    -keyout server.key \
    -out server.crt \
    -subj "/C=IN/ST=Dev/L=Local/O=PromptPolisher/OU=Dev/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:192.168.1.100"

echo ""
echo "✅ SSL certificate generated successfully!"
echo "   📁 Key:  $SCRIPT_DIR/server.key"
echo "   📁 Cert: $SCRIPT_DIR/server.crt"
echo ""
echo "⚠️  This is a SELF-SIGNED certificate for local development only."
echo "   Your browser will show a security warning — this is expected."
echo "   For production, use Let's Encrypt (certbot)."
