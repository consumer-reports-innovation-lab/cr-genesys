import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Basic config for development debugging
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

export default nextConfig;
