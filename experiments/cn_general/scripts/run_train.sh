#!/usr/bin/env bash
# 中文全科：Qwen2.5-14B 学生，α=0 纯 GT，1 epoch，3 seed。
# 数据 data/cn_general/（train 4608 / val 991 / test 991，CMExam 全科重分割）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_14B:-$HOME/arthas/mentalDistill/models/Qwen2.5-14B-Instruct}"
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=0

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/cn_general/runs/14B_a00_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN 14B_a00_s${seed}"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/cn_general/train.jsonl \
    --val_path data/cn_general/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
done

echo "评估（3 seed）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/cn_general/runs/14B_a00_s${seed}" \
    --test data/cn_general/test.jsonl --lang zh
done
