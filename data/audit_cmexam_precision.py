#!/usr/bin/env python3
"""校准内容级牙科关键词在无标签 CSV 上的精度。

用 test_with_annotations.csv（有 ground-truth 学科标签）做混淆矩阵：
  内容级关键词命中 vs Medical Discipline==口腔医学。
据此估计 train.csv / val.csv 上内容命中里「真牙科」的占比（precision），
以及漏掉的牙科题比例（recall / false negative）。

同时统计 train.csv 与 val.csv 的内容命中是否互相重叠（uid）。
"""
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cn_dental_content import content_signal, dept_signal


def uid_of(q, o):
    import hashlib
    return "cmexam-" + hashlib.md5((str(q) + "||" + str(o)).encode()).hexdigest()[:12]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    cm = os.path.join(here, "cmexam")

    # ---- 混淆矩阵（用 test_with_annotations.csv 的地面真值）----
    print("=" * 72)
    print("混淆矩阵：内容级关键词命中 vs 学科标签==口腔医学 (test_with_annotations.csv)")
    print("=" * 72)
    tp = fp = fn = tn = 0
    for row in csv.DictReader(open(os.path.join(cm, "test_with_annotations.csv"), encoding="utf-8")):
        q = row.get("Question", ""); o = row.get("Options", "")
        hit = bool(content_signal({"Question": q, "Options": o}))
        dental = (row.get("Medical Discipline") or "").strip() == "口腔医学"
        if dental and hit:
            tp += 1
        elif dental and not hit:
            fn += 1
        elif (not dental) and hit:
            fp += 1
        else:
            tn += 1
    total = tp + fp + fn + tn
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    print(f"  TP(牙科且命中)={tp}  FP(非牙科但命中)={fp}")
    print(f"  FN(牙科但漏掉)={fn}  TN={tn}")
    print(f"  Precision(命中里真牙科) = {precision:.1%}")
    print(f"  Recall(牙科里被命中)   = {recall:.1%}")
    print(f"  口腔医学总题数 = {tp+fn}，内容命中总题数 = {tp+fp}")

    # ---- 内容命中里 FP 的高频词（看哪些词造成假阳性）----
    print("\n  FP(非牙科但被内容命中)样本 & 命中词:")
    fp_hits = Counter()
    fp_samples = []
    for row in csv.DictReader(open(os.path.join(cm, "test_with_annotations.csv"), encoding="utf-8")):
        q = row.get("Question", ""); o = row.get("Options", "")
        hits = content_signal({"Question": q, "Options": o})
        dental = (row.get("Medical Discipline") or "").strip() == "口腔医学"
        if hits and not dental:
            for _, w in hits:
                fp_hits[w] += 1
            if len(fp_samples) < 15:
                fp_samples.append((q[:50], [w for _, w in hits]))
    print("  造成FP的高频词:", dict(fp_hits.most_common(20)))
    for q, ws in fp_samples:
        print(f"    [FP] {ws}  Q: {q}")

    # ---- train.csv vs val.csv 内容命中重叠 ----
    print("\n" + "=" * 72)
    print("train.csv / val.csv 内容命中 uid 重叠检查")
    print("=" * 72)
    def content_uids(path):
        uids = set()
        for row in csv.DictReader(open(path, encoding="utf-8")):
            q = row.get("Question", ""); o = row.get("Options", "")
            if content_signal({"Question": q, "Options": o}):
                uids.add(uid_of(q, o))
        return uids
    val_uids = content_uids(os.path.join(cm, "val.csv"))
    train_uids = content_uids(os.path.join(cm, "train.csv"))
    inter = val_uids & train_uids
    print(f"  val.csv   内容命中: {len(val_uids)}")
    print(f"  train.csv 内容命中: {len(train_uids)}")
    print(f"  两文件重叠        : {len(inter)}  <-- 若 >0 则 val 是 train 的子集/重复")


if __name__ == "__main__":
    main()
