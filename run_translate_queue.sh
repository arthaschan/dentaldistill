#!/usr/bin/env bash
# 牙科数据互译队列：英->中（en_dental train 566）+ 中->英（cn_dental train 381）。
# 用 Qwen2.5-32B 本地翻译（无 API key），断点续跑（按 uid 跳过）。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/
PY="/home/student/anaconda3/bin/python3"
LOG="translate_queue.log"
exec > >(tee -a "$LOG") 2>&1

echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] translate queue START"
echo "=================================================================="

echo ""
echo "############ 英->中：en_dental train 566 -> 中文 ############"
"$PY" data/translate_mcq.py \
  --src data/en_dental/train.jsonl \
  --out data/translate_en2zh_train.jsonl \
  --direction en2zh
echo "EN2ZH_RC=$?"

echo ""
echo "############ 中->英：cn_dental train 381 -> 英文 ############"
"$PY" data/translate_mcq.py \
  --src data/cn_dental_clean/train.jsonl \
  --out data/translate_zh2en_train.jsonl \
  --direction zh2en
echo "ZH2EN_RC=$?"

echo ""
echo "=================================================================="
echo "[$(date '+%F %H:%M:%S')] translate queue END"
echo "=================================================================="
