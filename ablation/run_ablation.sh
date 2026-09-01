#!/usr/bin/env bash
# 消融网格：在指定场景上扫描 α / rank / lr / epoch，输出汇总 TSV。
# 默认场景 = 中文牙科（Qwen3-32B）。可设 SCENARIO=cn_general 等切换。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"

SCENARIO="${SCENARIO:-cn_dental}"
case "$SCENARIO" in
  cn_dental)
    STUDENT="${BASE_MODEL_QWEN3_32B:-$HOME/arthas/mentalDistill/models/Qwen3-32B}"
    LANG=zh; DATA="data/cn_dental";;
  cn_general)
    STUDENT="${BASE_MODEL_14B:-$HOME/arthas/mentalDistill/models/Qwen2.5-14B-Instruct}"
    LANG=zh; DATA="data/cn_general";;
  *)
    echo "未知 SCENARIO=$SCENARIO"; exit 2;;
esac
export DISTILL_PROMPT_LANG=$LANG
export DISTILL_USE_CHAT_TEMPLATE=1

SEED=42
RESULT="ablation/results_${SCENARIO}.tsv"
echo -e "alpha\trank\tlr\tepoch\tval_acc\ttest_acc" > "$RESULT"

ALPHAS=(0.0 0.15 0.35)
RANKS=(8 16 64)
LRS=(1e-4 3e-4)
EPOCHS=(1 3)

for alpha in "${ALPHAS[@]}"; do
  for rank in "${RANKS[@]}"; do
    for lr in "${LRS[@]}"; do
      for ep in "${EPOCHS[@]}"; do
        name="a${alpha}_r${rank}_lr${lr}_e${ep}"
        out="ablation/runs/${SCENARIO}/${name}"
        [[ -f "$out/DONE" ]] && { echo "[SKIP] $name"; continue; }
        mkdir -p "$out"
        echo "[$(date +%H:%M:%S)] $name"
        "$PY" shared/train_choice_head_distill.py \
          --model_name "$STUDENT" \
          --data_path "$DATA/train.jsonl" --val_path "$DATA/val.jsonl" \
          --output_dir "$out" --num_epochs "$ep" --batch_size 1 \
          --gradient_accumulation_steps 8 --learning_rate "$lr" \
          --rank "$rank" --lora_alpha $((rank*2)) --alpha "$alpha" \
          --default_distill_mask 1 --seed $SEED --deterministic \
          > "$out/train.log" 2>&1
        touch "$out/DONE"
      done
    done
  done
done

echo "汇总 -> $RESULT"
echo "（注：val/test acc 需从各 runs/*/train.log 的 [VAL]/测试集准确率 行提取，或重跑 shared/eval_choice_head.py 补测）"
