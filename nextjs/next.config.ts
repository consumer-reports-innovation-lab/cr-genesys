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
    }
    return config;
  },
};

export default nextConfig;
