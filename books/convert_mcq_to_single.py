#!/usr/bin/env python3
"""过滤拆分后的 MCQ 单选（R1 严格牙科），并入英文牙科 train，输出 train_mcq.jsonl。

同时生成 5 选项「which ONE is correct/incorrect」版本（|T|=1 保留、|T|=4 反转），
与 True/False 2 选项版本分开统计，方便对比哪种格式更有用。
"""
import json
import os
import re
import sys

D = os.path.dirname(os.path.abspath(__file__))  # books/
ROOT = os.path.dirname(D)                        # dentaldistill/
sys.path.insert(0, os.path.join(ROOT, "data"))
from dental_filter import is_dental_record_strict  # noqa: E402

BOOKS = D
DATA = os.path.join(ROOT, "data")


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def dump(rows, p):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    # 1) 过滤 True/False 2 选项拆分题
    split = load(os.path.join(BOOKS, "books_mcq_single.jsonl"))
    tf_dental = [r for r in split if is_dental_record_strict(r)[0]]
    dump(tf_dental, os.path.join(BOOKS, "books_mcq_single_dental.jsonl"))
    print(f"True/False 拆分题: {len(split)} -> 牙科(R1) {len(tf_dental)}")

    # 2) 从 books_tf.jsonl 生成 5 选项「which ONE」版本
    tf = load(os.path.join(BOOKS, "books_tf.jsonl"))
    fiveopt = []
    for r in tf:
        opts = []
        for part in str(r.get("Options", "")).split("\n"):
            part = part.strip()
            m = re.match(r"^([A-E])[.\s、:：]\s*(.*)$", part)
            if m:
                opts.append((m.group(1), m.group(2).strip()))
        ans = set(str(r.get("Answer", "")).strip().upper())
        true_letters = [l for l, _ in opts if l in ans]
        false_letters = [l for l, _ in opts if l not in ans]
        stem = str(r.get("Question", "")).strip()
        if len(true_letters) == 1:
            # 只有一条为真 -> "which is correct"，答案=该真陈述
            new = dict(r)
            new["Question"] = re.sub(r"(?i)are\s+correct", "is CORRECT", stem)
            new["Answer"] = true_letters[0]
            fiveopt.append(new)
        elif len(false_letters) == 1:
            # 只有一条为假 -> "which is incorrect"，答案=该假陈述
            new = dict(r)
            new["Question"] = re.sub(r"(?i)are\s+correct", "is INCORRECT", stem)
            new["Answer"] = false_letters[0]
            fiveopt.append(new)
    fiveopt_dental = [r for r in fiveopt if is_dental_record_strict(r)[0]]
    dump(fiveopt_dental, os.path.join(BOOKS, "books_mcq_5option_dental.jsonl"))
    print(f"5 选项「which ONE」: 生成 {len(fiveopt)} -> 牙科(R1) {len(fiveopt_dental)}")

    # 3) 并入 en_dental train
    base = load(os.path.join(DATA, "en_dental", "train.jsonl"))
    seen = {r.get("uid") for r in base}
    test_uids = {r.get("uid") for r in load(os.path.join(DATA, "en_dental", "test.jsonl"))}
    val_uids = {r.get("uid") for r in load(os.path.join(DATA, "en_dental", "val.jsonl"))}
    added_5 = added_tf = 0
    for r in fiveopt_dental + tf_dental:
        uid = r.get("uid")
        if uid in seen or uid in test_uids or uid in val_uids:
            continue
        base.append(r)
        seen.add(uid)
        if r.get("source") == "MCQ_tf":
            added_tf += 1
        else:
            added_5 += 1
    dump(base, os.path.join(DATA, "en_dental", "train_mcq.jsonl"))
    print(f"en_dental train: 原文 {len(load(os.path.join(DATA,'en_dental','train.jsonl')))} "
          f"+ 5选项 {added_5} + True/False {added_tf} = {len(base)}")


if __name__ == "__main__":
    main()
