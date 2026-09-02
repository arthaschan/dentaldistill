#!/usr/bin/env python3
"""英文牙科子集内容级审计 v2 —— 找出「只靠 oral 语境、无强牙科词」的边界题。

背景
----
dental_filter v2 的命中分两类：
  R1 强牙科信号（精确词/词干/限定短语）——tooth/teeth/dental/gingivitis/periodontal/pulpitis/
     alveolar bone/…，几乎必然牙科；
  R2 "oral" 口腔语境——oral ulcer/oral candidiasis/oral cavity/oral surgery/…，是口腔相关，
     但可能是「全身病的口腔表现」（如 Behçet 的口腔溃疡、SCID 的口腔念珠菌、多形红斑的口腔损害）。

本脚本对 en_dental 三集逐题判定：
  命中 R1 → 真牙科；
  只命中 R2（无 R1）→ 标记「边界题」，列出全文供人工复核（是否属牙科由审查者按定义判定）。

用法
----
    python3 data/audit_en_dental.py [data/en_dental] [--report reports/en_dental_audit.md]
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dental_filter import dental_match, question_text  # noqa: E402


def classify(record):
    hits = dental_match(question_text(record))
    r1 = [h[1] for h in hits if h[0] == "R1"]
    r2 = [h[1] for h in hits if h[0] == "R2"]
    return hits, bool(r1), bool(r2)


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


def main():
    indir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "en_dental")
    report_path = None
    if "--report" in sys.argv:
        report_path = sys.argv[sys.argv.index("--report") + 1]

    print("=" * 70)
    print("英文牙科子集内容级审计 v2（找「仅 oral 语境、无强牙科词」的边界题）")
    print("=" * 70)

    all_flagged = []
    for name in ["train", "val", "test"]:
        path = os.path.join(indir, f"{name}.jsonl")
        if not os.path.exists(path):
            continue
        rows = load(path)
        r1_hit, r2_only = [], []
        for r in rows:
            hits, has_r1, has_r2 = classify(r)
            if has_r1:
                r1_hit.append(r)
            elif has_r2:
                r2_only.append(r)
            else:
                # 理论上不该出现（en_dental 由 is_dental_record 过滤而来，必有 R1 或 R2）
                r2_only.append(r)
        print(f"\n[{name}] 共 {len(rows)}；命中 R1 强牙科词 {len(r1_hit)}；仅 R2 oral 语境 {len(r2_only)}")
        all_flagged.append((name, r2_only))

    print("\n" + "=" * 70)
    total = sum(len(x) for _, x in all_flagged)
    if total == 0:
        print("[PASS] 无仅 R2 的边界题。")
    else:
        print(f"[REVIEW] 共 {total} 题仅命中 oral 语境（无强牙科词），属边界题，列出供人工按定义判定：")
        for name, arr in all_flagged:
            for r in arr:
                hits = classify(r)[0]
                print(f"  [{name}] uid={r.get('uid')} source={r.get('source')} hits={[h[1] for h in hits]}")
                print(f"      {question_text(r)[:120]}")

    if report_path:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        L = ["# 英文牙科子集内容级审计报告（v2）\n\n",
             "## 检测方法\n\n",
             "- 对 `data/en_dental/{train,val,test}.jsonl` 逐题跑 `dental_filter.dental_match`（v2）。\n",
             "- R1 强牙科词（tooth/teeth/dental/gingivitis/periodontal/pulpitis/alveolar bone/…）→ 真牙科；\n",
             "- 仅命中 R2「oral 口腔语境」（oral ulcer/oral candidiasis/oral cavity/…）而无 R1 → 边界题。\n",
             "- 边界题是「全身病的口腔表现」（Behçet/SCID/多形红斑等），是否算牙科取决于对「牙科」的定义，\n",
             "  故显式列出供审计方按定义复核，而非静默判定。\n\n",
             "## 结果\n\n"]
        for name, arr in all_flagged:
            L.append(f"- `{name}`: 仅 R2 边界题 {len(arr)} 题\n")
        L.append("\n## 边界题清单\n\n")
        for name, arr in all_flagged:
            for r in arr:
                hits = classify(r)[0]
                L.append(f"- `{name}` uid={r.get('uid')} source={r.get('source')} hits={[h[1] for h in hits]}\n")
                L.append(f"  - {question_text(r)[:160]}\n")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("".join(L))
        print(f"\n报告已写入: {report_path}")


if __name__ == "__main__":
    main()
