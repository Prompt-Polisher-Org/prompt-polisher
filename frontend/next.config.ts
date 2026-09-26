import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable HTTP response compression
  compress: true,

  // Image optimization: convert to WebP / AVIF automatically
  images: {
    formats: ['image/avif', 'image/webp'],
    // Responsive breakpoints for srcset
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
  },

  // Strict TypeScript / ESLint in builds
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
