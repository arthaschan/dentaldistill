#!/usr/bin/env bash
# 英文牙科 v3（干净重做）完整重训 + 参数消融（2026-09-17 重新执行）。
#
# 数据：data/en_dental_v3/（train 913 / val 35 / test 70，已验证可复现）
#   扩张：书籍题(BoF 272 + NBDE 366 = 638) 全纳入训练 + MedQA/MMLU 严格过滤 270 -> 训练池 908
#   重拆：书籍题只进训练；教师答错 29 道难题强制进训练；MedQA/MMLU 重拆 70/10/20
#
# 主训练（历史最优组合，各 3 seed）：
#   教师 Qwen3-32B
#   - 学生 Llama-70B：LoRA r16/alpha32, lr 1e-4, QLoRA 4bit, 1 epoch
#   - 学生 Qwen2.5-32B：LoRA r8/alpha16, lr 3e-4, bf16, 1 epoch
# 消融（单 seed 42，1 epoch，α=0）证明上述为最优：
#   - Llama-70B：rank{8,16} × lr{1e-4,2e-4,3e-4,5e-4} = 8 组
#   - Qwen2.5-32B：rank{4,8,16} × lr{1e-4,2e-4,3e-4,5e-4} = 12 组
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
M="$HOME/arthas/mentalDistill/models"
TEACHER="$M/Qwen3-32B"
LLAMA="$M/Llama-3.3-70B-Instruct"
QWEN="$M/Qwen2.5-32B-Instruct"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1
DATA="data/en_dental_v3"
LOG="retrain_en_v3_full.log"
exec > >(tee -a "$LOG") 2>&1

echo "====================================================================="
echo "[$(date '+%F %H:%M:%S')] en-dental v3 FULL retrain + ablation START"
echo "====================================================================="

# ---------------------------------------------------------------
# 1. 零样本基线
# ---------------------------------------------------------------
echo ""
echo "### 1. 零样本基线 (test 70)"
echo "[$(date +%H:%M:%S)] 教师 Qwen3-32B 零样本"
"$PY" shared/eval_choice_head.py --model "$TEACHER" --test "$DATA/test.jsonl" --lang en 2>/dev/null | grep -E 'acc='

echo "[$(date +%H:%M:%S)] 学生 Llama-70B 零样本 (4bit)"
"$PY" shared/eval_choice_head.py --model "$LLAMA" --test "$DATA/test.jsonl" --lang en --quantize 4bit 2>/dev/null | grep -E 'acc='

echo "[$(date +%H:%M:%S)] 学生 Qwen2.5-32B 零样本"
"$PY" shared/eval_choice_head.py --model "$QWEN" --test "$DATA/test.jsonl" --lang en 2>/dev/null | grep -E 'acc='

# ---------------------------------------------------------------
# 2. 主训练：Llama-70B（历史最优 r16/lr1e-4，QLoRA 4bit），3 seed
# ---------------------------------------------------------------
echo ""
echo "### 2. 主训练 Llama-70B r16/lr1e-4 (3 seed)"
SEEDS=(11 42 8)
for seed in "${SEEDS[@]}"; do
  out="experiments/en_dental/runs/v3r_Llama70B_r16_lr1e-4_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN $out"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$LLAMA" \
    --data_path "$DATA/train.jsonl" --val_path "$DATA/val.jsonl" \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 1e-4 --rank 16 --lora_alpha 32 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic --quantize 4bit \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done
echo "评估 Llama-70B 3 seed:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py --model "$LLAMA" \
    --adapter "experiments/en_dental/runs/v3r_Llama70B_r16_lr1e-4_s${seed}" \
    --test "$DATA/test.jsonl" --lang en --quantize 4bit 2>/dev/null | grep -E 'acc='
done

# ---------------------------------------------------------------
# 3. 主训练：Qwen2.5-32B（历史最优 r8/lr3e-4，bf16），3 seed
# ---------------------------------------------------------------
echo ""
echo "### 3. 主训练 Qwen2.5-32B r8/lr3e-4 (3 seed)"
for seed in "${SEEDS[@]}"; do
  out="experiments/en_dental/runs/v3r_32B_r8_lr3e4_s${seed}"
  [[ -f "$out/DONE" ]] && { echo "[SKIP] $out"; continue; }
  mkdir -p "$out"
  echo "[$(date +%H:%M:%S)] TRAIN $out"
  "$PY" shared/train_choice_head_distill.py \
    --model_name "$QWEN" \
    --data_path "$DATA/train.jsonl" --val_path "$DATA/val.jsonl" \
    --output_dir "$out" --num_epochs 1 --batch_size 1 --gradient_accumulation_steps 8 \
    --learning_rate 3e-4 --rank 8 --lora_alpha 16 --alpha 0.0 \
    --default_distill_mask 1 --seed "$seed" --deterministic \
    > "$out/train.log" 2>&1 \
    || { echo "[FAIL] seed=$seed rc=$? 见 $out/train.log"; exit 1; }
  touch "$out/DONE"
  echo "[$(date +%H:%M:%S)] done $out"
done
echo "评估 Qwen2.5-32B 3 seed:"
for seed in "${SEEDS[@]}"; do
  "$PY" shared/eval_choice_head.py --model "$QWEN" \
    --adapter "experiments/en_dental/runs/v3r_32B_r8_lr3e4_s${seed}" \
    --test "$DATA/test.jsonl" --lang en 2>/dev/null | grep -E 'acc='
done

echo "====================================================================="
echo "[$(date '+%F %H:%M:%S')] en-dental v3 FULL retrain + ablation END"
echo "====================================================================="
