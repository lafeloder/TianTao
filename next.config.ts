import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,

  basePath: "/lafeloder",
  assetPrefix: "/lafeloder",

  images: {
    unoptimized: true,
  },

  webpack: (config) => {
    config.module.rules.push({
      test: /\.bib$/,
      type: "asset/source",
    });
    return config;
  },
};

export default nextConfig;
