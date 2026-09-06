#!/usr/bin/env python3
"""从 CMExam train.csv + val.csv 用「严格牙科过滤」挖中文牙科题，扩展现有训练集。

产出 data/cn_dental_clean/train_v2.jsonl = 原 train(381) + 新挖矿牙科题。
val(80) / test(84) 保持不变，保证与历史结果可比。

判定：`content_signal_strict`（严格中文词 + 英文 R1 不含 R2），
      在 test_with_annotations.csv 地面真值上 precision ≈ 87.3%。

只挖 train.csv / val.csv（真正的 train/val 切分）；不碰 test_with_annotations.csv（测试切分，
避免训练-测试分布泄漏）。只保留 5 选项(A-E) + 单字母答案的有效题。

用法：
    python3 data/prepare_cn_dental_v2.py
"""
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from check_cn_dental_content import content_signal_strict  # noqa: E402

OPT_LETTERS = {"A", "B", "C", "D", "E"}
# 选项行形如 "A ...\nB ...\n..."；从行首字母识别选项数
_OPT_LINE_RE = re.compile(r"(?m)^([A-E])\s")


def uid_of(q, o):
    return "cmexam-" + hashlib.md5((str(q) + "||" + str(o)).encode()).hexdigest()[:12]


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def option_letters(opts):
    return sorted(set(_OPT_LINE_RE.findall(opts or "")))


def load_csv(path):
    """读取 CSV，返回 [record]，其中 record 含 Question/Options/Answer/Explanation。"""
    rows = []
    for row in csv.DictReader(open(path, encoding="utf-8")):
        rows.append({
            "Question": (row.get("Question") or "").strip(),
            "Options": (row.get("Options") or "").strip(),
            "Answer": (row.get("Answer") or "").strip().upper(),
            "Explanation": (row.get("Explanation") or "").strip(),
        })
    return rows


def dump(rows, p):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    clean_dir = os.path.join(D, "cn_dental_clean")
    old_train = load_jsonl(os.path.join(clean_dir, "train.jsonl"))
    val = load_jsonl(os.path.join(clean_dir, "val.jsonl"))
    test = load_jsonl(os.path.join(clean_dir, "test.jsonl"))
    test_uids = {r.get("uid") for r in test}
    val_uids = {r.get("uid") for r in val}
    existing_uids = {r.get("uid") for r in old_train}

    cm = os.path.join(D, "cmexam")
    valid_opt = Counter()
    mined = []
    for fn in ["train.csv", "val.csv"]:
        rows = load_csv(os.path.join(cm, fn))
        n_valid = 0
        keep = []
        for r in rows:
            letters = option_letters(r["Options"])
            # 只保留标准 5 选项 + 单字母答案
            if letters != ["A", "B", "C", "D", "E"] or r["Answer"] not in OPT_LETTERS:
                valid_opt[len(letters)] += 1
                continue
            n_valid += 1
            if content_signal_strict(r):
                r["uid"] = uid_of(r["Question"], r["Options"])
                keep.append(r)
        mined.extend(keep)
        print(f"[{fn}] 总 {len(rows)} -> 5选项单答案 {n_valid} -> 严格牙科 {len(keep)}")
    print(f"非标准题分布(按选项数): {dict(valid_opt)}")

    # 去重 + 避开 test/val/已用
    seen = set()
    new_records = []
    for r in mined:
        uid = r["uid"]
        if uid in seen or uid in test_uids or uid in val_uids or uid in existing_uids:
            continue
        seen.add(uid)
        new_records.append(r)
    print(f"\n挖矿去重后新增: {len(new_records)}（剔除与 test/val/原train 重叠）")

    merged = old_train + new_records
    dump(merged, os.path.join(clean_dir, "train_v2.jsonl"))
    print(f"train_v2 = 原 {len(old_train)} + 新增 {len(new_records)} = {len(merged)}")

    m_uids = {r.get("uid") for r in merged}
    print(f"与 test 重叠: {len(m_uids & test_uids)}（应 0）")
    print(f"与 val  重叠: {len(m_uids & val_uids)}（应 0）")
    print(f"train_v2 内唯一 uid: {len(m_uids)}")

    # 答案分布 sanity
    ans = Counter(r.get("Answer") for r in merged)
    print(f"答案分布: {dict(sorted(ans.items()))}")


if __name__ == "__main__":
    main()
