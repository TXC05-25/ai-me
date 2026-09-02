"""
启动后端调试版本：打印启动时的环境变量状态
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# ===== 关键：在 import config 之前打印 =====
print("=" * 60)
print("启动调试信息")
print("=" * 60)
print(f"cwd: {os.getcwd()}")
print(f"__file__: {__file__}")
print(f"Path(__file__).resolve(): {Path(__file__).resolve()}")
print(f"Path(__file__).resolve().parent: {Path(__file__).resolve().parent}")
print(f"Path(__file__).resolve().parent.parent: {Path(__file__).resolve().parent.parent}")

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / '.env'
print(f"\n计算出的 ROOT_DIR: {ROOT_DIR}")
print(f"计算出的 .env 路径: {ENV_PATH}")
print(f".env exists: {ENV_PATH.exists()}")

# 加载 .env
load_dotenv(ENV_PATH)

# 检查
key = os.getenv('LLM_API_KEY', '')
print(f"\n加载后 LLM_API_KEY 长度: {len(key)}")
print(f"加载后 LLM_API_KEY 首字符: '{key[:5]}'" if key else "LLM_API_KEY 为空")

# 现在才 import config
print("\n现在导入 config...")
import sys
sys.path.insert(0, str(ROOT_DIR / 'backend'))
from config import LLM_API_KEY as CK, LLM_BASE_URL as CB, LLM_MODEL as CM, ROOT_DIR as CONFIG_ROOT
print(f"config.ROOT_DIR: {CONFIG_ROOT}")
print(f"config.LLM_API_KEY 长度: {len(CK)}")
print(f"config.LLM_API_KEY 首字符: '{CK[:5]}'" if CK else "config.LLM_API_KEY 为空")

# 测试用 config 中的值构造 ChatOpenAI
print("\n测试 ChatOpenAI + 实际调用...")
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import asyncio

if not CK:
    print("✗ LLM_API_KEY 为空，无法测试")
else:
    chat = ChatOpenAI(model=CM, api_key=CK, base_url=CB, temperature=0.1)
    async def call():
        return await chat.ainvoke([HumanMessage(content="一个字: 好")])
    try:
        result = asyncio.run(call())
        print(f"OK LLM response: {result.content[:50]}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("调试完成")
print("=" * 60)