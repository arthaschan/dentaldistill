#!/usr/bin/env bash
# 中文牙科 v2 重训：挖出 CMExam train.csv + val.csv 的牙科题扩充训练集（381 -> 6762）。
# 目标：验证「同域加数据」能否让 Qwen2.5-32B 学生超越教师（教师 86.90%）。
# 数据 data/cn_dental_clean/train_v2.jsonl（6762 = 原 381 + 挖矿 6381）。
# val/test 保持不变（val 80 / test 84），与历史结果可比。
# 配置与历史最优一致：rank16/lr2e-4/1epoch/α0，3 seed（11/42/8）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=0
LOG="retrain_cn_v2_queue.log"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date '+%F %H:%M:%S')] retrain-cn-v2 queue START"

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/cn_dental/runs/Qwen25_cn_v2_r16_lr2e4_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN $out (train_v2 6762)"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/cn_dental_clean/train_v2.jsonl \
    --val_path data/cn_dental_clean/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 2e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done

echo "评估（3 seed，干净测试集 84 题）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/cn_dental/runs/Qwen25_cn_v2_r16_lr2e4_s${seed}" \
    --test data/cn_dental_clean/test.jsonl --lang zh
done

echo "[$(date '+%F %H:%M:%S')] retrain-cn-v2 queue END"
