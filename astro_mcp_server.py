#!/usr/bin/env python3
"""astro_mcp_server.py — Minimal MCP server for an Astro blog

Prerequisites
-------------
- Python 3.10+
- `pip install mcp-server fastapi uvicorn`
- A checked-out Astro project (git repo) and working `npm` install.
- Set the environment variable `ASTRO_DIR` to the absolute path of your Astro
  project (defaults to `./astro`).

"""
from __future__ import annotations

import os
import pathlib
import subprocess
from typing import List

# MCP server helper from the `mcp-server` package (FastMCP implementation)
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ASTRO_DIR = pathlib.Path(os.getenv("ASTRO_DIR", "./astro")).expanduser().resolve()
if not ASTRO_DIR.is_dir():
    raise RuntimeError(
        f"ASTRO_DIR {ASTRO_DIR} does not exist or is not a directory"
    )

# ---------------------------------------------------------------------------
# Helper util
# ---------------------------------------------------------------------------

def _run(cmd: List[str]) -> str:
    """Run *cmd* inside *ASTRO_DIR* and return the combined stdout+stderr."""
    proc = subprocess.run(cmd, cwd=ASTRO_DIR, capture_output=True, text=True)
    banner = f"$ {' '.join(cmd)}\n"
    return banner + proc.stdout + proc.stderr

# ---------------------------------------------------------------------------
# MCP app definition
# ---------------------------------------------------------------------------
app = FastMCP(
    name="Astro Deployment MCP Server",
    instructions="Exposes publish_article and commit_code tools for an Astro blog",
)

# @app.tool()
# async def publish_article() -> str:
#     """Deploy the Astro blog to production by running npm run deploy."""
#     return _run(["npm", "run", "deploy"])

@app.tool()
async def publish_blog_post(
    directory: str, 
    content: str, 
    filename: str,
    commit_message: str = None,
    deploy: bool = True
) -> str:
    """Save article, commit changes, and optionally deploy - all in one command.
    
    Args:
        directory: The subdirectory within ASTRO_DIR where to save the file (e.g., "src/content/blog")
        content: The content to save to the file
        filename: The filename to use (e.g., "my-article.md")
        commit_message: Optional custom commit message (defaults to "feat: publish {filename}")
        deploy: Whether to run npm deploy after commit (default: True)
    """
    import datetime
    outputs: List[str] = []
    
    # Step 1: Save the article
    target_dir = ASTRO_DIR / directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = target_dir / filename
    
    # Add frontmatter if the file is markdown and doesn't already have it
    if filename.endswith(('.md', '.mdx')) and not content.startswith('---'):
        # Extract title from content (first # heading or filename)
        title = filename.replace('.md', '').replace('.mdx', '').replace('-', ' ').title()
        lines = content.split('\n')
        for line in lines[:5]:  # Check first 5 lines for a title
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        frontmatter = f"""---
title: "{title}"
pubDate: {datetime.date.today().isoformat()}
description: "Article published via MCP"
author: "AI Assistant"
---

"""
        content = frontmatter + content
    
    # Write the file
    try:
        file_path.write_text(content, encoding='utf-8')
        outputs.append(f"✓ Saved article to: {file_path}")
    except Exception as e:
        return f"Error saving article: {str(e)}"
    
    # Step 2: Commit and push
    outputs.append("\n=== Git Operations ===")
    outputs.append(_run(["git", "add", "-A"]))
    
    # Use custom message or generate one
    if not commit_message:
        commit_message = f"feat: publish {filename}"
    
    commit_result = _run(["git", "commit", "-m", commit_message])
    outputs.append(commit_result)
    
    if "nothing to commit" not in commit_result:
        outputs.append(_run(["git", "push"]))
    else:
        outputs.append("No changes to push.\n")
    
    # Step 3: Deploy (if requested)
    if deploy:
        outputs.append("\n=== Deployment ===")
        outputs.append(_run(["npm", "run", "deploy"]))
    
    return "\n".join(outputs)

