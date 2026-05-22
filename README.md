# multilingual-emotion-analysis

## 终端聊天机器人

仓库包含一个简单的终端聊天脚本 `chat_cli.py`，支持在线（通过环境变量 `OPENAI_API_KEY`）和离线回退两种模式。

运行示例：

```bash
python chat_cli.py
```

若要启用在线模式（示例使用 OpenAI 兼容 SDK）：

```bash
export OPENAI_API_KEY="你的_api_key"
export OPENAI_MODEL="gpt-3.5-turbo"  # 可选
python chat_cli.py
```

在没有设置 API key 时，脚本会自动使用离线简单回复。
