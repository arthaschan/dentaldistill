#!/usr/bin/env python3
"""英文牙科数据准备：从英文全科（MedQA+MMLU）筛牙科 + 并入 3 本书。

- 第一步：对 data/en_general/{train,val,test}.jsonl 逐题跑收紧后的牙科判定
          （dental_filter.py），只保留牙科题，且 train/val/test 维持零重叠。
- 第二步（可选）：并入 books/ 下提取出的牙科题（source=BoF/NBDE/MCQ），
          与已有题去重，并入 train；避免与 test 重叠。
- 第三步：用 check_dental_subset.py 审计（应 [PASS]）。

输出 data/en_dental/{train,val,test}.jsonl。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dental_filter import is_dental_record, question_text  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "en_dental")
EN_GEN = os.path.join(os.path.dirname(__file__), "en_general")
BOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "books")
os.makedirs(OUT, exist_ok=True)


def load(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def dump(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# 1) 从英文全科筛牙科
splits = {}
for name in ["train", "val", "test"]:
    rows = load(os.path.join(EN_GEN, f"{name}.jsonl"))
    dental, dropped = [], 0
    for r in rows:
        ok, hits = is_dental_record(r)
        if ok:
            dental.append(r)
        else:
            dropped += 1
    splits[name] = dental
    print(f"en_general/{name}: {len(rows)} -> 牙科 {len(dental)}（筛掉 {dropped}）")

# 2) 并入书籍（若 books/ 已有提取产物）
book_dental = []
for fname in ["books_bof.jsonl", "books_nbde.jsonl", "books_mcq.jsonl"]:
    p = os.path.join(BOOKS_DIR, fname)
    if os.path.exists(p):
        rows = load(p)
        kept = [r for r in rows if is_dental_record(r)[0]]
        book_dental += kept
        print(f"并入 {fname}: {len(rows)} -> 牙科 {len(kept)}")
if book_dental:
    existing_uids = {r.get("uid") for r in splits["train"] + splits["val"] + splits["test"]}
    test_uids = {r.get("uid") for r in splits["test"]}
    add = [r for r in book_dental if r.get("uid") not in existing_uids and r.get("uid") not in test_uids]
    splits["train"] += add
    print(f"书籍净并入 train: {len(add)} 题（去重、避开 test）")
else:
    print("（books/ 尚无提取产物，跳过书籍并入；先跑 books/extract_*.py）")

for name in ["train", "val", "test"]:
    dump(splits[name], os.path.join(OUT, f"{name}.jsonl"))
    print(f"en_dental/{name}.jsonl: {len(splits[name])} 题")

print("\n审计命令:")
print("  python3 data/check_dental_subset.py data/en_dental/train.jsonl")
print("  python3 data/check_dental_subset.py data/en_dental/val.jsonl")
print("  python3 data/check_dental_subset.py data/en_dental/test.jsonl")
