#!/usr/bin/env python3
"""牙科子集检查工具 —— 证明 train/val/test 子集里"不含非牙科数据"。

用途
----
对任意牙科子集 jsonl 逐题跑 `dental_filter.is_dental_record`，输出：
  1. 总题数 / 判为牙科 / 判为非牙科；
  2. 每题的命中明细（命中了 R1 哪个词 / R2 哪个 oral 语境）；
  3. 若存在非牙科题，显式列出并给出理由，让人工/AI 可复核。

判断依据
--------
见 `dental_filter.py` 顶部 docstring：R1 强关键词、R2 oral 语境、裸 oral 排除。

用法
----
    python3 data/check_dental_subset.py <子集.jsonl> [--detail report.txt]

输出
----
    - 控制台：汇总 + 非牙科题列表（若有）
    - --detail 指定文件：逐题命中明细（审计用）
退出码：0=全部牙科；1=存在非牙科题；2=参数错误。
"""
import json
import sys
from collections import Counter

from dental_filter import is_dental_record, question_text


def load_jsonl(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def main():
    if len(sys.argv) < 2:
        print("用法: python3 check_dental_subset.py <子集.jsonl> [--detail 报告.txt]")
        sys.exit(2)
    path = sys.argv[1]
    detail_path = None
    if "--detail" in sys.argv:
        detail_path = sys.argv[sys.argv.index("--detail") + 1]

    rows = load_jsonl(path)
    dental, nondental = [], []
    rule_counter = Counter()
    for r in rows:
        ok, hits = is_dental_record(r)
        if ok:
            dental.append((r, hits))
            for rule, kw in hits:
                rule_counter[f"{rule}:{kw}"] += 1
        else:
            nondental.append((r, hits))

    print("=" * 60)
    print(f"牙科子集检查：{path}")
    print(f"  总题数        : {len(rows)}")
    print(f"  判为牙科      : {len(dental)}")
    print(f"  判为非牙科    : {len(nondental)}")
    print("=" * 60)

    if nondental:
        print(f"\n[FAIL] 发现 {len(nondental)} 道非牙科题：")
        for r, _ in nondental[:20]:
            uid = r.get("uid") or r.get("id") or "?"
            src = r.get("source") or r.get("subject") or ""
            print(f"  - uid={uid}  source={src}")
            print(f"    {question_text(r)[:160]}...")
        if len(nondental) > 20:
            print(f"  ... 其余 {len(nondental) - 20} 道省略")
    else:
        print("\n[PASS] 该子集全部为牙科题，无污染。")

    print("\n命中规则分布（前 20）：")
    for k, v in rule_counter.most_common(20):
        print(f"  {k:40s} {v}")

    if detail_path:
        with open(detail_path, "w", encoding="utf-8") as f:
            for r, hits in dental + nondental:
                uid = r.get("uid") or r.get("id") or "?"
                tag = "DENTAL" if hits else "NON-DENTAL"
                f.write(f"[{tag}] {uid}  hits={hits}\n")
                f.write(f"    {question_text(r)[:200]}\n")
        print(f"\n逐题明细已写入: {detail_path}")

    sys.exit(1 if nondental else 0)


if __name__ == "__main__":
    main()
