/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/analysis/generate',
        destination: 'http://localhost:5000/api/analysis/generate',
      },
    ];
  },
};

module.exports = nextConfig;
