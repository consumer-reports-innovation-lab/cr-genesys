import type { NextConfig } from "next";
import webpack from 'webpack';

const nextConfig: NextConfig = {
  // Enable source maps and disable minification for debugging
  productionBrowserSourceMaps: true,
  experimental: {
    // Optional: Keep component names readable
    optimizePackageImports: ["lucide-react"],
  },
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      // Disable minification for client-side production bundles
      config.optimization.minimize = false;
      
      // Enable React development mode for better debugging
      config.plugins.push(
        new webpack.DefinePlugin({
          __DEV__: JSON.stringify(true),
        })
      );
    }
    return config;
  },
};

export default nextConfig;