@app.tool()
async def find_articles(
    keyword: str,
    directory: str = "src/content/blog",
    case_sensitive: bool = False
) -> str:
    """Find articles containing a keyword in their content or filename.
    
    Args:
        keyword: The keyword to search for
        directory: The subdirectory within ASTRO_DIR to search (default: "src/content/blog")
        case_sensitive: Whether the search should be case sensitive (default: False)
    """
    search_dir = ASTRO_DIR / directory
    if not search_dir.exists():
        return f"Directory not found: {search_dir}"
    
    results = []
    search_keyword = keyword if case_sensitive else keyword.lower()
    
    # Search for markdown files
    for file_path in search_dir.rglob("*.md"):
        try:
            content = file_path.read_text(encoding='utf-8')
            filename = file_path.name
            
            # Check if keyword is in filename
            filename_to_check = filename if case_sensitive else filename.lower()
            if search_keyword in filename_to_check:
                results.append(f"✓ Found in filename: {file_path.relative_to(ASTRO_DIR)}")
                continue
            
            # Check if keyword is in content
            content_to_check = content if case_sensitive else content.lower()
            if search_keyword in content_to_check:
                # Find the line containing the keyword
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    line_to_check = line if case_sensitive else line.lower()
                    if search_keyword in line_to_check:
                        preview = line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                        results.append(f"✓ Found in {file_path.relative_to(ASTRO_DIR)} (line {i+1}): {preview}")
                        break
        except Exception as e:
            results.append(f"✗ Error reading {file_path.relative_to(ASTRO_DIR)}: {str(e)}")
    
    if not results:
        return f"No articles found containing '{keyword}'"
    
    return f"Found {len(results)} matches for '{keyword}':\n\n" + "\n".join(results)

@app.tool()
async def delete_article(
    filepath: str,
    commit: bool = True,
    push: bool = True
) -> str:
    """Delete an article file and optionally commit the deletion.
    
    Args:
        filepath: The file path relative to ASTRO_DIR (e.g., "src/content/blog/my-article.md")
        commit: Whether to commit the deletion (default: True)
        push: Whether to push after commit (default: True)
    """
    file_path = ASTRO_DIR / filepath
    
    # Check if file exists
    if not file_path.exists():
        return f"File not found: {filepath}"
    
    # Check if it's a markdown file
    if not filepath.endswith(('.md', '.mdx')):
        return f"Error: Can only delete markdown files (.md or .mdx), got: {filepath}"
    
    # Check if file is within ASTRO_DIR (security check)
    try:
        file_path.relative_to(ASTRO_DIR)
    except ValueError:
        return f"Error: File must be within ASTRO_DIR"
    
    outputs: List[str] = []
    
    # Delete the file
    try:
        file_path.unlink()
        outputs.append(f"✓ Deleted file: {filepath}")
    except Exception as e:
        return f"Error deleting file: {str(e)}"
    
    # Commit and push if requested
    if commit:
        outputs.append("\n=== Git Operations ===")
        outputs.append(_run(["git", "add", "-A"]))
        
        commit_message = f"feat: remove article {file_path.name}"
        commit_result = _run(["git", "commit", "-m", commit_message])
        outputs.append(commit_result)
        
        if push and "nothing to commit" not in commit_result:
            outputs.append(_run(["git", "push"]))
    
    return "\n".join(outputs)

# ---------------------------------------------------------------------------
# Test mode support
# ---------------------------------------------------------------------------
async def test_mode():
    """Run in test mode - directly call tools for testing"""
    import json
    
    print("=== MCP Server Test Mode ===")
    print(f"ASTRO_DIR: {ASTRO_DIR}")
    print("\nAvailable tools:")
    tools = await app.get_tools()
    for name, tool in tools.items():
        desc_first_line = tool.description.split('\n')[0]
        print(f"  - {name}: {desc_first_line}")
    
    # Get the actual tool functions
    publish_tool = tools.get("publish_blog_post")
    find_tool = tools.get("find_articles")
    delete_tool = tools.get("delete_article")
    
    # Test 1: publish_blog_post
    print("\n\n1. Testing publish_blog_post...")
    print("-" * 40)
    
    if publish_tool:
        # Call the tool's underlying function
        result = await publish_tool.fn(
            directory="src/content/blog/test",
            content="""# MCP Test Article

This is a test article created in test mode.

## Features Tested

- Article creation with frontmatter
- Git operations
- Search functionality

Keywords: MCP, Test, FastMCP, Automation""",
            filename="mcp-test-mode.md",
            commit_message="test: test mode article",
            deploy=False
        )
        print("Result:")
        print(result)
    
    # Test 2: find_articles
    print("\n\n2. Testing find_articles...")
    print("-" * 40)
    
    if find_tool:
        result = await find_tool.fn(
            keyword="MCP",
            directory="src/content/blog/test"
        )
        print("Result:")
        print(result)
    
    # Test 3: delete_article
    print("\n\n3. Testing delete_article...")
    print("-" * 40)
    
    if delete_tool:
        result = await delete_tool.fn(
            filepath="src/content/blog/test/mcp-test-mode.md",
            commit=False,
            push=False
        )
        print("Result:")
        print(result)
    
    print("\n=== Test Mode Completed ===")

# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run in test mode
        import asyncio
        asyncio.run(test_mode())
    else:
        # Run as stdio server for MCP protocol
        app.run()