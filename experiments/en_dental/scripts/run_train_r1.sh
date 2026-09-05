#!/usr/bin/env bash
# 英文牙科：DeepSeek-R1-Distill-Qwen-32B 学生（α=0 纯 GT，1 epoch，seed 42）。
# 关键：R1 零样本 66.67% = 教师 Qwen3-32B 66.67%（headroom=0），蒸馏有望明显超越。
# prompt 用 Qwen 硬编码格式（DISTILL_USE_CHAT_TEMPLATE=0）——R1 对该格式响应正常，
# 其自带的 DeepSeek 模板（chat_template=1）反而输出 malformed（实测见 eval_r1_zeroshot.py 注释）。
# 数据 data/en_dental/（train 566 / val 26 / test 84，R1 严格口径零非牙科）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="$HOME/arthas/mentalDistill/models/DeepSeek-R1-Distill-Qwen-32B"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=0

out="experiments/en_dental/runs/R1_a00_s42"
mkdir -p "$out"
"$PY" shared/train_choice_head_distill.py \
  --model_name "$STUDENT" \
  --data_path data/en_dental/train.jsonl \
  --val_path data/en_dental/val.jsonl \
  --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
  --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
  --default_distill_mask 1 --seed 42 --deterministic \
  > "$out/train.log" 2>&1
touch "$out/DONE"

echo "训练完成。评测（thinking 感知，max_new_tokens=2048）："
echo "  python3 eval_r1_zeroshot.py --adapter $out  （待实现 --adapter 参数）"
