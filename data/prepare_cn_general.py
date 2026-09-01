#!/usr/bin/env python3
"""中文全科数据准备：从 mentalDistill/15 拷贝 train/val/test（不改划分）。

输出 data/cn_general/{train,val,test}.jsonl，并打印条数。
"""
import os
import shutil

SRC = os.environ.get("MENTALDISTILL", "/home/student/arthas/mentalDistill")
D = os.path.join(SRC, "15_fulldata_resplit", "data")
OUT = os.path.join(os.path.dirname(__file__), "cn_general")
os.makedirs(OUT, exist_ok=True)

for name in ["train", "val", "test"]:
    src = os.path.join(D, f"{name}.jsonl")
    dst = os.path.join(OUT, f"{name}.jsonl")
    shutil.copyfile(src, dst)
    n = sum(1 for _ in open(dst, encoding="utf-8"))
    print(f"cn_general/{name}.jsonl: {n} 题")

print("来源:", D)
print("核对: python3 data/check_dental_subset.py 不适用（这是全科，非牙科子集）")
