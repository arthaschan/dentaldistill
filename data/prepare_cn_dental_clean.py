#!/usr/bin/env python3
"""中文牙科「干净」子集重筛 —— 按内容级牙科关键词过滤，产出纯牙科数据。

背景
----
`data/prepare_cn_dental.py` 按学科字段 `Medical Discipline == "口腔医学"` 拆出的子集，
经 `check_cn_dental_content.py` 检测发现约 35%–42% 是通科医学题（药理/儿科/妇产/统计/伦理…）。
本脚本用「内容级强牙科关键词」重筛，只保留题干+选项里确有牙科信号的题，产出
`data/cn_dental_clean/{train,val,test}.jsonl`，并打印新旧条数对比。

判定：复用 `check_cn_dental_content.content_signal`（C1 中文强关键词 + C3 英文 R1/R2）。
高精度、偏保守（会剔除个别无关键词但确属牙科的题），取舍可接受且逐题可复核。

用法
----
    python3 data/prepare_cn_dental_clean.py [in=data/cn_dental] [out=data/cn_dental_clean]

退出码：0 正常。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cn_dental_content import dental_signal  # noqa: E402


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


def main():
    indir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "cn_dental")
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "cn_dental_clean")
    os.makedirs(outdir, exist_ok=True)

    print(f"in={indir}  out={outdir}")
    total_old = total_new = 0
    for name in ["train", "val", "test"]:
        rows = load(os.path.join(indir, f"{name}.jsonl"))
        keep = [r for r in rows if dental_signal(r)]
        drop = len(rows) - len(keep)
        dump(keep, os.path.join(outdir, f"{name}.jsonl"))
        total_old += len(rows)
        total_new += len(keep)
        print(f"  {name}: {len(rows)} -> 保留牙科 {len(keep)}（剔除 {drop}）")

    print(f"\n合计: {total_old} -> {total_new}（剔除 {total_old - total_new}，"
          f"{(total_old - total_new) * 100 / max(total_old, 1):.1f}%）")
    print("\n审计（应 [PASS]，且内容级应全命中）:")
    print(f"  python3 data/check_dental_subset.py {outdir}/test.jsonl")
    print(f"  python3 data/check_cn_dental_content.py {outdir} --report reports/cn_dental_clean_report.md")


if __name__ == "__main__":
    main()
