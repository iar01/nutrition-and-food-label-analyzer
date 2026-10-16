import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // Compression can buffer streamed responses. We stream Server-Sent Events, so keep it off
  // here and let a reverse proxy handle compression in production (Phase 11).
  compress: false,
  turbopack: {
    rules: {
      '*.css': {
        loaders: ['@tailwindcss/turbopack'],
        as: '*.css',
      },
    },
  },
};

export default nextConfig;
