#!/usr/bin/env python3
"""英文全科数据准备：从 mentalDistill/27 拷贝，并切出 val。

- test：固定 = 27 的 test_no_india.jsonl（4110 = MedQA 1273 + MMLU 2837）
- train：27 的 train_no_india_dentalsplit.jsonl（10168 = MedQA 9862 + MMLU 306）
        按 source 分层切出 val（默认 10%，seed=42），其余为 train。

输出 data/en_general/{train,val,test}.jsonl，并打印条数 + 来源分布 + 零重叠校验。
"""
import json
import os
import random
import shutil
from collections import Counter, defaultdict

SRC = os.environ.get("MENTALDISTILL", "/home/student/arthas/mentalDistill")
D = os.path.join(SRC, "27_english_general_noindia", "data")
OUT = os.path.join(os.path.dirname(__file__), "en_general")
VAL_RATIO = 0.10
SEED = 42
os.makedirs(OUT, exist_ok=True)

# test 固定拷贝
shutil.copyfile(os.path.join(D, "test_no_india.jsonl"), os.path.join(OUT, "test.jsonl"))


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def dump(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


train_pool = load(os.path.join(D, "train_no_india_dentalsplit.jsonl"))

# 按 source 分层切 val
random.seed(SEED)
by_src = defaultdict(list)
for r in train_pool:
    by_src[r.get("source", "__none__")].append(r)
train, val = [], []
for src, items in by_src.items():
    random.shuffle(items)
    n_val = int(round(len(items) * VAL_RATIO))
    val += items[:n_val]
    train += items[n_val:]
random.shuffle(train); random.shuffle(val)

dump(train, os.path.join(OUT, "train.jsonl"))
dump(val, os.path.join(OUT, "val.jsonl"))

# 校验
test = load(os.path.join(OUT, "test.jsonl"))
u = lambda s: {r["uid"] for r in s}
assert not (u(train) & u(val)) and not (u(train) & u(test)) and not (u(val) & u(test)), "重叠!"
print(f"en_general: train {len(train)} / val {len(val)} / test {len(test)}（零重叠 OK）")
for name, split in [("train", train), ("val", val), ("test", test)]:
    print(f"  {name} source: {dict(Counter(r.get('source') for r in split))}")
