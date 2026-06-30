const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, "../..");

const config = getDefaultConfig(projectRoot);

// Metro must watch the entire monorepo so it can resolve workspace packages.
config.watchFolders = [workspaceRoot];

// Look for modules in the app's node_modules first, then the workspace root.
// This is required because pnpm uses a non-flat node_modules layout.
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(workspaceRoot, "node_modules"),
];

module.exports = config;
