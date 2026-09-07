"""Test: ask about deleted projects - should not make them up"""
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
    "你在浙江省图书馆做的澜澜是干什么的",
    "给我讲讲 WorkBase 项目",
    "你在杭州亿渡网络科技实习做什么",
    "你做过最复杂的项目是什么",
]:
    ask(q)
