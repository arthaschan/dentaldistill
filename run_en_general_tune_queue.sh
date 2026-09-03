#!/usr/bin/env bash
# 英文全科（en_general）参数调优队列：两个学生各 6 组细扫，串行执行（单卡 H100）。
#   Qwen2.5-32B 细扫（~4h）→ Llama-70B 细扫（~14h）
# 网格：rank{8,16} × lr{1e-4,2e-4,3e-4} × e1；α=0；seed=42。
# 排序口径：eval_choice_head.py（greedy, max_new_tokens=8）test_acc，与既有 RESULTS_english.md 一致。
# 断点续跑：每组 DONE 跳过。
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/
LOG="en_general_tune_queue.log"
exec > >(tee -a "$LOG") 2>&1

echo ""
echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] en_general tuning queue START"
echo "=================================================================="

echo ""
echo "############ Qwen2.5-32B 细扫（rank{8,16} x lr{1e-4,2e-4,3e-4}） ############"
if bash ablation/run_sweep_en_general_qwen25.sh; then
  echo "QWEN_SWEEP_RESULT=OK"
else
  echo "QWEN_SWEEP_RESULT=FAIL"
fi

echo ""
echo "############ Llama-70B 细扫（rank{8,16} x lr{1e-4,2e-4,3e-4}） ############"
if bash ablation/run_sweep_en_general_llama70b.sh; then
  echo "LLAMA_SWEEP_RESULT=OK"
else
  echo "LLAMA_SWEEP_RESULT=FAIL"
fi

echo ""
echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] en_general tuning queue END"
echo "=================================================================="
