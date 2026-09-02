"""
验证 AI-Me 数据是否完整填充
"""

from pathlib import Path
import yaml
import json

BASE = Path(__file__).resolve().parent.parent / "backend" / "data"


def main():
    print("===== profile.yaml =====")
    profile = yaml.safe_load((BASE / "profile.yaml").read_text(encoding="utf-8"))
    print("name:    ", profile.get("name"))
    print("title:   ", profile.get("title"))
    print("email:   ", profile.get("email"))
    print("phone:   ", profile.get("phone") or "(不公开)")
    print("github:  ", profile.get("github"))
    print("school:  ", profile["education"][0]["school"])
    print("major:   ", profile["education"][0]["major"])
    print("intern:  ", profile["experience"][0]["company"], profile["experience"][0]["period"])
    print("projects:", len(profile["projects"]))
    for p in profile["projects"]:
        print("  -", p["id"], ":", p["name"][:40])

    print()
    print("===== resume.md =====")
    resume = (BASE / "resume.md").read_text(encoding="utf-8")
    print(f"长度: {len(resume)} 字符")
    print(f"开头: {resume.split(chr(10))[0]}")

    print()
    print("===== qa_pairs.jsonl =====")
    pairs = [json.loads(l) for l in (BASE / "qa_pairs.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]
    print(f"共 {len(pairs)} 条问答")
    print("前 5 个问题:")
    for p in pairs[:5]:
        print(f"  [{p['intent']}] {p['question']}")

    print()
    print("===== projects/ 目录 =====")
    for f in sorted((BASE / "projects").glob("*.md")):
        print(f"  - {f.name} ({f.stat().st_size} B)")


if __name__ == "__main__":
    main()