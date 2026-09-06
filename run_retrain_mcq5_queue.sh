#!/usr/bin/env bash
# 英文牙科 MCQ「重组 5 选项」扩充重训（train_mcq5 914 = 566 原 + 348 重组五选项）。
# 与上一轮「判断题 2 选项」对比：这次格式与 5 选项任务一致，看是否不再掉点。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
M32="$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct"
M70="$HOME/arthas/mentalDistill/models/Llama-3.3-70B-Instruct"
LOG="retrain_mcq5_queue.log"
exec > >(tee -a "$LOG") 2>&1
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1

echo "[$(date '+%F %H:%M:%S')] retrain-mcq5 queue START"

echo "[$(date +%H:%M:%S)] TRAIN en_dental Qwen2.5-32B (train_mcq5 914)"
OUT="experiments/en_dental/runs/32B_mcq5_r8_lr3e4_s42"
mkdir -p "$OUT"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$M32" --data_path data/en_dental/train_mcq5.jsonl \
  --val_path data/en_dental/val.jsonl --output_dir "$OUT" \
  --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 3e-4 --rank 8 --lora_alpha 16 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic \
  > "$OUT/train.log" 2>&1 && touch "$OUT/DONE" || echo "[FAIL] qwen 见 $OUT/train.log"
"$PY" shared/eval_choice_head.py --model "$M32" --adapter "$OUT" --test data/en_dental/test.jsonl --lang en

echo "[$(date +%H:%M:%S)] TRAIN en_dental Llama-70B (train_mcq5 914, 4bit)"
OUT="experiments/en_dental/runs/Llama70B_mcq5_s42"
mkdir -p "$OUT"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$M70" --data_path data/en_dental/train_mcq5.jsonl \
  --val_path data/en_dental/val.jsonl --output_dir "$OUT" \
  --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic --quantize 4bit \
  > "$OUT/train.log" 2>&1 && touch "$OUT/DONE" || echo "[FAIL] llama 见 $OUT/train.log"
"$PY" shared/eval_choice_head.py --model "$M70" --adapter "$OUT" --test data/en_dental/test.jsonl --lang en --quantize 4bit

echo "[$(date '+%F %H:%M:%S')] retrain-mcq5 queue END"
