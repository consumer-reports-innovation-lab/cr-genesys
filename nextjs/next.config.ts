import type { NextConfig } from "next";

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
      
      // Use React development builds for better error messages
      config.resolve.alias = {
        ...config.resolve.alias,
        'react$': 'react/index.js',
        'react-dom$': 'react-dom/index.js',
      };
      
      // Enable React development mode for better debugging
      config.plugins.push(
        new config.webpack.DefinePlugin({
          __DEV__: JSON.stringify(true),
        })
      );
    }
    return config;
  },
};

export default nextConfig;
