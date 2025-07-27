# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for Astro blog deployment. It exposes tools that AI agents can use to automatically publish articles and commit code changes to an Astro blog repository.

## Key Components

- **astro_mcp_server.py**: Main server implementation using FastMCP
- **ASTRO_DIR**: Environment variable pointing to the Astro blog repository (defaults to `./astro`)
- **Blog System Location**: The actual Astro blog is located at `~/repo/blog/geyuxu.com`

## Development Commands

### Server Setup and Running
```bash
# Install dependencies
pip install mcp-server fastapi uvicorn

# Set the Astro directory path
export ASTRO_DIR=~/repo/blog/geyuxu.com

# Run the server
uvicorn astro_mcp_server:app --reload --port 23333
```

### Testing the Server
```bash
# Test server is running
curl http://localhost:23333/openapi.json

# Test publish_article tool
curl -X POST http://localhost:23333/tools/publish_article

# Test commit_code tool with custom message
curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"feat: test commit"}' \
  http://localhost:23333/tools/commit_code
```

## Architecture

The server implements two MCP tools:

1. **publish_article**: Executes `npm run deploy` in the Astro project directory
2. **commit_code**: Performs git operations (add, commit, push) with customizable commit messages

The implementation uses subprocess to execute shell commands within the specified ASTRO_DIR, capturing and returning output for agent feedback.

## Development Workflow

1. Ensure ASTRO_DIR points to a valid Astro blog repository with git initialized
2. The Astro project should have a working `npm run deploy` script
3. Git credentials should be configured for push operations
4. The server runs on port 23333 by default

## Integration Notes

- Agents can discover available tools via the MCP protocol
- The server provides detailed command output for debugging
- Commit operations gracefully handle "nothing to commit" scenarios
- All operations are executed within the ASTRO_DIR context