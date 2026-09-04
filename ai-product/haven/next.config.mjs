const nextConfig = {
  output: 'standalone',          // ← 加这行
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  experimental: {
    serverComponentsExternalPackages: ['node:sqlite'],
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = { ...config.resolve.fallback, fs: false, path: false };
    }
    return config;
  },
};
export default nextConfig;