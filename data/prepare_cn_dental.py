#!/usr/bin/env python3
"""中文牙科数据准备：从 CMExam 全科拆出「口腔医学」学科（学科字段，非关键词）。

- train：从 15 的全科 train(4608) 里筛 Medical Discipline == "口腔医学" -> 580
- val  ：15 的 val_dental.jsonl（125）
- test ：15 的 test_dental.jsonl（125）

拆分方法 = 学科字段过滤，100% 可靠、无 "oral" 误判风险。
输出 data/cn_dental/{train,val,test}.jsonl，并打印条数与学科分布。
"""
import json
import os
import shutil

SRC = os.environ.get("MENTALDISTILL", "/home/student/arthas/mentalDistill")
D = os.path.join(SRC, "15_fulldata_resplit", "data")
OUT = os.path.join(os.path.dirname(__file__), "cn_dental")
os.makedirs(OUT, exist_ok=True)

DISC = "口腔医学"

# train: 从全科训练集筛口腔医学
train = []
for line in open(os.path.join(D, "train.jsonl"), encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if r.get("Medical Discipline") == DISC:
        train.append(r)

with open(os.path.join(OUT, "train.jsonl"), "w", encoding="utf-8") as f:
    for r in train:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

for name in ["val_dental", "test_dental"]:
    dst_name = "val" if name == "val_dental" else "test"
    shutil.copyfile(os.path.join(D, f"{name}.jsonl"), os.path.join(OUT, f"{dst_name}.jsonl"))

print(f"cn_dental/train.jsonl: {len(train)} 题（学科={DISC}）")
for name in ["val", "test"]:
    n = sum(1 for _ in open(os.path.join(OUT, f"{name}.jsonl"), encoding="utf-8"))
    print(f"cn_dental/{name}.jsonl: {n} 题")

print("\n核对（应输出 [PASS]，且 train/val/test 学科全为口腔医学）:")
print(f"  python3 data/check_dental_subset.py data/cn_dental/train.jsonl")
