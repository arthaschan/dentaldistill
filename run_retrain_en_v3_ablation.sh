#!/usr/bin/env bash
# 英文牙科 v3 参数消融（单 seed 42，1 epoch，α=0）—— 证明主训练参数为最优。
# 数据：data/en_dental_v3/（train 913 / val 35 / test 70）。
# 网格：
#   Llama-70B：rank{8,16} × lr{1e-4,2e-4,3e-4,5e-4} = 8 组（QLoRA 4bit）
#   Qwen2.5-32B：rank{4,8,16} × lr{1e-4,2e-4,3e-4,5e-4} = 12 组（bf16）
# 抗共享 GPU 争抢：训练前等待显存阈值；OOM/失败自动重试。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
M="$HOME/arthas/mentalDistill/models"
LLAMA="$M/Llama-3.3-70B-Instruct"
QWEN="$M/Qwen2.5-32B-Instruct"
export DISTILL_PROMPT_LANG=en
export DISTILL_USE_CHAT_TEMPLATE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
DATA="data/en_dental_v3"
SEED=42

# 等待 GPU 空闲 >= need_gb GB（最多 wait_max 秒）
wait_gpu() {
  local need_gb="$1" wait_max="${2:-1800}" waited=0 free_mb=0
  while [[ $waited -lt $wait_max ]]; do
    free_mb=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
    [[ -n "$free_mb" ]] || free_mb=0
    if (( free_mb >= need_gb * 1024 )); then
      return 0
    fi
    sleep 30
    waited=$((waited + 30))
  done
  return 1
}

run_sweep() {
  local student="$1" label="$2" quantize="$3" ranks_str="$4" lrs_str="$5" need_gb="$6"
  local RESULT="ablation/results_en_dental_v3_${label}.tsv"
  [[ -f "$RESULT" ]] || echo -e "rank\tlr\tepoch\tval_acc\ttest_acc" > "$RESULT"
  IFS=' ' read -ra RANKS <<< "$ranks_str"
  IFS=' ' read -ra LRS <<< "$lrs_str"
  for rank in "${RANKS[@]}"; do
    for lr in "${LRS[@]}"; do
      local name="r${rank}_lr${lr}_e1"
      local out="ablation/runs/en_dental_v3_${label}/${name}"
      # 已完成且结果已记录 -> 跳过
      if [[ -f "$out/DONE" ]] && grep -q $'\t'"${lr}"$'\t1' "$RESULT" 2>/dev/null; then
        echo "[SKIP] $label/$name"; continue
      fi
      mkdir -p "$out"
      rm -f "$out/DONE"
      local attempt=0
      while [[ $attempt -lt 5 ]]; do
        attempt=$((attempt + 1))
        echo "[$(date +%H:%M:%S)] wait-gpu ${need_gb}GB for $label/$name (attempt $attempt)"
        wait_gpu "$need_gb" 3600 || { echo "[WAITFAIL] $label/$name 显存不足，跳过（后续手动续跑）"; break; }
        echo "[$(date +%H:%M:%S)] TRAIN $label/$name (attempt $attempt)"
        if "$PY" shared/train_choice_head_distill.py \
          --model_name "$student" \
          --data_path "$DATA/train.jsonl" --val_path "$DATA/val.jsonl" \
          --output_dir "$out" --num_epochs 1 --batch_size 1 \
          --gradient_accumulation_steps 8 --learning_rate "$lr" \
          --rank "$rank" --lora_alpha $((rank*2)) --alpha 0.0 \
          --default_distill_mask 1 --seed $SEED --deterministic \
          ${quantize:+--quantize "$quantize"} \
          > "$out/train.log" 2>&1; then
          break
        else
          echo "[FAIL] $label/$name attempt=$attempt rc=$? 见 $out/train.log"
          sleep 60
        fi
      done
      # 训练成功后评测
      if [[ -f "$out/adapter_model.safetensors" ]]; then
        echo "[$(date +%H:%M:%S)] EVAL $label/$name"
        local val_acc test_acc
        val_acc=$("$PY" shared/eval_choice_head.py --model "$student" --adapter "$out" \
                   --test "$DATA/val.jsonl" --lang en ${quantize:+--quantize "$quantize"} 2>/dev/null \
                   | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
        test_acc=$("$PY" shared/eval_choice_head.py --model "$student" --adapter "$out" \
                   --test "$DATA/test.jsonl" --lang en ${quantize:+--quantize "$quantize"} 2>/dev/null \
                   | grep -oE 'acc=[0-9.]+' | head -1 | cut -d= -f2)
        [[ -z "$val_acc" ]] && val_acc="NA"
        [[ -z "$test_acc" ]] && test_acc="NA"
        echo -e "$rank\t$lr\t1\t$val_acc\t$test_acc" >> "$RESULT"
        touch "$out/DONE"
        echo "[$(date +%H:%M:%S)] $label/$name -> val=$val_acc test=$test_acc"
      else
        echo "[SKIP-EVAL] $label/$name 训练未产出 adapter，不评测"
      fi
    done
  done
  echo "汇总 $RESULT:"
  cat "$RESULT"
}

echo "====================================================================="
echo "[$(date '+%F %H:%M:%S')] en-dental v3 ABLATION START (OOM-resilient)"
echo "====================================================================="

echo ""
echo "### Llama-70B 消融：rank{8,16} × lr{1e-4,2e-4,3e-4,5e-4}"
run_sweep "$LLAMA" "llama70b" "4bit" "8 16" "1e-4 2e-4 3e-4 5e-4" 57

echo ""
echo "### Qwen2.5-32B 消融：rank{4,8,16} × lr{1e-4,2e-4,3e-4,5e-4}"
run_sweep "$QWEN" "qwen25" "" "4 8 16" "1e-4 2e-4 3e-4 5e-4" 68

echo "====================================================================="
echo "[$(date '+%F %H:%M:%S')] en-dental v3 ABLATION END"
echo "====================================================================="
