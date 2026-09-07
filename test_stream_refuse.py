"""Test /chat/stream with refused question - should now hit refuse_node"""
import json
import urllib.request


def ask_stream(question):
    print(f"\n=== Asking (stream): {question} ===")
    body = json.dumps({"question": question}).encode()
    req = urllib.request.Request(
        "http://localhost:8000/chat/stream",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        for line in resp:
            print(line.decode().rstrip())
    except Exception as e:
        print("ERROR:", e)


ask_stream("你有没有女朋友")
ask_stream("你叫什么名字")
