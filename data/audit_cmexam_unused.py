#!/usr/bin/env python3
"""评估 data/cmexam/ 三个 CSV 中，val.csv 与 test_with_annotations.csv 是否含未用牙科题。

背景：用户认为当前中文牙科只用了 train.csv，另两个文件（val.csv / test_with_annotations.csv）
未使用，看能否挖出更多牙科题。本脚本逐文件统计牙科题量，并与当前已用数据（data/cn_dental/）
按 uid（md5(Question||Options)[:12]）做重叠校验。

输出：
  - test_with_annotations.csv：用学科字段 Medical Discipline==口腔医学 / Clinical Department==口腔科
  - val.csv / train.csv：无学科字段，用内容级牙科关键词（CN_STRONG + dental_filter R1/R2）估算
"""
import csv
import json
import hashlib
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cn_dental_content import content_signal


def uid_of(q, o):
    return "cmexam-" + hashlib.md5((str(q) + "||" + str(o)).encode()).hexdigest()[:12]


def load_used_uids():
    used = {}
    for name in ["train", "val", "test"]:
        p = os.path.join(os.path.dirname(__file__), "cn_dental", f"{name}.jsonl")
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            used[r.get("uid", uid_of(r.get("Question", ""), r.get("Options", "")))] = name
    return used


def iter_csv(path):
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield row


def main():
    used = load_used_uids()
    print("=" * 72)
    print("已用数据 data/cn_dental/*.jsonl 的 uid 分布:")
    print("  ", dict(Counter(used.values())), "共", len(used))
    print("=" * 72)

    here = os.path.dirname(os.path.abspath(__file__))
    cm = os.path.join(here, "cmexam")

    # ---- test_with_annotations.csv：学科字段精确 ----
    print("\n[test_with_annotations.csv] (6811 行，含学科/科室标签)")
    disc, dept = [], []
    for row in iter_csv(os.path.join(cm, "test_with_annotations.csv")):
        q = row.get("Question", ""); o = row.get("Options", "")
        uid = uid_of(q, o)
        d = (row.get("Medical Discipline") or "").strip()
        c = (row.get("Clinical Department") or "").strip()
        if d == "口腔医学":
            disc.append(uid)
        if c == "口腔科":
            dept.append(uid)
    disc, dept = set(disc), set(dept)
    union = disc | dept
    print(f"  Medical Discipline==口腔医学 : {len(disc)}")
    print(f"  Clinical Department==口腔科   : {len(dept)}")
    print(f"  并集                          : {len(union)}")
    print(f"    已在 cn_dental 中 : {len(union & set(used))}")
    print(f"    未在 cn_dental 中 : {len(union - set(used))}  <-- 潜在可用")

    # ---- val.csv / train.csv：内容级关键词 ----
    for name in ["val.csv", "train.csv"]:
        print(f"\n[{name}] (无学科标签，用内容级牙科关键词估算)")
        n = 0
        dental = []
        for row in iter_csv(os.path.join(cm, name)):
            n += 1
            q = row.get("Question", ""); o = row.get("Options", "")
            hits = content_signal({"Question": q, "Options": o})
            if hits:
                dental.append((uid_of(q, o), hits[0][1] if hits else ""))
        dental_uids = {u for u, _ in dental}
        print(f"  总行数            : {n}")
        print(f"  内容命中牙科关键词: {len(dental_uids)}")
        print(f"    已在 cn_dental 中 : {len(dental_uids & set(used))}")
        print(f"    未在 cn_dental 中 : {len(dental_uids - set(used))}  <-- 潜在可用")
        # 命中词 top
        c = Counter(w for _, w in dental)
        print("  命中关键词 top15:", dict(c.most_common(15)))


if __name__ == "__main__":
    main()
