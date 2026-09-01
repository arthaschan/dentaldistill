#!/usr/bin/env bash
# 英文全科：Qwen2.5-32B 学生，α=0 纯 GT，1 epoch，seed 42。
# 数据 data/en_general/（train 9151 / val 1017 / test 4110，MedQA+MMLU 无印度）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1

out="experiments/en_general/runs/32B_a00_s42"
mkdir -p "$out"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$STUDENT" \
  --data_path data/en_general/train.jsonl \
  --val_path data/en_general/val.jsonl \
  --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic \
  > "$out/train.log" 2>&1
touch "$out/DONE"

echo "评估:"
"$PY" shared/eval_choice_head.py --model "$STUDENT" --adapter "$out" \
  --test data/en_general/test.jsonl --lang en
