#!/usr/bin/env python3
"""中文牙科数据准备：从 CMExam 全科拆出「口腔医学」学科（学科字段，非关键词），并补 uid。

- train：从 15 的全科 train(4608) 里筛 Medical Discipline == "口腔医学" -> 580
- val  ：15 的 val_dental.jsonl（125）
- test ：15 的 test_dental.jsonl（125）

拆分方法 = 学科字段过滤，100% 可靠、无 "oral" 误判风险。
输出 data/cn_dental/{train,val,test}.jsonl（含 uid），并打印条数。
"""
import hashlib
import json
import os

SRC = os.environ.get("MENTALDISTILL", "/home/student/arthas/mentalDistill")
D = os.path.join(SRC, "15_fulldata_resplit", "data")
OUT = os.path.join(os.path.dirname(__file__), "cn_dental")
os.makedirs(OUT, exist_ok=True)

DISC = "口腔医学"


def uid_of(r):
    return "cmexam-" + hashlib.md5(
        (str(r.get("Question", "")) + "||" + str(r.get("Options", ""))).encode()
    ).hexdigest()[:12]


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def dump(rows, path):
    for r in rows:
        r["uid"] = uid_of(r)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# train: 从全科训练集筛口腔医学
train = [r for r in load(os.path.join(D, "train.jsonl")) if r.get("Medical Discipline") == DISC]
dump(train, os.path.join(OUT, "train.jsonl"))

for name, dst in [("val_dental", "val"), ("test_dental", "test")]:
    dump(load(os.path.join(D, f"{name}.jsonl")), os.path.join(OUT, f"{dst}.jsonl"))

print(f"cn_dental/train.jsonl: {len(train)} 题（学科={DISC}）")
for name in ["val", "test"]:
    n = sum(1 for _ in open(os.path.join(OUT, f"{name}.jsonl"), encoding="utf-8"))
    print(f"cn_dental/{name}.jsonl: {n} 题")

print("\n核对（应 [PASS]）:")
print("  python3 data/check_dental_subset.py data/cn_dental/train.jsonl")
