#!/usr/bin/env bash
# 中文牙科（干净子集 v2）：Qwen3-32B 学生，α=0 纯 GT，1 epoch，3 seed。
# 数据 data/cn_dental_clean/（train 381 / val 80 / test 84，扩充关键词 + 口腔科科室信号重筛，
#   比旧 489 题多回收 56 题真牙科，见 reports/cn_dental_rescreen_report.md）。
# 输出到 *_clean2_* 目录，与旧 *_clean_*（340/73/76 口径）区分，便于对比。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_QWEN3_32B:-$HOME/arthas/mentalDistill/models/Qwen3-32B}"
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=1

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/cn_dental/runs/Qwen3_cn_a00_clean2_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN Qwen3_cn_a00_clean2_s${seed}"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/cn_dental_clean/train.jsonl \
    --val_path data/cn_dental_clean/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done

echo "评估（3 seed，干净测试集 v2 = 84 题）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/cn_dental/runs/Qwen3_cn_a00_clean2_s${seed}" \
    --test data/cn_dental_clean/test.jsonl --lang zh
done
