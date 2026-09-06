#!/usr/bin/env python3
"""计算「双方都错/学生独对/教师独对/双方都对」2x2，检验「难题稀释」假设。

对旧 84 题测试：用旧教师标签(deepseek_v4flash_cn_dental_clean_test.jsonl) + 重跑旧学生 adapter。
"""
import json
import os
import sys

os.environ["DISTILL_PROMPT_LANG"] = "zh"
os.environ["DISTILL_USE_CHAT_TEMPLATE"] = "0"

import torch  # noqa: E402
from peft import PeftModel  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

ROOT = "/home/student/arthas/dentaldistill"
sys.path.insert(0, os.path.join(ROOT, "shared"))
from train_choice_head_distill import (  # noqa: E402
    apply_prompt_template, build_mcq_prompt, extract_answer_char, load_base_model,
)

MODEL = "/home/student/arthas/mentalDistill/models/Qwen2.5-32B-Instruct"
ADAPTER = os.path.join(ROOT, "experiments/cn_dental/runs/Qwen25_cn_a00_clean2_r16_lr2e4_s42")
TEST = os.path.join(ROOT, "data/cn_dental_clean/test.jsonl")
TEACHER = os.path.join(ROOT, "teachers/deepseek_v4flash_cn_dental_clean_test.jsonl")


def main():
    # 教师逐题预测
    teacher_right = {}
    for line in open(TEACHER, encoding="utf-8"):
        r = json.loads(line)
        teacher_right[r["uid"]] = (r.get("TeacherAnswer") == r.get("OriginalAnswer"))

    rows = [json.loads(l) for l in open(TEST, encoding="utf-8") if l.strip()]

    device = torch.device("cuda:0")
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = load_base_model(MODEL, "none", device).to(device)
    model = PeftModel.from_pretrained(base, ADAPTER)
    model.eval()

    both_right = both_wrong = stu_only = tea_only = 0
    with torch.no_grad():
        for r in rows:
            q, opts, ans = r["Question"], r["Options"], str(r["Answer"]).strip().upper()
            sys_line, user_block = build_mcq_prompt(q, opts)
            prompt, _ = apply_prompt_template(tok, sys_line, user_block)
            inputs = tok(prompt, return_tensors="pt", truncation=True).to(device)
            out = model.generate(**inputs, max_new_tokens=8, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
            gen = tok.decode(out[0][inputs["input_ids"].size(1):], skip_special_tokens=True)
            s_right = (extract_answer_char(gen) == ans)
            t_right = teacher_right.get(r["uid"], False)
            if s_right and t_right:
                both_right += 1
            elif s_right and not t_right:
                stu_only += 1
            elif (not s_right) and t_right:
                tea_only += 1
            else:
                both_wrong += 1

    n = len(rows)
    print(f"旧 84 题（seed42 学生 88.10%）2x2 分解：")
    print(f"  双方都对   {both_right:3d}  ({100*both_right/n:.1f}%)")
    print(f"  学生独对   {stu_only:3d}  ({100*stu_only/n:.1f}%)  <- 学生优势")
    print(f"  教师独对   {tea_only:3d}  ({100*tea_only/n:.1f}%)  <- 教师优势")
    print(f"  双方都错   {both_wrong:3d}  ({100*both_wrong/n:.1f}%)  <- 谁都做不对")
    print(f"  学生净优势 = {stu_only - tea_only:+d} 题")


if __name__ == "__main__":
    main()
