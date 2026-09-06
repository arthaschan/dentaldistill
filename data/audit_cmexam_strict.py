#!/usr/bin/env python3
"""严格中文牙科过滤在 test_with_annotations.csv 上的精度/召回（复用 content_signal_strict）。"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cn_dental_content import content_signal_strict


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    cm = os.path.join(here, "cmexam")
    tp = fp = fn = tn = 0
    fp_samples = []
    for row in csv.DictReader(open(os.path.join(cm, "test_with_annotations.csv"), encoding="utf-8")):
        q = row.get("Question", ""); o = row.get("Options", "")
        hits = content_signal_strict({"Question": q, "Options": o})
        dental = (row.get("Medical Discipline") or "").strip() == "口腔医学"
        if dental and hits:
            tp += 1
        elif dental and not hits:
            fn += 1
        elif (not dental) and hits:
            fp += 1
            if len(fp_samples) < 25:
                fp_samples.append((q[:45], [w for _, w in hits]))
        else:
            tn += 1
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    print(f"TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"Precision = {prec:.1%}  (全量版 76.6%)")
    print(f"Recall    = {rec:.1%}  (全量版 64.8%)")
    print(f"口腔医学总 {tp+fn}，严格命中总 {tp+fp}")
    print("\n剩余 FP 样本（多为跨学科但牙科相关，或少数真噪声）:")
    for q, ws in fp_samples:
        print(f"  {ws}  Q: {q}")


if __name__ == "__main__":
    main()
