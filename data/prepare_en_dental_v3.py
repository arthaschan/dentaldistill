#!/usr/bin/env python3
"""用放宽后的 R1（v3，补口腔内科/唾液腺词）重建英文牙科训练集。

- 从 en_general/train 用 is_dental_record_strict(放宽版) 重筛，回收口腔内科牙科题。
- 从 books_singlebest(BoF+NBDE) 重筛。
- 去重 + 避开 val/test（val/test 保持原 26/84 不动，保证评测可比）。
输出 data/en_dental/train_v3.jsonl。
"""
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from dental_filter import is_dental_record_strict, question_text  # noqa: E402


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def dump(rows, p):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    # 重筛 en_general train（放宽 R1）
    gen_train = load(os.path.join(D, "en_general", "train.jsonl"))
    dental = [r for r in gen_train if is_dental_record_strict(r)[0]]
    print(f"en_general/train: {len(gen_train)} -> 牙科(放宽R1) {len(dental)}")

    # 重筛书籍（BoF+NBDE）
    books = load(os.path.join(os.path.dirname(D), "books", "books_singlebest.jsonl"))
    book_dental = [r for r in books if is_dental_record_strict(r)[0]]
    print(f"books_singlebest: {len(books)} -> 牙科(放宽R1) {len(book_dental)}")

    # 合并 + 去重 + 避开 val/test
    val_uids = {r.get("uid") for r in load(os.path.join(D, "en_dental", "val.jsonl"))}
    test_uids = {r.get("uid") for r in load(os.path.join(D, "en_dental", "test.jsonl"))}
    seen = set()
    merged = []
    for r in dental + book_dental:
        uid = r.get("uid")
        if uid in seen or uid in val_uids or uid in test_uids:
            continue
        seen.add(uid)
        merged.append(r)
    dump(merged, os.path.join(D, "en_dental", "train_v3.jsonl"))
    print(f"en_dental/train_v3: {len(merged)} 题（原 train 566）")

    # 与旧 train 对比
    old_uids = {r.get("uid") for r in load(os.path.join(D, "en_dental", "train.jsonl"))}
    new_added = [r for r in merged if r.get("uid") not in old_uids]
    print(f"  新增 {len(new_added)} 题（放宽过滤回收的牙科题）")


if __name__ == "__main__":
    main()
