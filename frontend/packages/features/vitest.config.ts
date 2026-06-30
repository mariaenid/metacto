import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [],
  },
  resolve: {
    alias: {
      // Allow importing RN modules in the test environment.
      "react-native": "react-native-web",
    },
  },
});
