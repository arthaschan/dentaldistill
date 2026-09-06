#!/usr/bin/env python3
"""把 MCQ 书的 true/false 陈述「重组」成 5 选项单选题（与任务格式一致，答案随机分布）。

只处理 true/false 多选题（答案集合 ≥2 条，保证每条选项是完整陈述而非单选题选项）。
去重 + 丢弃歧义陈述（同一文本在不同题里真值冲突），显式跟踪答案位置，避免 options.index 定位错误。
  - 真陈述 -> "Which of the following statements is CORRECT?"（答案=该真陈述）
  - 假陈述 -> "Which of the following statements is INCORRECT?"（答案=该假陈述）
输出 books/books_mcq_recombined_5option.jsonl。
"""
import json
import os
import random
import re
import sys
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))  # books/
ROOT = os.path.dirname(D)
sys.path.insert(0, os.path.join(ROOT, "data"))
from dental_filter import is_dental_record_strict  # noqa: E402

SRC = os.path.join(D, "books_tf.jsonl")
OUT = os.path.join(D, "books_mcq_recombined_5option.jsonl")
LETTERS = "ABCDE"


def parse_options(opts_text):
    items = []
    for part in str(opts_text).split("\n"):
        part = part.strip()
        m = re.match(r"^([A-E])[.\s、:：]\s*(.*)$", part)
        if m:
            items.append((m.group(1), m.group(2).strip()))
    return items


def main():
    random.seed(42)
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8") if l.strip()]
    by_chapter = defaultdict(lambda: {"true": [], "false": []})
    n_skipped = 0
    for r in rows:
        ans = set(str(r.get("Answer", "")).strip().upper())
        if len(ans) < 2:  # 只取真假多选题（≥2 真），跳过单选题（题干嵌入选项的脏数据）
            n_skipped += 1
            continue
        chapter = r.get("subject", "?")
        for letter, text in parse_options(r.get("Options", "")):
            probe = {"Question": text, "Options": ""}
            if not is_dental_record_strict(probe)[0]:
                continue
            (by_chapter[chapter]["true"] if letter in ans else by_chapter[chapter]["false"]).append(text)

    n_correct = n_incorrect = n_dropped = 0
    with open(OUT, "w", encoding="utf-8") as wf:
        for chapter, pool in by_chapter.items():
            trues = list(dict.fromkeys(pool["true"]))
            falses = list(dict.fromkeys(pool["false"]))
            cross = set(trues) & set(falses)
            trues = [t for t in trues if t not in cross]
            falses = [f for f in falses if f not in cross]
            n_dropped += len(cross)
            # which is CORRECT：每条真陈述 + 4 条假陈述
            for i, t in enumerate(trues):
                if len(falses) < 4:
                    break
                dist = [falses[(i*4 + k) % len(falses)] for k in range(4)]
                options = [t] + dist
                idxs = list(range(5))
                random.shuffle(idxs)
                shuffled = [options[j] for j in idxs]
                ans_idx = next(k for k, x in enumerate(shuffled) if x is t or x == t)
                new = {
                    "uid": f"mcq5_{chapter}_{i}_corr",
                    "Question": "Which of the following statements is CORRECT?",
                    "Options": "\n".join(f"{L}. {txt}" for L, txt in zip(LETTERS, shuffled)),
                    "Answer": LETTERS[ans_idx],
                    "n_options": 5,
                    "source": "MCQ_recomb",
                    "subject": chapter,
                }
                wf.write(json.dumps(new, ensure_ascii=False) + "\n")
                n_correct += 1
            # which is INCORRECT：每条假陈述 + 4 条真陈述
            for i, f in enumerate(falses):
                if len(trues) < 4:
                    break
                dist = [trues[(i*4 + k) % len(trues)] for k in range(4)]
                options = [f] + dist
                idxs = list(range(5))
                random.shuffle(idxs)
                shuffled = [options[j] for j in idxs]
                ans_idx = next(k for k, x in enumerate(shuffled) if x == f)
                new = {
                    "uid": f"mcq5_{chapter}_{i}_incorr",
                    "Question": "Which of the following statements is INCORRECT?",
                    "Options": "\n".join(f"{L}. {txt}" for L, txt in zip(LETTERS, shuffled)),
                    "Answer": LETTERS[ans_idx],
                    "n_options": 5,
                    "source": "MCQ_recomb",
                    "subject": chapter,
                }
                wf.write(json.dumps(new, ensure_ascii=False) + "\n")
                n_incorrect += 1

    print(f"跳过单选题(答案<2) {n_skipped}；丢弃歧义陈述 {n_dropped}")
    print(f"重组 5 选项题：which-correct {n_correct} + which-incorrect {n_incorrect} = {n_correct+n_incorrect}")
    print(f"输出 {OUT}")


if __name__ == "__main__":
    main()
