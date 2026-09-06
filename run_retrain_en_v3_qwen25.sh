#!/usr/bin/env bash
# 英文牙科 v3 重试 Qwen2.5-32B（历史 66.27% 打平那个），用新切分 train 913 / test 70。
# 配置沿用历史最优：rank8/lr3e-4/α0，3 seed(11/42/8)，chat template，lang en。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1
LOG="retrain_en_v3_qwen25.log"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date '+%F %H:%M:%S')] en-v3 qwen25 queue START"

echo "[$(date +%H:%M:%S)] 学生 Qwen2.5-32B 零样本 (test 70)"
"$PY" shared/eval_choice_head.py --model "$STUDENT" --test data/en_dental_v3/test.jsonl --lang en

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/en_dental/runs/32B_v3_r8_lr3e4_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN $out (train_v3 913)"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/en_dental_v3/train.jsonl \
    --val_path data/en_dental_v3/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 3e-4 --rank 8 --lora_alpha 16 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done

echo "评估（3 seed，en_dental_v3/test 70）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/en_dental/runs/32B_v3_r8_lr3e4_s${seed}" \
    --test data/en_dental_v3/test.jsonl --lang en
done

echo "[$(date '+%F %H:%M:%S')] en-v3 qwen25 queue END"
