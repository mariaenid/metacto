/** @type {import('tailwindcss').Config} */
module.exports = {
  // NativeWind v4 requires specifying the content paths for class generation.
  content: [
    "./app/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
    "../../packages/features/src/**/*.{ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        primary: "#4F46E5",
      },
    },
  },
  plugins: [],
};
