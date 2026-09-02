#!/usr/bin/env python3
"""审计新干净集：按临床科室分布，列出所有「非口腔科」题（它们只靠内容关键词保留），供人工核对是否误收。"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cn_dental_content import content_signal  # noqa: E402


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "cn_dental_clean")
    total = Counter()
    nonoral = []
    for name in ["train", "val", "test"]:
        for r in load(os.path.join(outdir, f"{name}.jsonl")):
            dept = str(r.get("Clinical Department") or "")
            total[dept] += 1
            if "口腔" not in dept:
                nonoral.append((name, r))

    print("=== 新干净集 Clinical Department 分布 ===")
    for k, v in total.most_common():
        print(f"  {k}: {v}")
    print(f"\n非口腔科题(只靠内容关键词保留): {len(nonoral)} 题\n")

    for name, r in sorted(nonoral, key=lambda x: (x[1].get("Clinical Department", ""), x[1].get("uid", ""))):
        sig = content_signal(r)
        hits = "|".join(w for _, w in sig)
        print(f"[{name}] 科室={r.get('Clinical Department')} uid={r.get('uid')}")
        print(f"  命中词: {hits}")
        print(f"  Q: {r.get('Question', '')[:70]}")


if __name__ == "__main__":
    main()
