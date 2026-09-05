#!/usr/bin/env bash
# 扩充数据重训队列（打平的实验）：中文牙科 + 英文牙科两个学生，单 seed(42) 先快速验证。
# 数据用扩充后的 train_aug.jsonl（中文 930 / 英文 944）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
M32="$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct"
M70="$HOME/arthas/mentalDistill/models/Llama-3.3-70B-Instruct"
LOG="retrain_aug_queue.log"
exec > >(tee -a "$LOG") 2>&1

echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] retrain-aug queue START"
echo "=================================================================="

# ---------- 1. 中文牙科 Qwen2.5-32B（原 86.90% 打平，最优 rank16/lr2e-4）----------
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=0
OUT="experiments/cn_dental/runs/32B_aug_r16_lr2e4_s42"
mkdir -p "$OUT"
echo "[$(date +%H:%M:%S)] TRAIN cn_dental Qwen2.5-32B (train_aug 930)"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$M32" \
  --data_path data/cn_dental_clean/train_aug.jsonl \
  --val_path data/cn_dental_clean/val.jsonl \
  --output_dir "$OUT" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 2e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic \
  > "$OUT/train.log" 2>&1 && touch "$OUT/DONE" || echo "[FAIL] cn_dental 见 $OUT/train.log"
echo "  cn_dental 评测:"
"$PY" shared/eval_choice_head.py --model "$M32" --adapter "$OUT" --test data/cn_dental_clean/test.jsonl --lang zh

# ---------- 2. 英文牙科 Qwen2.5-32B（原 66.27%，最优 rank8/lr3e-4）----------
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1
OUT="experiments/en_dental/runs/32B_aug_r8_lr3e4_s42"
mkdir -p "$OUT"
echo "[$(date +%H:%M:%S)] TRAIN en_dental Qwen2.5-32B (train_aug 944)"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$M32" \
  --data_path data/en_dental/train_aug.jsonl \
  --val_path data/en_dental/val.jsonl \
  --output_dir "$OUT" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 3e-4 --rank 8 --lora_alpha 16 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic \
  > "$OUT/train.log" 2>&1 && touch "$OUT/DONE" || echo "[FAIL] en_dental_qwen 见 $OUT/train.log"
echo "  en_dental Qwen2.5 评测:"
"$PY" shared/eval_choice_head.py --model "$M32" --adapter "$OUT" --test data/en_dental/test.jsonl --lang en

# ---------- 3. 英文牙科 Llama-70B（原 67.06%，默认 rank16/lr1e-4）----------
OUT="experiments/en_dental/runs/Llama70B_aug_s42"
mkdir -p "$OUT"
echo "[$(date +%H:%M:%S)] TRAIN en_dental Llama-70B (train_aug 944, 4bit)"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$M70" \
  --data_path data/en_dental/train_aug.jsonl \
  --val_path data/en_dental/val.jsonl \
  --output_dir "$OUT" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic --quantize 4bit \
  > "$OUT/train.log" 2>&1 && touch "$OUT/DONE" || echo "[FAIL] en_dental_llama 见 $OUT/train.log"
echo "  en_dental Llama 评测:"
"$PY" shared/eval_choice_head.py --model "$M70" --adapter "$OUT" --test data/en_dental/test.jsonl --lang en --quantize 4bit

echo ""
echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] retrain-aug queue END"
echo "=================================================================="
