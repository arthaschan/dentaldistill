#!/usr/bin/env bash
# 英文牙科 Llama-70B 3-seed 坐实：α=0 纯 GT，1 epoch，seed(11/42/8)，QLoRA 4bit。
# 数据 data/en_dental/（train 566 / val 26 / test 84，R1 严格口径零非牙科）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_LLAMA70B:-$HOME/arthas/mentalDistill/models/Llama-3.3-70B-Instruct}"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/en_dental/runs/Llama70B_a00_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN Llama70B_a00_s${seed}"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/en_dental/train.jsonl \
    --val_path data/en_dental/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic --quantize 4bit \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done

echo "评估（3 seed，en_dental test 84 题）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/en_dental/runs/Llama70B_a00_s${seed}" \
    --test data/en_dental/test.jsonl --lang en --quantize 4bit
done
