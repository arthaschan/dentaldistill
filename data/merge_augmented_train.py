#!/usr/bin/env python3
"""合并扩充训练集：原文 + 反向译文，并校验与 val/test 零重叠。

- 中文牙科扩充：cn_dental_clean/train(381) + 英译中(549) -> train_aug
- 英文牙科扩充：en_dental/train(566) + 中译英(378) -> train_aug
输出：
  data/cn_dental_clean/train_aug.jsonl
  data/en_dental/train_aug.jsonl
"""
import json
import os


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


def merge(base_dir, base_train, translated, out_path, val_path, test_path):
    base = load(base_train)
    trans = load(translated)
    val_uids = {r.get("uid") for r in load(val_path)}
    test_uids = {r.get("uid") for r in load(test_path)}

    seen = {r.get("uid") for r in base}
    added = 0
    skipped_dup = 0
    skipped_test = 0
    for r in trans:
        uid = r.get("uid")
        if uid in seen:
            skipped_dup += 1
            continue
        if uid in val_uids or uid in test_uids:
            skipped_test += 1
            continue
        base.append(r)
        seen.add(uid)
        added += 1

    dump(base, out_path)
    print(f"{base_dir}: 原文 {len(load(base_train))} + 译文 {len(trans)} -> 合并 {len(base)}")
    print(f"  新增 {added}，重复跳过 {skipped_dup}，命中 val/test 跳过 {skipped_test}")
    return len(base)


if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    print("=== 中文牙科扩充 ===")
    merge("cn_dental",
          os.path.join(d, "cn_dental_clean", "train.jsonl"),
          os.path.join(d, "translate_en2zh_train.jsonl"),
          os.path.join(d, "cn_dental_clean", "train_aug.jsonl"),
          os.path.join(d, "cn_dental_clean", "val.jsonl"),
          os.path.join(d, "cn_dental_clean", "test.jsonl"))
    print()
    print("=== 英文牙科扩充 ===")
    merge("en_dental",
          os.path.join(d, "en_dental", "train.jsonl"),
          os.path.join(d, "translate_zh2en_train.jsonl"),
          os.path.join(d, "en_dental", "train_aug.jsonl"),
          os.path.join(d, "en_dental", "val.jsonl"),
          os.path.join(d, "en_dental", "test.jsonl"))
