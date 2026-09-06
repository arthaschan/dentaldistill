#!/usr/bin/env bash
# 英文牙科 v2（重新切分）从头做：data/en_dental_v2/（train 519 / val 74 / test 148）。
# 教师 Qwen3-32B 零样本，学生 Llama-70B（历史最优英文学生，r16/lr1e-4，4bit），3 seed。
# 英文池子小（741），test 只能到 148；预期效果弱于中文（~1pp vs ~2pp），如实记录。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
M="$HOME/arthas/mentalDistill/models"
TEACHER="$M/Qwen3-32B"
STUDENT="$M/Llama-3.3-70B-Instruct"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1
LOG="retrain_en_v2_queue.log"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date '+%F %H:%M:%S')] en-v2 queue START"

echo "[$(date +%H:%M:%S)] 教师 Qwen3-32B 零样本 (en_dental_v2/test 148)"
"$PY" shared/eval_choice_head.py --model "$TEACHER" --test data/en_dental_v2/test.jsonl --lang en

echo "[$(date +%H:%M:%S)] 学生 Llama-70B 零样本 (test 148)"
"$PY" shared/eval_choice_head.py --model "$STUDENT" --test data/en_dental_v2/test.jsonl --lang en --quantize 4bit

SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/en_dental/runs/Llama70B_v2_r16_lr1e-4_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN $out (train_v2 519)"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/en_dental_v2/train.jsonl \
    --val_path data/en_dental_v2/val.jsonl \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic --quantize 4bit \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done

echo "评估（3 seed，en_dental_v2/test 148）:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/en_dental/runs/Llama70B_v2_r16_lr1e-4_s${seed}" \
    --test data/en_dental_v2/test.jsonl --lang en --quantize 4bit
done

echo "[$(date '+%F %H:%M:%S')] en-v2 queue END"
