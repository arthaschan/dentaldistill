#!/usr/bin/env bash
# 中文牙科 v3（重新切分）从头训练：data/cn_dental_v3/（train 6239 / val 347 / test 346）。
# 配置沿用超参扫描确认的最优：rank16/lr2e-4/1epoch/α0，3 seed（11/42/8）。
# 教师（DeepSeek-V4-flash）与旧 84 口径不同，本套全部在 v3 上重做，不复用旧实验产物。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=0
LOG="retrain_cn_v3_queue.log"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date '+%F %H:%M:%S')] cn-v3 queue START"

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/cn_dental/runs/Qwen25_cn_v3_r16_lr2e4_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN $out (train_v3 6239)"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/cn_dental_v3/train.jsonl \
    --val_path data/cn_dental_v3/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 2e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done

echo "评估（3 seed，v3 测试集 346 题）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/cn_dental/runs/Qwen25_cn_v3_r16_lr2e4_s${seed}" \
    --test data/cn_dental_v3/test.jsonl --lang zh
done

echo "[$(date '+%F %H:%M:%S')] cn-v3 queue END"
