#!/usr/bin/env bash
# 中文牙科（干净子集 v2）参数细扫 —— 学生 = Qwen2.5-32B，α=0，seed=42。
# 在任务 a 的默认配置（rank16/lr1e-4/1ep）之外，细扫 lr 2e-4/5e-4、rank4、2 epoch。
# 数据 data/cn_dental_clean/（train 381 / val 80 / test 84）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=zh
export DISTILL_USE_CHAT_TEMPLATE=0

DATA="data/cn_dental_clean"
SEED=42
RESULT="ablation/results_cn_dental_clean_qwen25.tsv"
[[ -f "$RESULT" ]] || echo -e "rank\tlr\tepoch\tval_acc\ttest_acc" > "$RESULT"

# 细扫网格：rank{4,8,16} × lr{1e-4,2e-4,3e-4,5e-4} × epoch{1,2}
RANKS=(4 8 16)
LRS=(1e-4 2e-4 3e-4 5e-4)
EPOCHS=(1 2)

for rank in "${RANKS[@]}"; do
  for lr in "${LRS[@]}"; do
    for ep in "${EPOCHS[@]}"; do
      name="r${rank}_lr${lr}_e${ep}"
      out="ablation/runs/cn_dental_clean_qwen25/${name}"
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
                 --test "$DATA/val.jsonl" --lang zh 2>/dev/null | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
      test_acc=$("$PY" shared/eval_choice_head.py --model "$STUDENT" --adapter "$out" \
                 --test "$DATA/test.jsonl" --lang zh 2>/dev/null | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
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
