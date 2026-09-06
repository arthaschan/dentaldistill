#!/usr/bin/env python3
"""英文 v3（干净重做，test 70）逐题预测 + McNemar（教师 Qwen3-32B vs 学生 Llama-70B 3-seed）。"""
import json
import os
import sys

os.environ["DISTILL_PROMPT_LANG"] = "en"
os.environ["DISTILL_USE_CHAT_TEMPLATE"] = "1"

import torch  # noqa: E402
from peft import PeftModel  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

ROOT = "/home/student/arthas/dentaldistill"
sys.path.insert(0, os.path.join(ROOT, "shared"))
from train_choice_head_distill import (  # noqa: E402
    apply_prompt_template, build_mcq_prompt, extract_answer_char, load_base_model,
)

TEACHER = "/home/student/arthas/mentalDistill/models/Qwen3-32B"
STUDENT = "/home/student/arthas/mentalDistill/models/Llama-3.3-70B-Instruct"
TEST = os.path.join(ROOT, "data/en_dental_v3/test.jsonl")

try:
    from scipy.stats import chi2 as chi2_dist
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


def predict(model, tok, rows, device):
    preds = []
    model.eval()
    with torch.no_grad():
        for r in rows:
            q, opts, ans = r["Question"], r["Options"], str(r["Answer"]).strip().upper()
            sys_line, user_block = build_mcq_prompt(q, opts)
            prompt, _ = apply_prompt_template(tok, sys_line, user_block)
            inputs = tok(prompt, return_tensors="pt", truncation=True).to(device)
            out = model.generate(**inputs, max_new_tokens=8, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
            gen = tok.decode(out[0][inputs["input_ids"].size(1):], skip_special_tokens=True)
            preds.append(extract_answer_char(gen) == ans)
    return preds


def main():
    rows = [json.loads(l) for l in open(TEST, encoding="utf-8") if l.strip()]
    n = len(rows)
    device = torch.device("cuda:0")

    tok = AutoTokenizer.from_pretrained(TEACHER, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base_t = load_base_model(TEACHER, "none", device).to(device)
    t_pred = predict(base_t, tok, rows, device)
    del base_t
    torch.cuda.empty_cache()
    print(f"教师 Qwen3-32B: {100*sum(t_pred)/n:.2f}% ({sum(t_pred)}/{n})")

    tok2 = AutoTokenizer.from_pretrained(STUDENT, trust_remote_code=True)
    if tok2.pad_token is None:
        tok2.pad_token = tok2.eos_token
    base_s = load_base_model(STUDENT, "4bit", device).to(device)
    for seed in ["11", "42", "8"]:
        adapter = os.path.join(ROOT, f"experiments/en_dental/runs/Llama70B_v3_r16_lr1e-4_s{seed}")
        model = PeftModel.from_pretrained(base_s, adapter)
        s_pred = predict(model, tok2, rows, device)
        s_acc = sum(s_pred)
        b = c = 0
        for t, s in zip(t_pred, s_pred):
            if s and not t:
                b += 1
            elif (not s) and t:
                c += 1
        chi2 = ((b - c) ** 2) / (b + c) if (b + c) > 0 else 0.0
        p = (1.0 - chi2_dist.cdf(chi2, 1)) if HAVE_SCIPY else None
        print(f"seed {seed}: 学生 {100*s_acc/n:.2f}% ({s_acc}/{n}) | McNemar b={b} c={c} 净胜{b-c} chi2={chi2:.3f} p={p if p is not None else 'n/a'}")


if __name__ == "__main__":
    main()
