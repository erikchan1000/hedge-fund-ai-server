/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/generate_analysis',
        destination: 'http://localhost:5000/api/generate_analysis',
      },
    ];
  },
};

module.exports = nextConfig; 