#!/usr/bin/env python3
"""多选题（MCQ true/false 多选）对单候选训练/评估影响的演示 + 判定。

背景
----
books/MCQs for Dentistry 是 true/false 多选：每题 A-E 五个陈述，答案是「全部为真的陈述集合」
（如 "ADE" = A、D、E 三条陈述为真）。这与本仓库「单候选 A-E」任务（模型只输出一个字母）
格式不兼容。本脚本用训练/评估代码的真实路径，演示把多选答案塞进单候选流水线会发生什么。

结论预览
--------
1) 训练（shared/train_choice_head_distill.py 的 DentalChoiceHeadDataset.__getitem__）：
   ans="ADE" 不在 OPTION_LETTERS=["A".."E"] 中 -> 被强制置为 "A"，gt_option=0。
   => 会用「标准答案 A」去监督一道真答案是「A、D、E 三条都真」的题，主动教错。
2) 评估（shared/train_choice_head_distill.py 的 extract_answer_char）：
   只看生成文本里出现的第一个 A-E 字母。模型正确输出 "ADE" 时只取到 "A"，
   与存储答案 "ADE" 永远对不上，多选无法被单候选指标评分。
=> 结论：多选（MCQ true/false）不应并入单候选英文训练/测试，会拉低正确率且不可评分。
"""
import re
import sys

OPTION_LETTERS = ["A", "B", "C", "D", "E"]


def dataset_coerce_answer(ans: str) -> str:
    """复刻 DentalChoiceHeadDataset.__getitem__ 对 Answer 的强制逻辑。"""
    ans = str(ans).strip().upper()
    if ans not in OPTION_LETTERS:
        ans = "A"
    return ans


def extract_answer_char(text: str) -> str:
    """复刻训练脚本的答案提取逻辑。"""
    for ch in text.strip().upper():
        if ch in OPTION_LETTERS:
            return ch
    return ""


def main():
    # 取一条真实的 MCQ 多选记录
    import json
    rows = [json.loads(l) for l in open("books/books_mcq.jsonl", encoding="utf-8") if l.strip()]
    multi = [r for r in rows if r["answer"] and len(r["answer"]) > 1]
    print(f"MCQ 多选记录数: {len(multi)} / {len(rows)}")
    if not multi:
        print("（无多选记录）")
        return
    ex = multi[0]
    print("\n示例题（真实）:")
    print("  stem   :", ex["stem"][:70])
    print("  answer :", ex["answer"], "（多选：多条陈述为真）")
    print("  format :", ex.get("format"))

    # 1) 训练路径
    coerced = dataset_coerce_answer(ex["answer"])
    print("\n[训练路径] DentalChoiceHeadDataset.__getitem__:")
    print(f"  输入 Answer = {ex['answer']!r}")
    print(f"  -> 强制后 ans = {coerced!r}  (gt_option 索引 = {OPTION_LETTERS.index(coerced)})")
    print("  -> 结论：用单字母监督一道多选真值题，模型被教成只输出一个字母，与真值不符。")

    # 2) 评估路径
    print("\n[评估路径] extract_answer_char:")
    for gen in ["ADE", "A,D,E", "A、D、E", "The correct statements are A, D and E"]:
        print(f"  模型生成 {gen!r} -> 提取 {extract_answer_char(gen)!r}；存储答案 {ex['answer']!r} "
              f"-> 判对? {extract_answer_char(gen) == ex['answer']}")

    # 3) 统计：单候选流水线对多选答案的处理
    print("\n[统计] books_mcq.jsonl 的答案形态分布:")
    from collections import Counter
    c = Counter(len(r["answer"]) for r in rows if r["answer"])
    for k, v in sorted(c.items()):
        tag = "多选（不可用于单候选）" if k > 1 else "单选（可用）"
        print(f"  答案长度 {k}: {v} 题  {tag}")


if __name__ == "__main__":
    main()
