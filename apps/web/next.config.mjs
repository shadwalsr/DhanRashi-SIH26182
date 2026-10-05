/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    // When running under standalone local dev without Vercel routing, proxy to local API
    const apiTarget = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiTarget}/api/:path*`,
      },
      {
        source: "/health/:path*",
        destination: `${apiTarget}/health/:path*`,
      },
    ];
  },
};

export default nextConfig;

