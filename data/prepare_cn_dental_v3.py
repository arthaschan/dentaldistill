#!/usr/bin/env python3
"""合并 CMExam 三个切分的牙科题 → 去重 → 固定 seed 重打乱 → 重新切分。

背景：当前测试集只有 84 题（来自 test_with_annotations 内部重切），训练集扩到 6762 后测试集
没同步扩大，±1 题就 1.19pp，任何差异都被噪声淹没。本脚本把三个切分的牙科题合池重切，
给出更大、更可靠的 test/val，旧测试题回到池子里重新分配，一切从头训练。

口径：三个文件统一用 content_signal_strict（严格内容牙科过滤，precision ~87.3%），
      只保留 5 选项(A-E) + 单字母答案的标准题。

产出 data/cn_dental_v3/{train,val,test}.jsonl（默认 90/5/5，可用参数改）。
"""
import csv
import hashlib
import json
import os
import random
import re
import sys
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from check_cn_dental_content import content_signal_strict  # noqa: E402

OPT_LETTERS = {"A", "B", "C", "D", "E"}
_OPT_LINE_RE = re.compile(r"(?m)^([A-E])\s")


def uid_of(q, o):
    return "cmexam-" + hashlib.md5((str(q) + "||" + str(o)).encode()).hexdigest()[:12]


def option_letters(opts):
    return sorted(set(_OPT_LINE_RE.findall(opts or "")))


def load_csv(path, source):
    out = []
    for row in csv.DictReader(open(path, encoding="utf-8")):
        q = (row.get("Question") or "").strip()
        o = (row.get("Options") or "").strip()
        a = (row.get("Answer") or "").strip().upper()
        if option_letters(o) != ["A", "B", "C", "D", "E"] or a not in OPT_LETTERS:
            continue
        if not content_signal_strict({"Question": q, "Options": o}):
            continue
        out.append({
            "Question": q, "Options": o, "Answer": a,
            "Explanation": (row.get("Explanation") or "").strip(),
            "uid": uid_of(q, o), "source": source,
        })
    return out


def dump(rows, p):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    cm = os.path.join(D, "cmexam")
    train_r = load_csv(os.path.join(cm, "train.csv"), "train")
    val_r = load_csv(os.path.join(cm, "val.csv"), "val")
    test_r = load_csv(os.path.join(cm, "test_with_annotations.csv"), "test")
    print(f"train.csv 严格牙科: {len(train_r)}")
    print(f"val.csv   严格牙科: {len(val_r)}")
    print(f"test.csv  严格牙科: {len(test_r)}")

    # 合并去重
    seen = set()
    merged = []
    for r in train_r + val_r + test_r:
        if r["uid"] in seen:
            continue
        seen.add(r["uid"])
        merged.append(r)
    print(f"合并去重后总数: {len(merged)}")
    print(f"  来源分布: {dict(Counter(r['source'] for r in merged))}")

    # 固定 seed 重打乱
    rng = random.Random(42)
    rng.shuffle(merged)

    # 切分比例
    tr, va, te = (0.9, 0.05, 0.05)
    if len(sys.argv) > 1:
        tr, va, te = (float(x) for x in sys.argv[1].split("/"))
    n = len(merged)
    ntr = round(n * tr)
    nva = round(n * va)
    nte = n - ntr - nva
    train = merged[:ntr]
    val = merged[ntr:ntr + nva]
    test = merged[ntr + nva:]

    outdir = os.path.join(D, sys.argv[2] if len(sys.argv) > 2 else "cn_dental_v3")
    os.makedirs(outdir, exist_ok=True)
    dump(train, os.path.join(outdir, "train.jsonl"))
    dump(val, os.path.join(outdir, "val.jsonl"))
    dump(test, os.path.join(outdir, "test.jsonl"))

    print(f"\n切分 {tr:.0%}/{va:.0%}/{te:.0%}:")
    print(f"  train {len(train)} / val {len(val)} / test {len(test)}")

    # 校验：三集 uid 互不重叠
    su = {r["uid"] for r in train}
    vu = {r["uid"] for r in val}
    tu = {r["uid"] for r in test}
    print(f"  三集两两不重叠: {len(su & vu) == 0 and len(su & tu) == 0 and len(vu & tu) == 0}")
    print(f"  test 答案分布: {dict(sorted(Counter(r['Answer'] for r in test).items()))}")


if __name__ == "__main__":
    main()
