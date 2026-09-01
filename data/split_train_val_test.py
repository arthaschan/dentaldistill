#!/usr/bin/env python3
"""通用 train/val/test 划分（分层、可复现、零重叠）。

用法
----
    python3 data/split_train_val_test.py <输入.jsonl> <输出目录> \
        [--stratify source] [--val 0.10] [--test 0.15] [--seed 42]

说明
----
- 按指定字段分层切分，保证每个 split 的类别比例一致；
- 用 uid（或 id）去重，保证 train/val/test 三集零重叠；
- 打印每个 split 的条数与分层分布，便于人工核对。
"""
import argparse
import hashlib
import json
import os
import random
from collections import Counter, defaultdict


def load_jsonl(path):
    rows, seen = [], set()
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        uid = r.get("uid") or r.get("id") or None
        if uid is None:
            # 无 uid 则用内容哈希
            uid = hashlib.md5(json.dumps(r, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        if uid in seen:
            continue
        seen.add(uid)
        r["uid"] = uid
        rows.append(r)
    return rows


def stratify_key(r, field):
    v = r.get(field)
    if v is None or v == "":
        return "__none__"
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("outdir")
    ap.add_argument("--stratify", default="source")
    ap.add_argument("--val", type=float, default=0.10)
    ap.add_argument("--test", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    rows = load_jsonl(args.input)
    assert args.val + args.test < 1.0, "val+test 必须 < 1"

    by_key = defaultdict(list)
    for r in rows:
        by_key[stratify_key(r, args.stratify)].append(r)

    train, val, test = [], [], []
    for k, items in by_key.items():
        random.shuffle(items)
        n = len(items)
        n_test = int(round(n * args.test))
        n_val = int(round(n * args.val))
        test += items[:n_test]
        val += items[n_test:n_test + n_val]
        train += items[n_test + n_val:]
    random.shuffle(train); random.shuffle(val); random.shuffle(test)

    os.makedirs(args.outdir, exist_ok=True)
    for name, split in [("train", train), ("val", val), ("test", test)]:
        with open(os.path.join(args.outdir, f"{name}.jsonl"), "w", encoding="utf-8") as f:
            for r in split:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"输入 {len(rows)} 题 -> train {len(train)} / val {len(val)} / test {len(test)}")
    for name, split in [("train", train), ("val", val), ("test", test)]:
        c = Counter(stratify_key(r, args.stratify) for r in split)
        print(f"  {name}: {dict(c.most_common(8))}")
    # 零重叠校验
    u = lambda s: {r["uid"] for r in s}
    assert not (u(train) & u(val)) and not (u(train) & u(test)) and not (u(val) & u(test)), "split 有重叠!"
    print("  [OK] 三集零重叠")


if __name__ == "__main__":
    main()
