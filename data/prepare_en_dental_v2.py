#!/usr/bin/env python3
"""英文牙科重新切分：合并 train_v3(631)+val(26)+test(84)=741，去重，重打乱，重切。

背景：英文牙科旧口径 test 84 太小（±1 题就 1.19pp），与中文侧「test 放大」同理，
把全部英文牙科题合池重切，产出更大的 test。英文池子小（741），test 只能到 ~148（20%）。

口径：train_v3 是放宽 R1 后的完整牙科（631），val/test 是原 R1 严格（26/84），
三者 uid 互不重叠（train_v3 已在 prepare_en_dental_v3.py 里避开 val/test）。

产出 data/en_dental_v2/{train,val,test}.jsonl（默认 70/10/20）。
"""
import json
import os
import random
import sys

D = os.path.dirname(os.path.abspath(__file__))


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def dump(rows, p):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    en = os.path.join(D, "en_dental")
    train = load(os.path.join(en, "train_v3.jsonl"))
    val = load(os.path.join(en, "val.jsonl"))
    test = load(os.path.join(en, "test.jsonl"))
    print(f"train_v3 {len(train)} / val {len(val)} / test {len(test)}")

    seen = set()
    merged = []
    for r in train + val + test:
        uid = r.get("uid")
        if uid in seen:
            continue
        seen.add(uid)
        merged.append(r)
    print(f"合并去重后: {len(merged)}")

    rng = random.Random(42)
    rng.shuffle(merged)

    tr, va, te = (0.7, 0.1, 0.2)
    if len(sys.argv) > 1:
        tr, va, te = (float(x) for x in sys.argv[1].split("/"))
    n = len(merged)
    ntr = round(n * tr)
    nva = round(n * va)
    nte = n - ntr - nva
    tr_r = merged[:ntr]
    va_r = merged[ntr:ntr + nva]
    te_r = merged[ntr + nva:]

    outdir = os.path.join(D, sys.argv[2] if len(sys.argv) > 2 else "en_dental_v2")
    os.makedirs(outdir, exist_ok=True)
    dump(tr_r, os.path.join(outdir, "train.jsonl"))
    dump(va_r, os.path.join(outdir, "val.jsonl"))
    dump(te_r, os.path.join(outdir, "test.jsonl"))

    su = {r["uid"] for r in tr_r}
    vu = {r["uid"] for r in va_r}
    tu = {r["uid"] for r in te_r}
    print(f"切分 {tr:.0%}/{va:.0%}/{te:.0%}: train {len(tr_r)} / val {len(va_r)} / test {len(te_r)}")
    print(f"三集不重叠: {not (su & vu) and not (su & tu) and not (vu & tu)}")


if __name__ == "__main__":
    main()
