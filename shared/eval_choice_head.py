#!/usr/bin/env python3
"""统一评估脚本：加载 base + LoRA adapter，在测试集上输出生成式准确率。

用法
----
    python3 shared/eval_choice_head.py \
        --model <base模型路径> --adapter <adapter路径> --test <测试jsonl> \
        [--lang zh|en] [--quantize 4bit]

复用 shared/train_choice_head_distill.py 的 prompt 构造与答案提取逻辑，
保证训练/评估口径一致。
"""
import argparse
import json
import os
import sys

import torch
from peft import PeftModel
from transformers import AutoTokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_choice_head_distill import (  # noqa: E402
    apply_prompt_template, build_mcq_prompt, extract_answer_char, load_base_model,
)


def eval_file(model, tok, path, device):
    samples = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("Question") and r.get("Options") and r.get("Answer"):
            samples.append((r["Question"], r["Options"], str(r["Answer"]).strip().upper()))
    correct = 0
    model.eval()
    with torch.no_grad():
        for q, opts, ans in samples:
            sys_line, user_block = build_mcq_prompt(q, opts)
            prompt, _ = apply_prompt_template(tok, sys_line, user_block)
            inputs = tok(prompt, return_tensors="pt", truncation=True).to(device)
            out = model.generate(**inputs, max_new_tokens=8, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
            gen = tok.decode(out[0][inputs["input_ids"].size(1):], skip_special_tokens=True)
            if extract_answer_char(gen) == ans:
                correct += 1
    return round(100.0 * correct / len(samples), 2) if samples else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", default="")
    ap.add_argument("--test", required=True)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--quantize", default="none")
    args = ap.parse_args()

    os.environ["DISTILL_PROMPT_LANG"] = args.lang
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = load_base_model(args.model, args.quantize, device).to(device)
    model = PeftModel.from_pretrained(base, args.adapter) if args.adapter else base
    model.eval()

    acc = eval_file(model, tok, args.test, device)
    print(f"test={os.path.basename(args.test)}  acc={acc}%  (n={sum(1 for _ in open(args.test))})")


if __name__ == "__main__":
    main()
