#!/usr/bin/env python3
"""逐题生成 3-seed 学生预测 + 与教师做 McNemar 配对检验（显著性）。"""
import json
import os
import sys
import math

import torch
from peft import PeftModel
from transformers import AutoTokenizer

ROOT = "/home/student/arthas/dentaldistill"
sys.path.insert(0, os.path.join(ROOT, "shared"))
from train_choice_head_distill import (  # noqa: E402
    apply_prompt_template, build_mcq_prompt, extract_answer_char, load_base_model,
)

MODEL = "/home/student/arthas/mentalDistill/models/Qwen2.5-32B-Instruct"
TEST = os.path.join(ROOT, "data/cn_dental_v3/test.jsonl")
TEACHER = os.path.join(ROOT, "teachers/deepseek_v4flash_cn_dental_v3_test.jsonl")

os.environ["DISTILL_PROMPT_LANG"] = "zh"

# 教师预测（按 uid）：是否答对
teacher_right = {}
for line in open(TEACHER, encoding="utf-8"):
    r = json.loads(line)
    teacher_right[r["uid"]] = (r.get("TeacherAnswer") == r.get("OriginalAnswer"))

test_rows = [json.loads(l) for l in open(TEST, encoding="utf-8") if l.strip()]

device = torch.device("cuda:0")
tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
base = load_base_model(MODEL, "none", device).to(device)

try:
    from scipy.stats import chi2 as chi2_dist
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


def mcnemar_p(chi2):
    if HAVE_SCIPY:
        return 1.0 - chi2_dist.cdf(chi2, 1)
    return None


for seed in ["11", "42", "8"]:
    adapter = os.path.join(ROOT, f"experiments/cn_dental/runs/Qwen25_cn_v3_r16_lr2e4_s{seed}")
    model = PeftModel.from_pretrained(base, adapter)
    model.eval()
    stu_right_total = 0
    b = c = 0  # b: 学生对教师错；c: 学生对错
    with torch.no_grad():
        for r in test_rows:
            q, opts, ans = r["Question"], r["Options"], str(r["Answer"]).strip().upper()
            sys_line, user_block = build_mcq_prompt(q, opts)
            prompt, _ = apply_prompt_template(tok, sys_line, user_block)
            inputs = tok(prompt, return_tensors="pt", truncation=True).to(device)
            out = model.generate(**inputs, max_new_tokens=8, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
            gen = tok.decode(out[0][inputs["input_ids"].size(1):], skip_special_tokens=True)
            pred = extract_answer_char(gen)
            stu_right = (pred == ans)
            if stu_right:
                stu_right_total += 1
            t_right = teacher_right[r["uid"]]
            if stu_right and not t_right:
                b += 1
            elif (not stu_right) and t_right:
                c += 1
    n = len(test_rows)
    chi2 = ((b - c) ** 2) / (b + c) if (b + c) > 0 else 0.0
    p = mcnemar_p(chi2)
    print(f"seed {seed}: 学生 acc={100*stu_right_total/n:.2f}% ({stu_right_total}/{n})")
    print(f"  McNemar: 学生对教师错 b={b}, 教师对学生错 c={c}, 净胜 {b-c}, chi2={chi2:.3f}, p={p if p is not None else 'n/a (无scipy)'}")
