#!/usr/bin/env node

import { HedgeFundAITools } from './tools.js';

async function main() {
  try {
    const tools = new HedgeFundAITools();
    await tools.run();
  } catch (error) {
    console.error('Failed to start MCP server:', error);
    process.exit(1);
  }
}

main(); 