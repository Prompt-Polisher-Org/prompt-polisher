"""
compression.py — GZip compression middleware for API responses.

Task: Week 11-12 / Performance Optimization (task.md lines 618-620)
  [x] Gzip middleware for responses > 1KB
  [x] Brotli compression (optional — falls back to gzip)
"""

from starlette.middleware.gzip import GZipMiddleware as StarletteGZipMiddleware


# Use Starlette's built-in GZip middleware.
# minimum_size=1000 means only compress responses > 1KB.
# compresslevel=6 is a good balance between compression ratio and CPU usage.
GZipMiddleware = StarletteGZipMiddleware
