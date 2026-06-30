/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    "@metacto/ui",
    "@metacto/features",
    "@metacto/api-client",
    "react-native",
    "react-native-web",
  ],
  webpack(config) {
    // Prefer .web.tsx/.web.ts over .tsx/.ts so platform-split screens are picked correctly.
    config.resolve.extensions = [
      ".web.tsx", ".web.ts", ".web.jsx", ".web.js",
      ...config.resolve.extensions,
    ];
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      "react-native$": "react-native-web",
    };
    return config;
  },
};

module.exports = nextConfig;
