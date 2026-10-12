import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // don't drop AGENTS.md files into the repo on `next dev`
  agentRules: false,
  // self-contained server bundle for the cloud run container (see Dockerfile)
  output: "standalone",
};

export default nextConfig;
