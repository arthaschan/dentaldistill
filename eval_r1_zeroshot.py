#!/usr/bin/env python3
"""DeepSeek-R1-Distill-Qwen-32B 零样本 / LoRA 适配器评测（thinking 感知：max_new_tokens=2048, greedy）。
用法:
    python3 eval_r1_zeroshot.py                          # 零样本
    python3 eval_r1_zeroshot.py --adapter <adapter_dir>  # 蒸馏后
在 cn_dental_clean/test 与 en_dental/test 上评测。
答案提取：取输出末尾最后一个 A-E 字母（R1 最终答案在思考之后）。
prompt 用 Qwen 硬编码格式（chat_template=0），R1 对此格式响应正常。"""
import argparse
import json
import os
import sys

import torch
from peft import PeftModel
from transformers import AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared"))
from train_choice_head_distill import (  # noqa: E402
    apply_prompt_template, load_base_model,
)

MODEL = "/home/student/arthas/mentalDistill/models/DeepSeek-R1-Distill-Qwen-32B"
LETTERS = ["A", "B", "C", "D", "E"]


def last_letter(text):
    for ch in reversed(text.strip().upper()):
        if ch in LETTERS:
            return ch
    return ""


def eval_file(model, tok, path, lang, dev):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    correct = 0
    for i, r in enumerate(rows):
        if lang == "en":
            sys_line = ("You are a medical expert. Output exactly one letter "
                        "(A, B, C, D, or E) as the answer, with no explanation or spaces.\n")
            user_block = f"Question: {r['Question']}\nOptions:\n{r['Options']}\n"
        else:
            sys_line = "你是一名专业的牙科医生，只需输出一个字母（A、B、C、D、E）作为结果，不要附带任何解释或空格。\n"
            user_block = f"问题：{r['Question']}\n选项：\n{r['Options']}\n"
        prompt, _ = apply_prompt_template(tok, sys_line, user_block)
        inputs = tok(prompt, return_tensors="pt").to(dev)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=2048, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
        gen = tok.decode(out[0][inputs["input_ids"].size(1):], skip_special_tokens=True)
        if last_letter(gen) == str(r["Answer"]).strip().upper():
            correct += 1
        if (i + 1) % 20 == 0:
            print(f"  ... {i+1}/{len(rows)}  acc_sofar={100.0*correct/(i+1):.1f}%", flush=True)
    return 100.0 * correct / len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="")
    args = ap.parse_args()

    dev = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"[load] {MODEL}", flush=True)
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    base = load_base_model(MODEL, "none", dev).to(dev)
    model = PeftModel.from_pretrained(base, args.adapter) if args.adapter else base
    model.eval()

    print("=== R1 中文牙科 test 84 ===", flush=True)
    acc_cn = eval_file(model, tok, "data/cn_dental_clean/test.jsonl", "zh", dev)
    print(f"cn_dental test acc={acc_cn:.2f}% (n=84)", flush=True)
    print("=== R1 英文牙科 test 84 ===", flush=True)
    acc_en = eval_file(model, tok, "data/en_dental/test.jsonl", "en", dev)
    print(f"en_dental test acc={acc_en:.2f}% (n=84)", flush=True)


if __name__ == "__main__":
    main()
