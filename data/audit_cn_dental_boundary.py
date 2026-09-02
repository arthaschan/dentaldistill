#!/usr/bin/env python3
"""任务3 第1步：抽出被内容过滤器剔除的题，按临床科室归类，重点列出「口腔科室但无关键词」的边界题。

用法: python3 data/audit_cn_dental_boundary.py [in=data/cn_dental] [out=reports/cn_boundary_review.md]
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cn_dental_content import content_signal, question_text  # noqa: E402


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
    indir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "cn_dental")
    out = sys.argv[2] if len(sys.argv) > 2 else "reports/cn_boundary_review.md"

    boundary = []          # 被剔除 + 科室含「口腔」
    nonoral = []           # 被剔除 + 科室非口腔
    for name in ["train", "val", "test"]:
        for r in load(os.path.join(indir, f"{name}.jsonl")):
            sig = content_signal(r)
            if sig:
                continue
            dept = str(r.get("Clinical Department") or "")
            rec = dict(r, _split=name)
            if "口腔" in dept:
                boundary.append(rec)
            else:
                nonoral.append(rec)

    print(f"被剔除总题数: {len(boundary) + len(nonoral)}")
    print(f"  口腔科室边界题(需复核): {len(boundary)}")
    print(f"  非口腔科室(高置信非牙科): {len(nonoral)}")
    print(f"\n边界题科室分布: {dict(Counter(str(r.get('Clinical Department')) for r in boundary))}")
    print(f"非口腔题科室分布: {dict(Counter(str(r.get('Clinical Department')) for r in nonoral))}")

    lines = ["# 中文牙科「口腔科室但内容无关键词」边界题复核清单\n",
             f"> 被内容过滤器剔除、但 Clinical Department 含「口腔」的题共 {len(boundary)} 道。\n",
             "> 这些题多数是真牙科（关键词表漏了专业术语），需逐题复核分类。\n\n"]
    for r in sorted(boundary, key=lambda x: (x["_split"], x.get("uid", ""))):
        lines.append(f"## [{r['_split']}] uid={r.get('uid')} 科室={r.get('Clinical Department')} 疾病组={r.get('Disease Group')}\n")
        lines.append(f"- 题干: {r.get('Question', '')}\n")
        lines.append(f"- 选项: {r.get('Options', '')}\n")
        lines.append(f"- 答案: {r.get('Answer', '')}\n")
        lines.append(f"- 解析: {r.get('Explanation', '')}\n\n")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print(f"\n已写 {out}")

    # 也把非口腔题清单落盘（供抽查）
    nonoral_out = out.replace("boundary_review", "nonoral_dropped")
    l2 = ["# 中文牙科「非口腔科室且无关键词」被剔除题清单\n",
          f"> 共 {len(nonoral)} 道，高置信非牙科（通科医学）。\n\n"]
    for r in sorted(nonoral, key=lambda x: (x["_split"], x.get("uid", ""))):
        l2.append(f"- [{r['_split']}] uid={r.get('uid')} 科室={r.get('Clinical Department')} | {r.get('Question','')[:80]}\n")
    with open(nonoral_out, "w", encoding="utf-8") as f:
        f.write("".join(l2))
    print(f"已写 {nonoral_out}")


if __name__ == "__main__":
    main()
