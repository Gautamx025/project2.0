import type { NextConfig } from 'next';
const config: NextConfig = {
  devIndicators: false,
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/:path*` }, { source: '/media/:path*', destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/media/:path*` }];
  },
};
export default config;
