#!/usr/bin/env bash
# 中文牙科 6762 题超参扫描：验证「打平」是否对调参稳健。
# 固定 seed=42、数据 train_v2(6762)、α=0、rank16/alpha32、batch1×8。
# 网格：lr ∈ {1e-4, 2e-4, 3e-4} × epoch ∈ {1, 2}。
# (2e-4, 1epoch) 已在 v2 主实验跑过（seed42=90.48%），此处不重复，仅补其余 5 组。
# val(80)/test(84) 不变。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=0
LOG="retrain_cn_v2_sweep.log"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date '+%F %H:%M:%S')] cn-v2 sweep START"

# lr 1e-4 记 1e_4 目录名避免小数点歧义
run() {
  local lr="$1" ep="$2" tag="$3"
  local out="experiments/cn_dental/runs/Qwen25_cn_v2_sweep_${tag}_s42"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; return; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN lr=$lr ep=$ep -> $out"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$STUDENT" \
    --data_path data/cn_dental_clean/train_v2.jsonl \
    --val_path data/cn_dental_clean/val.jsonl \
    --output_dir "$out" --num_epochs "$ep" --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate "$lr" --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed 42 --deterministic \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] lr=$lr ep=$ep rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
}

# 5 组新配置（(2e-4,1) 已有，见主实验）
run 1e-4 1 lr1e-4_e1
run 3e-4 1 lr3e-4_e1
run 1e-4 2 lr1e-4_e2
run 2e-4 2 lr2e-4_e2
run 3e-4 2 lr3e-4_e2

echo "评估（test 84）:"
for tag in lr1e-4_e1 lr3e-4_e1 lr1e-4_e2 lr2e-4_e2 lr3e-4_e2; do
  "$PY" shared/eval_choice_head.py \
    --model "$STUDENT" --adapter "experiments/cn_dental/runs/Qwen25_cn_v2_sweep_${tag}_s42" \
    --test data/cn_dental_clean/test.jsonl --lang zh
done

echo "[$(date '+%F %H:%M:%S')] cn-v2 sweep END"
