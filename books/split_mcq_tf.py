#!/usr/bin/env python3
"""把 MCQs for Dentistry 的 true/false 多选题拆成单选（每陈述一道 True/False）。

books_tf.jsonl 每题：Question=题干, Options="A xx\\nB xx\\n...", Answer=真陈述集合(如"ADE")。
拆分：对每条陈述生成一道单选题：
  Question = "Is the following statement true or false? <陈述>"
  Options  = "A. True\\nB. False"
  Answer   = A(真) / B(假)
输出 books/books_mcq_single.jsonl。
"""
import json
import os
import re

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, "books_tf.jsonl")
OUT = os.path.join(D, "books_mcq_single.jsonl")


def parse_options(opts_text):
    """把 "A xx\\nB yy\\n..." 解析成 [(letter, text), ...]"""
    items = []
    for part in opts_text.split("\n"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([A-E])[.\s、:：]\s*(.*)$", part)
        if m:
            items.append((m.group(1), m.group(2).strip()))
    return items


def main():
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8") if l.strip()]
    total_statements = 0
    total_true = 0
    total_false = 0
    skipped = 0
    with open(OUT, "w", encoding="utf-8") as wf:
        for r in rows:
            uid = r.get("uid", "")
            opts = parse_options(r.get("Options", ""))
            ans = set(str(r.get("Answer", "")).strip().upper())
            if not opts or not ans:
                skipped += 1
                continue
            for letter, text in opts:
                is_true = letter in ans
                total_statements += 1
                if is_true:
                    total_true += 1
                else:
                    total_false += 1
                new = {
                    "uid": f"{uid}__{letter}",
                    "Question": f"Is the following statement true or false? {text}",
                    "Options": "A. True\nB. False",
                    "Answer": "A" if is_true else "B",
                    "n_options": 2,
                    "source": "MCQ_tf",
                    "subject": r.get("subject", ""),
                    "orig_uid": uid,
                }
                wf.write(json.dumps(new, ensure_ascii=False) + "\n")

    print(f"源题 {len(rows)}，跳过 {skipped}（无选项/无答案）")
    print(f"拆出单选 {total_statements} 道：True {total_true} / False {total_false}")
    print(f"输出 {OUT}")


if __name__ == "__main__":
    main()
