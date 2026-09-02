#!/usr/bin/env python3
"""牙科数据集「无非牙科」最终检查 —— 输出检查方法 + 结论。

检查对象：
  1. 中文牙科干净集 data/cn_dental_clean/{train,val,test}.jsonl（545 题）
  2. 英文牙科 data/en_dental/{train,val,test}.jsonl（676 题，R1 严格口径）

检查方法：
  中文：每道题须命中「内容级牙科关键词(C1) 或 临床科室=口腔科(D3)」；对非口腔科科室的题，
        额外确认其内容命中牙科关键词（这些题此前已人工逐题复核，见 reports/cn_dental_rescreen_report.md）。
  英文：每道题须命中 R1 强牙科词（tooth/dental/gingivitis/periodontal/…）；不得有「仅 R2 oral 语境」的题。

退出码：0 = 两个数据集均无非牙科；非 0 = 发现疑似非牙科题。
"""
import json
import os
import sys
from collections import Counter

DD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(DD, "data"))
from check_cn_dental_content import content_signal, dept_signal, dental_signal  # noqa: E402
from dental_filter import dental_match, dental_match_strict, question_text  # noqa: E402


def load(p):
    rows = []
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main():
    problems = []

    # ---- 1. 中文牙科干净集 ----
    print("=" * 70)
    print("1. 中文牙科干净集 data/cn_dental_clean/")
    print("=" * 70)
    cn_total = 0
    cn_dept_counter = Counter()
    for split in ["train", "val", "test"]:
        rows = load(os.path.join(DD, f"data/cn_dental_clean/{split}.jsonl"))
        cn_total += len(rows)
        nodental = []
        nonoral_without_keyword = []
        for r in rows:
            dept = str(r.get("Clinical Department") or "")
            cn_dept_counter[dept] += 1
            if not dental_signal(r):
                nodental.append(r.get("uid"))
            # 非口腔科科室的题，必须还有内容关键词（否则就是靠科室字段误收）
            if "口腔" not in dept and not content_signal(r):
                nonoral_without_keyword.append(r.get("uid"))
        print(f"  {split}: {len(rows)} 题，无非牙科信号={len(nodental)}，非口腔科且无关键词={len(nonoral_without_keyword)}")
        if nodental:
            problems += [(f"cn/{split}", u) for u in nodental]
        if nonoral_without_keyword:
            problems += [(f"cn/{split}/非口腔科无关键词", u) for u in nonoral_without_keyword]
    print(f"  中文干净集合计 {cn_total} 题")
    print(f"  Clinical Department 分布: {dict(cn_dept_counter)}")

    # ---- 2. 英文牙科（R1 严格） ----
    print()
    print("=" * 70)
    print("2. 英文牙科 data/en_dental/（R1 严格口径）")
    print("=" * 70)
    en_total = 0
    for split in ["train", "val", "test"]:
        rows = load(os.path.join(DD, f"data/en_dental/{split}.jsonl"))
        en_total += len(rows)
        r2only = 0
        no_r1 = 0
        for r in rows:
            hits = dental_match(question_text(r))
            if not any(h[0] == "R1" for h in hits):
                no_r1 += 1
            if hits and all(h[0] == "R2" for h in hits):
                r2only += 1
        print(f"  {split}: {len(rows)} 题，无 R1 命中={no_r1}，仅 R2={r2only}")
        if no_r1:
            problems += [(f"en/{split}/无R1", u) for u in
                         [r.get("uid") for r in rows
                          if not any(h[0] == "R1" for h in dental_match(question_text(r)))]]
    print(f"  英文牙科合计 {en_total} 题")

    print()
    if problems:
        print(f"[FAIL] 发现 {len(problems)} 处疑似非牙科：{problems[:20]}")
        sys.exit(1)
    print(f"[PASS] 中文牙科 {cn_total} 题 + 英文牙科 {en_total} 题，全部为牙科，无非牙科数据。")


if __name__ == "__main__":
    main()
