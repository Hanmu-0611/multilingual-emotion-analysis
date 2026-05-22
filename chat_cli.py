import os
import sys
from typing import List, Dict

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
API_KEY = OPENAI_KEY or OPENROUTER_KEY
BASE_URL = "https://openrouter.ai/api/v1" if OPENROUTER_KEY and not OPENAI_KEY else None
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


def local_reply(text: str) -> str:
    t = text.strip()
    if not t:
        return "你没有输入内容。"
    if any(g in t.lower() for g in ("hi", "hello", "你好", "嗨")):
        return "你好！当前为离线模式，设置 OPENAI_API_KEY 可启用在线模型。"
    return f"（离线）我收到：{t}（{len(t)} 字符）"


class Agent:
    def __init__(self, client=None):
        self.client = client
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": "你是一个简洁友好的助手，尽量使用中文回复。"}
        ]

    def respond(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        if not self.client:
            return local_reply(user_message)

        try:
            resp = self.client.chat.completions.create(model=MODEL, messages=self.messages)
            # 兼容不同 SDK 返回结构
            if hasattr(resp, "choices") and resp.choices:
                choice = resp.choices[0]
                if hasattr(choice, "message") and choice.message:
                    content = choice.message.get("content") or getattr(choice.message, "content", "")
                else:
                    content = getattr(choice, "text", "")
            else:
                content = str(resp)
        except Exception as e:
            return f"API 请求出错：{e}"

        self.messages.append({"role": "assistant", "content": content})
        return content


def create_client(api_key: str, base_url: str | None):
    try:
        from openai import OpenAI
    except Exception:
        return None
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def main():
    client = None
    if API_KEY:
        client = create_client(API_KEY, BASE_URL)
        if client is None:
            print("无法导入 openai 客户端。请在虚拟环境中安装 openai 库，或取消设置 API key 以使用离线模式。")

    agent = Agent(client)

    print("聊天开始。输入 exit 或 Ctrl+C 退出。")
    while True:
        try:
            user_input = input("你: ")
        except (KeyboardInterrupt, EOFError):
            print("\n退出")
            return
        if user_input.strip().lower() in ("exit", "quit"):
            print("退出")
            return
        reply = agent.respond(user_input)
        print("机器人:", reply)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("运行时错误：", e)
        sys.exit(1)