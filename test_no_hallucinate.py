"""Test: ask about non-existent projects, should fall back to 'no data' message"""
import json
import urllib.request


def ask(question):
    print(f"\n=== Q: {question} ===")
    try:
        req = urllib.request.Request(
            "http://localhost:8000/chat/stream",
            data=json.dumps({"question": question}).encode(),
            headers={"Content-Type": "application/json"},
        )
        for line in urllib.request.urlopen(req, timeout=45):
            line = line.decode().rstrip()
            if line.startswith("event: done"):
                d = json.loads(line[5:].strip())
                print("ANSWER:", d.get("answer", "")[:300])
                print("CITATIONS:", len(d.get("citations", [])))
                print("INTENT:", d.get("intent"))
                return
    except Exception as e:
        print("ERROR:", e)


for q in [
    "澜澜是什么",
    "WorkBase 项目呢",
    "FlashAttention 原理是什么",  # 这个有答案
    "你在哪家公司实习",          # profile_qa 应正常召回
    "石斑鱼呢是什么",            # 完全没意义的词
]:
    ask(q)
