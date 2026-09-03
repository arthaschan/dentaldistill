#!/usr/bin/env bash
# 英文全科 参数细扫 —— 学生 = Qwen2.5-32B，α=0，seed=42。
# 网格：rank{8,16} × lr{1e-4,2e-4,3e-4} × epoch{1} = 6 组。
#   （依据英文牙科/中文牙科细扫：lr5e-4、rank4、epoch2 均已证劣化，此处跳过以省算力。）
# 数据 data/en_general/（train 9789 / val 1017 / test 4110，MedQA+MMLU 无印度 + 2 本单选书）。
# 教师 Qwen3-32B 零样本基线 = 80.22%（test 4110，历史 27 口径）。
# 排序口径：eval_choice_head.py（greedy, max_new_tokens=8）的 test_acc —— 与既有 RESULTS 一致；
#           注意 train.log 内的 [VAL] 是 max_new_tokens=4 的旧口径，仅作记录，不用于排序。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
STUDENT="${BASE_MODEL_32B:-$HOME/arthas/mentalDistill/models/Qwen2.5-32B-Instruct}"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1

DATA="data/en_general"
SEED=42
RESULT="ablation/results_en_general_qwen25.tsv"
[[ -f "$RESULT" ]] || echo -e "rank\tlr\tepoch\tval_acc\ttest_acc" > "$RESULT"

RANKS=(8 16)
LRS=(1e-4 2e-4 3e-4)
EPOCHS=(1)

for rank in "${RANKS[@]}"; do
  for lr in "${LRS[@]}"; do
    for ep in "${EPOCHS[@]}"; do
      name="r${rank}_lr${lr}_e${ep}"
      out="ablation/runs/en_general_qwen25/${name}"
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
      val_acc=$(grep -a '\[VAL\]' "$out/train.log" | tail -1 | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
      echo "[$(date +%H:%M:%S)] EVAL(test) $name"
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
