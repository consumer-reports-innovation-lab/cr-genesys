import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable source maps and disable minification for debugging
  productionBrowserSourceMaps: true,
  experimental: {
    // Optional: Keep component names readable
    optimizePackageImports: ["lucide-react"],
  },
  webpack: (config, { dev, isServer, webpack }) => {
    if (!dev && !isServer) {
      // Disable minification for client-side production bundles
      config.optimization.minimize = false;
      
      // Force React to use development builds for better error messages
      config.resolve.alias = {
        ...config.resolve.alias,
        'react$': 'react/cjs/react.development.js',
        'react-dom$': 'react-dom/cjs/react-dom.development.js',
        'react-dom/client$': 'react-dom/cjs/react-dom-client.development.js',
        'scheduler$': 'scheduler/cjs/scheduler.development.js',
      };
      
      // Enable React development mode for better debugging
      config.plugins.push(
        new webpack.DefinePlugin({
          __DEV__: JSON.stringify(true),
          'process.env.NODE_ENV': JSON.stringify('development'),
        })
      );
    }
    return config;
  },
};

export default nextConfig;
