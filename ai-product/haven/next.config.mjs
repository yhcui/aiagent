/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // node:sqlite 是 Node.js 原生模块，不打包
    serverComponentsExternalPackages: ['node:sqlite'],
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
      };
    }
    return config;
  },
};

export default nextConfig;
