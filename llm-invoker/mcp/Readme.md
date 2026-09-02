#运行
mcp dev words_counter.py  

mcp dev 是 FastMCP CLI 提供的开发命令，用于启动 MCP Inspector 界面来测试和调试你的 MCP 服务器。

# 配置
{
  "mcpServers": {
    "words_counter": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "python",
        "D:/OpenCode-Project/aiagent/llm-invoker/mcp/words_counter.py"
      ]
    }
  }
}
