#!/usr/bin/env python3
"""中文全科数据准备：从 mentalDistill/15 拷贝 train/val/test，并补 uid（内容哈希）。

输出 data/cn_general/{train,val,test}.jsonl，并打印条数。
uid = "cmexam-" + md5(Question||Options)[:12]，用于零重叠校验/去重（与英文数据口径一致）。
"""
import hashlib
import json
import os

SRC = os.environ.get("MENTALDISTILL", "/home/student/arthas/mentalDistill")
D = os.path.join(SRC, "15_fulldata_resplit", "data")
OUT = os.path.join(os.path.dirname(__file__), "cn_general")
os.makedirs(OUT, exist_ok=True)


def uid_of(r):
    return "cmexam-" + hashlib.md5(
        (str(r.get("Question", "")) + "||" + str(r.get("Options", ""))).encode()
    ).hexdigest()[:12]


for name in ["train", "val", "test"]:
    rows = [json.loads(l) for l in open(os.path.join(D, f"{name}.jsonl"), encoding="utf-8") if l.strip()]
    for r in rows:
        r["uid"] = uid_of(r)
    with open(os.path.join(OUT, f"{name}.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"cn_general/{name}.jsonl: {len(rows)} 题（已补 uid）")

print("来源:", D)
print("核对: python3 data/check_dental_subset.py 不适用（这是全科，非牙科子集）")
