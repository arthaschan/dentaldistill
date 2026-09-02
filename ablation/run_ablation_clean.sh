#!/usr/bin/env bash
# 消融网格（干净中文牙科）：扫描 α / rank / lr / epoch，训练后自动评测 test，汇总 TSV。
# 数据 data/cn_dental_clean/（train 340 / val 73 / test 76，纯牙科，见 cn_dental_content_report.md）。
# 学生 = Qwen3-32B。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_QWEN3_32B:-$HOME/arthas/mentalDistill/models/Qwen3-32B}"
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=1

DATA="data/cn_dental_clean"
SEED=42
RESULT="ablation/results_cn_dental_clean.tsv"
# 若 TSV 不存在则写表头；存在则续写（支持断点重跑）
[[ -f "$RESULT" ]] || echo -e "alpha\trank\tlr\tepoch\tval_acc\ttest_acc" > "$RESULT"

ALPHAS=(0.0 0.15 0.35)
RANKS=(8 16 64)
LRS=(1e-4 3e-4)
EPOCHS=(1 3)

for alpha in "${ALPHAS[@]}"; do
  for rank in "${RANKS[@]}"; do
    for lr in "${LRS[@]}"; do
      for ep in "${EPOCHS[@]}"; do
        name="a${alpha}_r${rank}_lr${lr}_e${ep}"
        out="ablation/runs/cn_dental_clean/${name}"
        [[ -f "$out/DONE" ]] && { echo "[SKIP] $name"; continue; }
        mkdir -p "$out"
        echo "[$(date +%H:%M:%S)] TRAIN $name"
        "$PY" shared/train_choice_head_distill.py \
          --model_name "$STUDENT" \
          --data_path "$DATA/train.jsonl" --val_path "$DATA/val.jsonl" \
          --output_dir "$out" --num_epochs "$ep" --batch_size 1 \
          --gradient_accumulation_steps 8 --learning_rate "$lr" \
          --rank "$rank" --lora_alpha $((rank*2)) --alpha "$alpha" \
          --default_distill_mask 1 --seed $SEED --deterministic \
          > "$out/train.log" 2>&1 \
          || { echo "[FAIL] $name rc=$? 见 $out/train.log"; exit 1; }
        echo "[$(date +%H:%M:%S)] EVAL $name"
        val_acc=$("$PY" shared/eval_choice_head.py --model "$STUDENT" --adapter "$out/best" \
                   --test "$DATA/val.jsonl" --lang zh 2>/dev/null | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
        test_acc=$("$PY" shared/eval_choice_head.py --model "$STUDENT" --adapter "$out/best" \
                   --test "$DATA/test.jsonl" --lang zh 2>/dev/null | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
        [[ -z "$val_acc" ]] && val_acc="NA"
        [[ -z "$test_acc" ]] && test_acc="NA"
        echo -e "$alpha\t$rank\t$lr\t$ep\t$val_acc\t$test_acc" >> "$RESULT"
        touch "$out/DONE"
        echo "[$(date +%H:%M:%S)] $name -> val=$val_acc test=$test_acc"
      done
    done
  done
done

echo "汇总 -> $RESULT"
cat "$RESULT"
