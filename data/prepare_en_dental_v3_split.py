#!/usr/bin/env python3
"""英文牙科合并+重拆（干净口径，防泄漏）。

原则（用户要求）：
  1. 书籍题(BoF/NBDE)是单一来源教材，只能进训练集，绝不能进测试集（否则背题泄漏）。
  2. MedQA/MMLU 是官方 benchmark 切分，可合并重拆（重拆后两两不相交）。
  3. 旧测试里教师答错的「难题」强制进训练集（让学生学会），不进测试集。

产出 data/en_dental_v3/{train,val,test}.jsonl（新目录，不覆盖旧的）。
"""
import json
import os
import random
import sys

D = os.path.dirname(os.path.abspath(__file__))
BOOK_SRC = {"BoF", "NBDE"}


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def dump(rows, p):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    expanded = load(os.path.join(D, "en_dental_expanded", "train.jsonl"))
    old_val = load(os.path.join(D, "en_dental", "val.jsonl"))
    old_test = load(os.path.join(D, "en_dental", "test.jsonl"))
    hard_uids = set(json.load(open(os.path.join(D, "en_dental_expanded", "hard_uids.json"), encoding="utf-8")))

    books = [r for r in expanded if r.get("source") in BOOK_SRC]
    mqmm_train = [r for r in expanded if r.get("source") not in BOOK_SRC]
    # MedQA/MMLU 全部池（train + old val + old test）
    mqmm_pool = mqmm_train + old_val + old_test

    print(f"书籍题(只进训练): {len(books)}")
    print(f"MedQA/MMLU 池: {len(mqmm_pool)}（扩张train {len(mqmm_train)} + 旧val {len(old_val)} + 旧test {len(old_test)}）")

    # 难题（旧测试教师答错）强制进训练
    hard = [r for r in mqmm_pool if r.get("uid") in hard_uids]
    rest = [r for r in mqmm_pool if r.get("uid") not in hard_uids]
    print(f"难题强制进训练: {len(hard)}")

    # 重拆 MedQA/MMLU 剩余部分（70/10/20）
    rng = random.Random(42)
    rng.shuffle(rest)
    n = len(rest)
    ntr = round(n * 0.7)
    nva = round(n * 0.1)
    mqmm_tr = rest[:ntr]
    mqmm_va = rest[ntr:ntr + nva]
    mqmm_te = rest[ntr + nva:]

    train = books + hard + mqmm_tr
    val = mqmm_va
    test = mqmm_te

    outdir = os.path.join(D, "en_dental_v3")
    os.makedirs(outdir, exist_ok=True)
    dump(train, os.path.join(outdir, "train.jsonl"))
    dump(val, os.path.join(outdir, "val.jsonl"))
    dump(test, os.path.join(outdir, "test.jsonl"))

    su = {r["uid"] for r in train}
    vu = {r["uid"] for r in val}
    tu = {r["uid"] for r in test}
    print(f"\n最终切分: train {len(train)} / val {len(val)} / test {len(test)}")
    print(f"三集两两不重叠: {not (su & vu) and not (su & tu) and not (vu & tu)}")
    # 防泄漏校验：test 必须无书籍题
    test_books = sum(1 for r in test if r.get("source") in BOOK_SRC)
    print(f"test 里书籍题数（应 0）: {test_books}")
    print(f"难题是否全在 train: {hard_uids <= su}")


if __name__ == "__main__":
    main()
