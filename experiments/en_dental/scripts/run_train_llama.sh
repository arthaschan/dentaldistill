#!/usr/bin/env bash
# 英文牙科：Llama-3.3-70B 学生（牙科专属数据，QLoRA 4bit），α=0 纯 GT，1 epoch，seed 42。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_LLAMA70B:-$HOME/arthas/mentalDistill/models/Llama-3.3-70B-Instruct}"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1

out="experiments/en_dental/runs/Llama70B_a00_s42"
mkdir -p "$out"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$STUDENT" \
  --data_path data/en_dental/train.jsonl \
  --val_path data/en_dental/val.jsonl \
  --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic --quantize 4bit \
  > "$out/train.log" 2>&1
touch "$out/DONE"

echo "评估:"
"$PY" shared/eval_choice_head.py --model "$STUDENT" --adapter "$out" \
  --test data/en_dental/test.jsonl --lang en --quantize 4bit
