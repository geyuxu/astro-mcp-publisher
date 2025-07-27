# Astro MCP Server

用于Astro博客自动化发布的MCP服务器。

## 功能

- `publish_article`: 执行 `npm run deploy` 发布博客
- `commit_code`: 执行 git add/commit/push 提交代码

## 安装

```bash
pip install fastmcp uvicorn
```

## 配置

设置环境变量：
```bash
export ASTRO_DIR=~/repo/blog/geyuxu.com
```

## 运行

### 独立运行测试
```bash
export ASTRO_DIR=~/repo/blog/geyuxu.com
python astro_mcp_server.py
```
服务器通过stdio协议运行，用于MCP通信。

### 在Claude Code中集成

MCP服务器需要通过stdio协议运行。在Claude Code的MCP配置中添加：

```
claude mcp add astro [PATH]/astro_mcp_server.py --transport stdio -s user
```

使用工具：
   - 在Claude Code中直接说："请发布博客文章"
   - 或："提交代码更改，commit message为'feat: update home page'"

## 注意

- FastMCP 使用标准 MCP 协议通过stdio进行通信，而不是HTTP协议
- MCP服务器作为子进程运行，通过标准输入/输出与Claude Code通信
- 确保Python环境中已安装fastmcp和uvicorn依赖

## 测试

运行测试脚本验证功能：
```bash
python test_direct.py
```