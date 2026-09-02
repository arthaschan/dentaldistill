#!/usr/bin/env bash
# 英文牙科 参数细扫 —— 学生 = Qwen2.5-32B，α=0，seed=42。
# 网格：rank{4,8,16} × lr{1e-4,2e-4,3e-4,5e-4} × epoch{1,2} = 24 组。
# 数据 data/en_dental/（train 566 / val 26 / test 84，R1 严格口径零非牙科）。
# 教师 Qwen3-32B 零样本基线 = 66.67%（test 84）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1

DATA="data/en_dental"
SEED=42
RESULT="ablation/results_en_dental_qwen25.tsv"
[[ -f "$RESULT" ]] || echo -e "rank\tlr\tepoch\tval_acc\ttest_acc" > "$RESULT"

RANKS=(4 8 16)
LRS=(1e-4 2e-4 3e-4 5e-4)
EPOCHS=(1 2)

for rank in "${RANKS[@]}"; do
  for lr in "${LRS[@]}"; do
    for ep in "${EPOCHS[@]}"; do
      name="r${rank}_lr${lr}_e${ep}"
      out="ablation/runs/en_dental_qwen25/${name}"
      [[ -f "$out/DONE" ]] && { echo "[SKIP] $name"; continue; }
      mkdir -p "$out"
      echo "[$(date +%H:%M:%S)] TRAIN $name"
      "$PY" shared/train_choice_head_distill.py \
        --model_name "$STUDENT" \
        --data_path "$DATA/train.jsonl" --val_path "$DATA/val.jsonl" \
        --output_dir "$out" --num_epochs "$ep" --batch_size 1 \
        --gradient_accumulation_steps 8 --learning_rate "$lr" \
        --rank "$rank" --lora_alpha $((rank*2)) --alpha 0.0 \
        --default_distill_mask 1 --seed $SEED --deterministic \
        > "$out/train.log" 2>&1 \
        || { echo "[FAIL] $name rc=$? 见 $out/train.log"; exit 1; }
      echo "[$(date +%H:%M:%S)] EVAL $name"
      val_acc=$("$PY" shared/eval_choice_head.py --model "$STUDENT" --adapter "$out" \
                 --test "$DATA/val.jsonl" --lang en 2>/dev/null | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
      test_acc=$("$PY" shared/eval_choice_head.py --model "$STUDENT" --adapter "$out" \
                 --test "$DATA/test.jsonl" --lang en 2>/dev/null | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
      [[ -z "$val_acc" ]] && val_acc="NA"
      [[ -z "$test_acc" ]] && test_acc="NA"
      echo -e "$rank\t$lr\t$ep\t$val_acc\t$test_acc" >> "$RESULT"
      touch "$out/DONE"
      echo "[$(date +%H:%M:%S)] $name -> val=$val_acc test=$test_acc"
    done
  done
done

echo "汇总 -> $RESULT"
cat "$RESULT"
