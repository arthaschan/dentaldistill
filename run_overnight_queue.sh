#!/usr/bin/env bash
# 夜间无人值守队列（英文牙科收尾）：
#   Phase A  Qwen2.5-32B 最优配置 rank8/lr3e-4/e1 跑 3 seed 坐实
#   Phase B  Llama-3.3-70B 参数细扫（rank{4,8,16}×lr{1e-4..5e-4}×e1，断点跳过）
#   Phase C  按 Phase B 结果自动取最优配置，跑 Llama-70B 3 seed 坐实
# 单卡 H100 95GB，串行执行。日志同时写 stdout 与 overnight_queue.log。
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/
LOG="overnight_queue.log"
exec > >(tee -a "$LOG") 2>&1

echo ""
echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] overnight queue START"
echo "=================================================================="

# ---------------- Phase A: Qwen2.5-32B 最优 3-seed ----------------
echo ""
echo "############ Phase A: Qwen2.5-32B rank8/lr3e-4/e1 3-seed ############"
if bash experiments/en_dental/scripts/run_train_qwen25_best_3seed.sh; then
  echo "PHASE_A_RESULT=OK"
else
  echo "PHASE_A_RESULT=FAIL"
fi

# ---------------- Phase B: Llama-70B 细扫 ----------------
echo ""
echo "############ Phase B: Llama-70B 细扫 ############"
if bash ablation/run_sweep_en_dental_llama70b.sh; then
  echo "PHASE_B_RESULT=OK"
else
  echo "PHASE_B_RESULT=FAIL"
fi

# ---------------- Phase C: Llama-70B 最优 3-seed ----------------
echo ""
echo "############ Phase C: Llama-70B 最优 3-seed ############"
TSV="ablation/results_en_dental_llama70b.tsv"
# 取 test_acc 最高的一行（第5列），并列时按 val_acc（第4列）降序；跳过 NA/空。
BEST_LINE=$(awk -F'\t' 'NR>1 && $5!="NA" && $5!="" && $5+0==$5 {print $5"\t"$4"\t"$1"\t"$2}' "$TSV" \
            | sort -t$'\t' -k1,1rn -k2,2rn | head -1)
if [[ -z "$BEST_LINE" ]]; then
  echo "PHASE_C_RESULT=SKIP（细扫无有效 test_acc，回退默认 rank16/lr1e-4）"
  BEST_RANK=16; BEST_LR="1e-4"; BEST_ACC="NA"
else
  BEST_ACC=$(echo "$BEST_LINE" | cut -f1)
  BEST_RANK=$(echo "$BEST_LINE" | cut -f3)
  BEST_LR=$(echo "$BEST_LINE" | cut -f4)
fi
echo "细扫最优 -> rank=$BEST_RANK lr=$BEST_LR test_acc=$BEST_ACC"

# 若最优 test_acc 仍未超教师 66.67%，也照样跑 3-seed（坐实「未超越」结论），
# 除非最优已经是 NA（说明细扫全失败）。
if bash experiments/en_dental/scripts/run_train_llama_best_3seed.sh "$BEST_RANK" "$BEST_LR"; then
  echo "PHASE_C_RESULT=OK"
else
  echo "PHASE_C_RESULT=FAIL"
fi

echo ""
echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] overnight queue END"
echo "=================================================================="
