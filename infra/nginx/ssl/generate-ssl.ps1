# ──────────────────────────────────────────────────────────────────────────────
# generate-ssl.ps1 — Generate a self-signed SSL certificate for local dev.
#
# Usage:  powershell -ExecutionPolicy Bypass -File infra\nginx\ssl\generate-ssl.ps1
# Output: server.key and server.crt in this directory
#
# Requires: OpenSSL installed and available in PATH
#           (comes with Git for Windows, or install via choco install openssl)
# ──────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "`n🔐 Generating self-signed SSL certificate for Prompt Polisher...`n" -ForegroundColor Cyan

# Check if OpenSSL is available
try {
    $null = Get-Command openssl -ErrorAction Stop
} catch {
    Write-Host "❌ OpenSSL not found in PATH." -ForegroundColor Red
    Write-Host "   Install it via: choco install openssl" -ForegroundColor Yellow
    Write-Host "   Or use the OpenSSL that comes with Git for Windows." -ForegroundColor Yellow
    exit 1
}

# Generate the self-signed certificate
openssl req -x509 -nodes `
    -days 365 `
    -newkey rsa:2048 `
    -keyout server.key `
    -out server.crt `
    -subj "/C=IN/ST=Dev/L=Local/O=PromptPolisher/OU=Dev/CN=localhost" `
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:192.168.1.100"

Write-Host "`n✅ SSL certificate generated successfully!" -ForegroundColor Green
Write-Host "   📁 Key:  $scriptDir\server.key"
Write-Host "   📁 Cert: $scriptDir\server.crt"
Write-Host ""
Write-Host "⚠️  This is a SELF-SIGNED certificate for local development only." -ForegroundColor Yellow
Write-Host "   Your browser will show a security warning — this is expected."
Write-Host "   For production, use Let's Encrypt (certbot)."
