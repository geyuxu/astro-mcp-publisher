astro_mcp_server.py 示例代码。它使用 mcp-server 的 FastMCP 实现，向代理公开两个工具：
	1.	publish_article → 在 ASTRO_DIR 中执行 npm run deploy
	2.	commit_code → 在 ASTRO_DIR 中依次执行 git add -A、git commit -m "<msg>"、git push

代码顶部包含运行前置条件、环境变量与启动方式，可直接 uvicorn astro_mcp_server:app --reload 启动。
如需进一步调整目录或参数，只需修改 ASTRO_DIR 配置或函数实现即可。如果想要额外的错误处理、权限控制、日志记录等，告诉我，我可以继续迭代。

```
#!/usr/bin/env python3
"""astro_mcp_server.py — Minimal MCP server for an Astro blog

This script exposes two MCP *tools* that an agent can call:

1. **publish_article** – runs `npm run deploy` in the Astro project directory
to publish new articles.
2. **commit_code** – stages, commits and pushes code changes in the Astro
directory.

Prerequisites
-------------
- Python 3.10+
- `pip install mcp-server fastapi uvicorn`
- A checked-out Astro project (git repo) and working `npm` install.
- Set the environment variable `ASTRO_DIR` to the absolute path of your Astro
  project (defaults to `./astro`).

Run the server:
    export ASTRO_DIR=/absolute/path/to/astro
    uvicorn astro_mcp_server:app --reload --port **23333**

Your agent platform (e.g. Claude Code, Graphiti, etc.) can now call the two
registered tools via the MCP protocol on port 23333.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
from typing import Optional, List

# MCP server helper from the `mcp-server` package (FastMCP implementation)
try:
    from mcp.server.fastmcp.server import MCP  # type: ignore
except ImportError:  # pragma: no cover
    from fastmcp.server import MCP  # type: ignore

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ASTRO_DIR = pathlib.Path(os.getenv("ASTRO_DIR", "./astro")).resolve()
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
app = MCP(
    title="Astro Deployment MCP Server",
    description="Exposes publish_article and commit_code tools for an Astro blog",
)


@app.tool(
    name="publish_article",
    description="Deploy the Astro site by running `npm run deploy` inside ASTRO_DIR.",
)
async def publish_article() -> str:  # noqa: D401 – imperative mood OK
    """Deploy the Astro blog to production and return the CLI output."""
    return _run(["npm", "run", "deploy"])


@app.tool(
    name="commit_code",
    description="Stage, commit, and push code changes in ASTRO_DIR.",
)
async def commit_code(message: Optional[str] = "chore: automated commit") -> str:
    """Commit local changes and push to the remote repository.

    Parameters
    ----------
    message:
        The git commit message (default: *chore: automated commit*).
    """
    outputs: List[str] = []

    # 1. git add -A
    outputs.append(_run(["git", "add", "-A"]))

    # 2. git commit (handle no-change exit code 1 gracefully)
    commit_result = _run(["git", "commit", "-m", message])
    outputs.append(commit_result)

    # 3. git push (only attempt if commit was created)
    if "nothing to commit" not in commit_result:
        outputs.append(_run(["git", "push"]))
    else:
        outputs.append("No changes to push.\n")

    return "\n".join(outputs)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "astro_mcp_server:app",
        host="0.0.0.0",
        port=23333,  # Changed from 8000 to 23333
        reload=True,
    )

```