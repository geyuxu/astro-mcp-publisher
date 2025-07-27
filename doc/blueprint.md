Astro MCP Server — 分步实现蓝图（已移除原步骤 0）

#	步骤	Prompt ✍️	验收标准 ✅
1	生成服务器骨架	“创建文件 astro_mcp_server.py，使用 mcp-server 的 FastMCP：• 实例化 MCP 应用• 读取 ASTRO_DIR 环境变量并校验目录存在• 实现私有函数 _run(cmd) 用于在 ASTRO_DIR 内执行 shell 命令并捕获输出• 提供 __main__ 入口用 uvicorn 启动”	- 运行 python astro_mcp_server.py 后，uvicorn 在 http://localhost:23333/ 启动- 访问 http://localhost:23333/openapi.json 返回 OpenAPI 文档
2	发布文章工具	“在文件中添加 @app.tool：publish_article() 调用 _run(['npm','run','deploy']) 并返回输出”	- 调用 curl -X POST http://localhost:23333/tools/publish_article 返回 npm 输出- 输出中含有 Astro 的部署成功信息（如 ‘Deployed!’）
3	提交代码工具	“再添加 @app.tool：commit_code(message:str='chore: automated commit')1) _run(['git','add','-A'])2) _run(['git','commit','-m',message])，若提示 ‘nothing to commit’ 则跳过 push3) 若有提交则 _run(['git','push'])”	- 在 Astro 目录修改文件后调用工具- curl 调用返回的输出包含 git push 完成信息- git log -1 的 commit message 与传入的 message 相同
4	本地端到端测试	“终端 A：uvicorn astro_mcp_server:app --reload终端 B：① 发布：curl -X POST http://localhost:23333/tools/publish_article② 提交：在 Astro 目录改动文件→ curl -X POST -H \"Content-Type: application/json\" -d '{\"message\":\"feat: test commit\"}' http://localhost:23333/tools/commit_code”	- 发布脚本执行完毕，无报错- Git 仓库出现新 commit 并已推送到远端
5	Agent 集成	“在 Graphiti / Claude Code 的 MCP 配置里：mcp add http://127.0.0.1:23333验证 list tools 出现 publish_article, commit_code”	- Agent 可通过自然语言调用两个工具，例如“发布文章”→触发部署- 调用日志显示 HTTP 200

如需再调整或添加更多验收项，随时告诉我！