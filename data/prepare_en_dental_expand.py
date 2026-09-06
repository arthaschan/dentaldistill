#!/usr/bin/env python3
"""英文牙科训练数据扩张：书籍题按 source 全部纳入 + MedQA/MMLU 严格过滤。

背景：书籍题(BoF=Best of Fives, NBDE=National Board Dental Examination)是牙科教材，
subject 字段全是牙科主题(Periodontics/Endodontics/Prosthodontics…)，但关键词 R1 只命中
377/638，漏掉 261 道无牙科关键词的题。本脚本用 source∈{BoF,NBDE} 把书籍题全部纳入。

产出 data/en_dental_expanded/train.jsonl。
"""
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from dental_filter import is_dental_record_strict  # noqa: E402


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    gen = load(os.path.join(D, "en_general", "train.jsonl"))
    books = [r for r in gen if r.get("source") in ("BoF", "NBDE")]
    medqa_mmlu = [r for r in gen
                  if r.get("source") in ("medqa", "mmlu") and is_dental_record_strict(r)[0]]
    expanded = books + medqa_mmlu
    print(f"书籍题(source 全纳入): {len(books)}")
    print(f"MedQA/MMLU(严格过滤): {len(medqa_mmlu)}")
    print(f"扩张后牙科训练池: {len(expanded)}（原 train_v3 631）")

    outdir = os.path.join(D, "en_dental_expanded")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "train.jsonl"), "w", encoding="utf-8") as f:
        for r in expanded:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"已写入 {outdir}/train.jsonl")


if __name__ == "__main__":
    main()
