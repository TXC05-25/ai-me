"""
调试脚本：在启动后端时打印关键环境变量
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("调试：检查 LLM API Key 加载")
print("=" * 60)

# 模拟 config.py 的加载逻辑
ROOT_DIR = Path(__file__).resolve().parent.parent
print(f"ROOT_DIR: {ROOT_DIR}")
print(f".env path: {ROOT_DIR / '.env'}")
print(f".env exists: {(ROOT_DIR / '.env').exists()}")

# 加载 .env
load_dotenv(ROOT_DIR / ".env")

# 读取关键环境变量
key = os.getenv("LLM_API_KEY", "")
print(f"\nLLM_API_KEY length: {len(key)}")
print(f"LLM_API_KEY first 20: {key[:20] if key else '(EMPTY)'}")
print(f"LLM_BASE_URL: {os.getenv('LLM_BASE_URL', '')}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '(not set)')[:20] if os.getenv('OPENAI_API_KEY') else '(not set)'}")

# 测试 LangChain ChatOpenAI 构造
print("\n=== LangChain ChatOpenAI 构造 ===")
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import asyncio

try:
    chat = ChatOpenAI(
        model="abab6.5s-chat",
        api_key=key,
        base_url="https://api.minimax.chat/v1",
        temperature=0.1,
    )
    print(f"  ChatOpenAI 构造 OK")
    print(f"  api_key in chat: {bool(chat.openai_api_key)}")
    print(f"  api_key length: {len(chat.openai_api_key or '')}")

    # 实际调用
    print("\n  测试调用...")

    async def call():
        resp = await chat.ainvoke([HumanMessage(content="说一个字: 好")])
        return resp
    result = asyncio.run(call())
    print(f"  ✓ LLM response: '{result.content}'")
except Exception as e:
    print(f"  ✗ ERROR: {type(e).__name__}: {e}")