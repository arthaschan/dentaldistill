#!/usr/bin/env bash
# 英文全科 Llama-70B 最优配置 3-seed 坐实（参数化 <rank> <lr>）。
# 用法: run_train_llama_best_3seed.sh <rank> <lr>
# 数据 data/en_general/（train 9789 / val 1017 / test 4110）。
# 教师 Qwen3-32B 零样本基线 = 80.22%（test 4110）。
# 默认 rank16/lr1e-4 = 81.39%；细扫最优 rank8/lr1e-4 = 82.75%（单 seed42）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_LLAMA70B:-$HOME/arthas/mentalDistill/models/Llama-3.3-70B-Instruct}"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1

RANK="${1:?用法: run_train_llama_best_3seed.sh <rank> <lr>}"
LR="${2:?用法: run_train_llama_best_3seed.sh <rank> <lr>}"
ALPHA=$((RANK*2))
TAG="r${RANK}_lr${LR}"

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/en_general/runs/Llama70B_${TAG}_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN Llama70B_${TAG}_s${seed}"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/en_general/train.jsonl \
    --val_path data/en_general/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate "$LR" --rank "$RANK" --lora_alpha "$ALPHA" --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic --quantize 4bit \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log（继续下一 seed）"; continue; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done

echo "评估（test 4110）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/en_general/runs/Llama70B_${TAG}_s${seed}" \
    --test data/en_general/test.jsonl --lang en --quantize 4bit
done
