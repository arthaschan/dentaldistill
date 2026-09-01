#!/usr/bin/env python3
"""把 books_*.jsonl 规整成与英文数据一致的字段，并区分单选/多选。

- BoF / NBDE：single-best A–E 单选 -> books/books_singlebest.jsonl（并入牙科训练池）
- MCQ        ：true/false 多选（答案=TRUE 语句集合，如 "ADE"）-> books/books_tf.jsonl（辅助集，不并入单选）

输出字段统一为：uid, Question, Options("A ...\\nB ..."), Answer, n_options, source, subject。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(p):
    rows = []
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def opts_to_str(opts):
    return "\n".join(f"{k} {v}" for k, v in opts.items())


def normalize(records, source, single_best=True):
    out = []
    for r in records:
        opts = r.get("options", {})
        if not isinstance(opts, dict) or len(opts) < 4:
            continue
        ans = str(r.get("answer", "")).strip().upper()
        if single_best:
            if ans not in opts:  # 单字母 A-E
                continue
        else:
            if not ans or not all(c in opts for c in ans):  # 多字母组合
                continue
        out.append({
            "uid": r.get("id") or f"{source}-{len(out)}",
            "Question": (r.get("stem") or "").strip(),
            "Options": opts_to_str(opts),
            "Answer": ans,
            "n_options": len(opts),
            "source": source,
            "subject": r.get("subject", ""),
        })
    return out


def dump(rows, p):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    bof = normalize(load(os.path.join(HERE, "books_bof.jsonl")), "BoF", single_best=True)
    nbde = normalize(load(os.path.join(HERE, "books_nbde.jsonl")), "NBDE", single_best=True)
    mcq = normalize(load(os.path.join(HERE, "books_mcq.jsonl")), "MCQ", single_best=False)

    single = bof + nbde
    dump(single, os.path.join(HERE, "books_singlebest.jsonl"))
    dump(mcq, os.path.join(HERE, "books_tf.jsonl"))
    print(f"单选池(BoF+NBDE): {len(single)} 题 -> books_singlebest.jsonl")
    print(f"   BoF {len(bof)} / NBDE {len(nbde)}")
    print(f"多选辅助(MCQ):   {len(mcq)} 题 -> books_tf.jsonl（不并入单选）")
