#!/usr/bin/env python3
"""牙科选择题翻译：英->中 或 中->英，用于扩充训练集。

用法:
    python3 data/translate_mcq.py --src data/en_dental/train.jsonl \
        --out data/translate_en2zh_train.jsonl --direction en2zh [--limit N]

只翻译 Question + Options（训练只用这三字段 + Answer 字母不变）。
保留 uid/source 并加 translated_from 标记，供合并去重。
断点续跑：按 uid 跳过已翻译的题。
"""
import argparse
import json
import os
import re
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL = "/home/student/arthas/mentalDistill/models/Qwen2.5-32B-Instruct"

SYSTEM = {
    "en2zh": "你是一名专业的医学翻译，精通中英文医学术语。请把英文医学选择题精确、准确地翻译成简体中文。",
    "zh2en": "You are a professional medical translator fluent in Chinese and English medical terminology. Translate Chinese medical multiple-choice questions into accurate, natural English.",
}

def build_user(direction, q, opts):
    if direction == "en2zh":
        return (
            "请把下面的医学选择题翻译成简体中文。选项标签 A/B/C/D/E 保持大写字母不变。"
            "只输出一个 JSON 对象，格式：\n"
            '{"Question": "题干译文", "Options": "A 选项1译文\\nB 选项2译文\\n..."}\n\n'
            f"题干：{q}\n选项：\n{opts}"
        )
    else:
        return (
            "Translate the following medical multiple-choice question into English. "
            "Keep option labels A/B/C/D/E as uppercase letters. Output ONLY one JSON object:\n"
            '{"Question": "translated stem", "Options": "A opt1\\nB opt2\\n..."}\n\n'
            f"Question: {q}\nOptions:\n{opts}"
        )


def extract_json(text):
    if not text:
        return None
    # 去掉可能的代码块围栏
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(t[start:end + 1])
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--direction", required=True, choices=["en2zh", "zh2en"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--quantize", default="none", choices=["none", "4bit"])
    ap.add_argument("--max_new_tokens", type=int, default=800)
    args = ap.parse_args()

    dev = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if args.quantize == "4bit":
        from transformers import BitsAndBytesConfig
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                 bnb_4bit_compute_dtype=torch.bfloat16,
                                 bnb_4bit_use_double_quant=True)
        model = AutoModelForCausalLM.from_pretrained(args.model, quantization_config=bnb,
                                                     device_map={"": dev}, trust_remote_code=True)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16,
                                                     trust_remote_code=True).to(dev)
    model.eval()

    rows = [json.loads(l) for l in open(args.src, encoding="utf-8") if l.strip()]
    if args.limit:
        rows = rows[:args.limit]

    done_uids = set()
    if os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    done_uids.add(json.loads(line)["uid"])
                except Exception:
                    pass

    out_mode = "a" if done_uids else "w"
    ok = fail = 0
    with open(args.out, out_mode, encoding="utf-8") as wf:
        for i, r in enumerate(rows):
            uid = r.get("uid", f"row{i}")
            if uid in done_uids:
                continue
            q = str(r.get("Question", "")).strip()
            opts = str(r.get("Options", "")).strip()
            ans = str(r.get("Answer", "")).strip().upper()
            msgs = [
                {"role": "system", "content": SYSTEM[args.direction]},
                {"role": "user", "content": build_user(args.direction, q, opts)},
            ]
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inputs = tok(prompt, return_tensors="pt").to(dev)
            with torch.no_grad():
                out_ids = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False,
                                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
            gen = tok.decode(out_ids[0][inputs["input_ids"].size(1):], skip_special_tokens=True)
            parsed = extract_json(gen)
            if parsed and parsed.get("Question") and parsed.get("Options"):
                new = dict(r)
                new["Question"] = str(parsed["Question"]).strip()
                new["Options"] = str(parsed["Options"]).strip()
                new["Answer"] = ans
                new["translated_from"] = args.src
                new["translation_direction"] = args.direction
                wf.write(json.dumps(new, ensure_ascii=False) + "\n")
                wf.flush()
                done_uids.add(uid)
                ok += 1
            else:
                fail += 1
                print(f"[FAIL] {uid}: {gen[:120]!r}", flush=True)
            if (i + 1) % 20 == 0:
                print(f"[PROGRESS] {i+1}/{len(rows)} ok={ok} fail={fail}", flush=True)

    print(f"[DONE] ok={ok} fail={fail} output={args.out}", flush=True)


if __name__ == "__main__":
    main()
