"""直接测 DeepSeek API"""
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(r'C:\Users\谭修诚\Desktop\ai-me\.env'))
api_key = os.getenv('LLM_API_KEY')
base_url = os.getenv('LLM_BASE_URL', '').rstrip('/')
model = os.getenv('LLM_MODEL')

print(f"base_url: {base_url}")
print(f"model: {model}")
print(f"api_key first 10: {api_key[:10]}")

try:
    resp = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "回复一个字: 好"}],
            "max_tokens": 20,
        },
        timeout=30,
    )
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")