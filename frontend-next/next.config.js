/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Ignore ESLint errors during builds (use lint command for checks)
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Ignore TypeScript errors during builds
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // API proxy for backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
      {
        source: '/ws/:path*',
        destination: 'http://localhost:8001/ws/:path*',
      },
    ];
  },

  // CORS headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
