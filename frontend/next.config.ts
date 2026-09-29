import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // don't drop AGENTS.md files into the repo on `next dev`
  agentRules: false,
};

export default nextConfig;
