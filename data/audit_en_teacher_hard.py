#!/usr/bin/env python3
"""跑教师 Qwen3-32B 逐题，找出旧测试 84 题里答错的（难题），存 uid 列表。"""
import json
import os
import sys

os.environ["DISTILL_PROMPT_LANG"] = "en"
os.environ["DISTILL_USE_CHAT_TEMPLATE"] = "1"

import torch  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

ROOT = "/home/student/arthas/dentaldistill"
sys.path.insert(0, os.path.join(ROOT, "shared"))
from train_choice_head_distill import (  # noqa: E402
    apply_prompt_template, build_mcq_prompt, extract_answer_char, load_base_model,
)

TEACHER = "/home/student/arthas/mentalDistill/models/Qwen3-32B"
TEST = os.path.join(ROOT, "data/en_dental/test.jsonl")
OUT = os.path.join(ROOT, "data/en_dental_expanded/hard_uids.json")


def main():
    rows = [json.loads(l) for l in open(TEST, encoding="utf-8") if l.strip()]
    device = torch.device("cuda:0")
    tok = AutoTokenizer.from_pretrained(TEACHER, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = load_base_model(TEACHER, "none", device).to(device)
    base.eval()

    wrong_uids = []
    correct = 0
    with torch.no_grad():
        for r in rows:
            q, opts, ans = r["Question"], r["Options"], str(r["Answer"]).strip().upper()
            sys_line, user_block = build_mcq_prompt(q, opts)
            prompt, _ = apply_prompt_template(tok, sys_line, user_block)
            inputs = tok(prompt, return_tensors="pt", truncation=True).to(device)
            out = base.generate(**inputs, max_new_tokens=8, do_sample=False,
                                pad_token_id=tok.pad_token_id or tok.eos_token_id)
            gen = tok.decode(out[0][inputs["input_ids"].size(1):], skip_special_tokens=True)
            if extract_answer_char(gen) == ans:
                correct += 1
            else:
                wrong_uids.append(r["uid"])

    n = len(rows)
    print(f"教师 Qwen3-32B 旧测试: {correct}/{n} = {100*correct/n:.2f}%")
    print(f"答错(难题) {len(wrong_uids)} 题")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(wrong_uids, f, ensure_ascii=False)
    print(f"已写入 {OUT}")


if __name__ == "__main__":
    main()
