import type { NextConfig } from "next";
const config: NextConfig = {
  devIndicators: false,
  async rewrites() {
    // Vercel Services routes API/media before requests enter the web service.
    if (process.env.VERCEL) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/:path*`,
      },
      {
        source: "/media/:path*",
        destination: `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/media/:path*`,
      },
    ];
  },
};
export default config;
