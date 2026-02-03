/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Transpile lucide-react to fix barrel import issues
  transpilePackages: ['lucide-react'],

  // Disable barrel file optimization for all packages - especially lucide-react
  experimental: {
    // Empty array means no automatic optimization - prevents the constructor error
    optimizePackageImports: [],
  },

  // Webpack configuration to handle lucide-react properly
  webpack: (config) => {
    // Ensure lucide-react is not treated specially
    config.resolve.alias = {
      ...config.resolve.alias,
    };
    return config;
  },

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
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/static/:path*',
        destination: 'http://localhost:8000/static/:path*',
      },
      {
        source: '/ws/:path*',
        destination: 'http://localhost:8000/ws/:path*',
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
