"""
Multi-Agent AI Chat System

Single-file implementation that meets the requested requirements:
 - `class Agent` structure (每个 Agent 保持自己的 messages memory)
 - 使用 `client.chat.completions.create`（OpenAI Python SDK）并指定 `gpt-4.1-mini`
 - 多个 Agent 可以互相交流：一个 Agent 的回复会被追加到其他 Agent 的 messages 中
 - 随机化发言顺序 (randomized speaking order)
 - 使用 `while True` 的终端循环，支持 `KeyboardInterrupt` 退出
 - 打印格式：Agent名称: 回复内容

说明：请通过环境变量 `OPENAI_API_KEY` 或 `OPENROUTER_API_KEY` 提供 API key。
如果使用 OpenRouter，请设置 `OPENROUTER_API_KEY`（脚本会自动把请求发到 `https://openrouter.ai/api/v1`）。
"""

from __future__ import annotations

import os
import random
import sys
import time
from typing import List, Dict

try:
    from openai import OpenAI
except Exception as e:  # pragma: no cover - runtime import error handling
    raise SystemExit("无法导入 openai 库；请在虚拟环境中安装 openai: pip install openai") from e


# --------------------------- 配置 ---------------------------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTERY_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # 要求使用 gpt-4.1-mini

if OPENROUTER_KEY and not OPENAI_KEY:
    API_KEY = OPENROUTER_KEY
    BASE_URL = "https://openrouter.ai/api/v1"
else:
    API_KEY = OPENAI_KEY
    BASE_URL = None

if not API_KEY:
    raise SystemExit("未检测到 OPENAI_API_KEY 或 OPENROUTER_API_KEY；请先设置环境变量后重试。")


def create_client(api_key: str, base_url: str | None) -> OpenAI:
    """根据是否使用 OpenRouter 创建 OpenAI 客户端实例。"""
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


client = create_client(API_KEY, BASE_URL)


# --------------------------- Agent 类 ---------------------------
class Agent:
    """表示一个对话代理（Agent）。

    属性:
    - name: 代理名称，用于打印和区分消息
    - personality: 一段描述代理性格的系统提示（system message）
    - messages: 此代理的消息记忆（用于后续调用）——列表中每项都是 dict(role, content)

    方法:
    - respond(): 调用模型生成回复，并把回复追加到自己的 messages
    - receive_external(): 当其他代理说话时，将那条消息追加到本代理的 messages
    """

    def __init__(self, name: str, personality: str):
        self.name = name
        self.personality = personality
        # 初始 messages 包含系统提示，说明该 Agent 的性格与行为
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": f"You are {name}. Personality: {personality}"}
        ]

    def receive_external(self, speaker: str, text: str) -> None:
        """将其他 Agent 的发言作为用户消息追加到本 Agent 的记忆中。

        我们把其他 Agent 的发言标注为 `user` role，这样模型会基于该输入生成下一条 assistant 回复。
        """
        annotated = f"{speaker} said: {text}"
        self.messages.append({"role": "user", "content": annotated})

    def respond(self, temperature: float = 0.7, max_tokens: int = 256) -> str:
        """向 OpenAI 调用 chat.completions.create 生成回复。

        返回纯文本回复（字符串）。如遇错误，返回错误信息并保证不会破坏其他 Agent 的记忆结构。
        """
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 兼容不同 SDK 返回结构：优先取 choices[0].message.content
            content = ""
            if hasattr(resp, "choices") and resp.choices:
                choice = resp.choices[0]
                if hasattr(choice, "message") and choice.message:
                    # message 可能是 dict 或对象
                    if isinstance(choice.message, dict):
                        content = choice.message.get("content", "")
                    else:
                        content = getattr(choice.message, "content", "")
                else:
                    content = getattr(choice, "text", "")
            else:
                content = str(resp)

        except Exception as e:
            # 网络或 API 错误：返回字符串并不追加到其他 agents
            return f"[Error calling API: {e}]"

        # 将自己的回复追加到自身记忆，role 用 assistant
        self.messages.append({"role": "assistant", "content": content})
        return content


# --------------------------- 多 Agent 协调器 ---------------------------
class MultiAgentChat:
    """管理多个 Agent 并协调它们互相交流的逻辑。"""

    def __init__(self, agents: List[Agent]):
        self.agents = agents

    def broadcast_to_others(self, speaker: Agent, text: str) -> None:
        """把 speaker 的回复追加到其他所有 Agent 的记忆中。"""
        for ag in self.agents:
            if ag is speaker:
                continue
            ag.receive_external(speaker.name, text)

    def run(self) -> None:
        """主循环：随机化发言顺序，轮流让每个 Agent 生成回复，并广播给其他 Agent。"""
        round_num = 0
        try:
            while True:
                round_num += 1
                # 随机化发言顺序
                order = self.agents[:]
                random.shuffle(order)

                for agent in order:
                    # agent 生成回复
                    reply = agent.respond()
                    # 打印格式：Agent名称: 回复内容
                    print(f"{agent.name}: {reply}")
                    # 将这条回复广播给其他 agents
                    self.broadcast_to_others(agent, reply)

                    # 短暂停顿，避免请求过于频繁
                    time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n已收到中断信号，退出多 Agent 聊天。")


def main() -> None:
    """脚本入口：创建三个性格不同的 Agent 并启动多 Agent 聊天。"""
    # 创建具有不同 personality 的 agents
    agents = [
        Agent("Analyst", "理性分析型：注重事实、结构化推理、常给出步骤化解释。"),
        Agent("Emotive", "情绪化型：更富同理心和情感化措辞，常基于感受回应。"),
        Agent("Skeptic", "怀疑论型：倾向质疑前提，提出反驳或要求证据。"),
    ]

    # 可选：让用户提供一个初始话题，作为所有 agents 的第一条 user input
    try:
        initial = input("请输入讨论的初始话题（回车使用默认）：")
    except (KeyboardInterrupt, EOFError):
        print("\n输入中断，退出。")
        return

    if not initial.strip():
        initial = "Discuss the implications of AI systems collaborating together."

    # 将初始话题追加到每个 agent 的记忆（作为 user 输入）
    for ag in agents:
        ag.messages.append({"role": "user", "content": f"Initial topic: {initial}"})

    mac = MultiAgentChat(agents)
    print("启动 Multi-Agent 聊天系统（按 Ctrl+C 退出）...\n")
    mac.run()


if __name__ == "__main__":
    main()
