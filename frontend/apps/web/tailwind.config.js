/** @type {import('tailwindcss').Config} */
module.exports = {
  // Scan all workspace packages so shared components pick up classes.
  content: [
    "./app/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
    "../../packages/features/src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#4F46E5",
      },
    },
  },
  plugins: [],
};
