#!/usr/bin/env python3
"""把 2 本单选书（BoF + NBDE）并入英文全科 train。

- 输入：books/books_singlebest.jsonl（= BoF 272 + NBDE 366 = 638，规整后单选 A–E）。
- 并入：data/en_general/train.jsonl（仅 train，test 固定 4110 保持 MedQA/MMLU 不动，val 不动）。
- 去重：按 uid 去重（书 uid 前缀 BoF-*/NBDE-*，与 medqa_*/mmlu_* 天然不冲突），
        并确保不与 val/test 重叠。
- 可选 --filter-dental：只并入命中牙科判定（R1/R2）的题（默认关闭——英文全科是通科，
        两本书里 Human Disease/Pharmacology 等非牙科章节对全科也是有效题目）。

用法
----
    python3 data/merge_books_into_en_general.py [--filter-dental]

幂等：若 train 里已存在 source∈{BoF,NBDE} 的记录，则先移除再重并（可安全重跑）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dental_filter import is_dental_record  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BOOKS = os.path.join(HERE, "..", "books", "books_singlebest.jsonl")
EN_GEN = os.path.join(HERE, "en_general")
FILTER_DENTAL = "--filter-dental" in sys.argv


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def dump(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    books = load(BOOKS)
    print(f"books_singlebest.jsonl: {len(books)} 题（BoF+NBDE 单选）")

    train = load(os.path.join(EN_GEN, "train.jsonl"))
    val = load(os.path.join(EN_GEN, "val.jsonl"))
    test = load(os.path.join(EN_GEN, "test.jsonl"))
    print(f"en_general 现状: train {len(train)} / val {len(val)} / test {len(test)}")

    # 幂等：先剔除此前并入的书题
    book_sources = {"BoF", "NBDE"}
    train = [r for r in train if r.get("source") not in book_sources]

    # 去重 + 避开 val/test
    existing = {r.get("uid") for r in train + val + test}
    add = [r for r in books if r.get("uid") not in existing]

    if FILTER_DENTAL:
        kept = [r for r in add if is_dental_record(r)[0]]
        print(f"[--filter-dental] {len(add)} -> 命中牙科 {len(kept)}（剔除 {len(add) - len(kept)}）")
        add = kept

    # 规整选项为 "A. text"（与 en_general 一致），保证训练口径统一
    for r in add:
        opts = r.get("Options", "")
        if opts and not opts.strip().startswith(("A.", "A ")):
            # 已是 "A text" 形式，补句点
            lines = []
            for ln in opts.split("\n"):
                if ln and ln[0] in "ABCDE" and (len(ln) == 1 or ln[1] == " "):
                    lines.append(ln[0] + "." + ln[1:])
                else:
                    lines.append(ln)
            r["Options"] = "\n".join(lines)

    train += add
    dump(train, os.path.join(EN_GEN, "train.jsonl"))

    print(f"\n并入 train {len(add)} 题 -> en_general/train.jsonl 现 {len(train)} 题")
    from collections import Counter
    print("train source 分布:", dict(Counter(r.get("source") for r in train)))
    # 零重叠校验
    u = lambda s: {r["uid"] for r in s}
    t, v = load(os.path.join(EN_GEN, "train.jsonl")), load(os.path.join(EN_GEN, "val.jsonl"))
    assert not (u(t) & u(v)) and not (u(t) & u(test)) and not (u(v) & u(test)), "重叠!"
    print("[OK] train/val/test 零重叠")


if __name__ == "__main__":
    main()
