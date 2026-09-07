"""Quick smoke test for refuse_node"""
import urllib.request
import json

def ask(question):
    print(f"\n=== Asking: {question} ===")
    req = urllib.request.Request(
        "http://localhost:8000/chat",
        data=json.dumps({"question": question}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30).read().decode()
        print("RESPONSE:", resp[:600])
    except Exception as e:
        print("ERROR:", e)

# Should be refused
for q in ["你有女朋友吗", "你谈过恋爱吗", "你单身吗", "你结婚了吗"]:
    ask(q)

# Should NOT be refused
for q in ["你叫什么名字", "你做了哪些项目", "你是怎么实现 RAG 的"]:
    ask(q)
