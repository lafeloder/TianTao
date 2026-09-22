import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,

  basePath: "/PRISM",
  assetPrefix: "/PRISM",

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
