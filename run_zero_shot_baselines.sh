#!/usr/bin/env bash
# 候选学生零样本基线测量 —— 为「换学生实现超越」选型。
# 在 cn_dental_clean/test(84) 与 en_dental/test(84) 上测各候选模型零样本准确率。
# 教师基线：中文牙科 DeepSeek-V4-flash 86.90%；英文牙科 Qwen3-32B 66.67%。
# 现学生（蒸馏后）：Qwen2.5-32B 中文 86.90% / 英文 66.27%；Llama-70B 英文 67.06%。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/
source setup.env 2>/dev/null || true
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"
M="$HOME/arthas/mentalDistill/models"
LOG="zero_shot_baselines.log"

# 等当前 Llama 3-seed 结束，避免抢 GPU / OOM
echo "[$(date +%H:%M:%S)] 等待当前 Llama 3-seed 结束（避免抢 GPU）..."
while pgrep -f 'run_train_llama_best_3seed.sh' >/dev/null 2>&1; do sleep 60; done
echo "[$(date +%H:%M:%S)] GPU 空闲，开始零样本基线测量"

exec > >(tee -a "$LOG") 2>&1
export DISTILL_USE_CHAT_TEMPLATE=1

eval_zero() {
  local tag="$1" model="$2" quant="$3" lang="$4" test="$5"
  local q=""
  [[ "$quant" == "4bit" ]] && q="--quantize 4bit"
  export DISTILL_PROMPT_LANG="$lang"
  echo ""
  echo "[$(date +%H:%M:%S)] === $tag  (lang=$lang) ==="
  "$PY" shared/eval_choice_head.py --model "$model" $q --test "$test" --lang "$lang" 2>/dev/null \
    || echo "  [ERR] $tag 失败 rc=$?"
}

echo "########## 中文牙科 test 84（教师 DeepSeek-V4-flash 86.90%）##########"
eval_zero "Qwen2.5-32B（现学生）"       "$M/Qwen2.5-32B-Instruct"       none zh data/cn_dental_clean/test.jsonl
eval_zero "Qwen3-32B-Instruct"          "$M/Qwen3-32B-Instruct"          none zh data/cn_dental_clean/test.jsonl
eval_zero "DeepSeek-R1-Distill-Qwen-32B" "$M/DeepSeek-R1-Distill-Qwen-32B" none zh data/cn_dental_clean/test.jsonl
eval_zero "Llama-3.3-70B"               "$M/Llama-3.3-70B-Instruct"      4bit zh data/cn_dental_clean/test.jsonl

echo ""
echo "########## 英文牙科 test 84（教师 Qwen3-32B 66.67%）##########"
eval_zero "Qwen2.5-32B（现学生）"       "$M/Qwen2.5-32B-Instruct"       none en data/en_dental/test.jsonl
eval_zero "Qwen3-32B-Instruct"          "$M/Qwen3-32B-Instruct"          none en data/en_dental/test.jsonl
eval_zero "DeepSeek-R1-Distill-Qwen-32B" "$M/DeepSeek-R1-Distill-Qwen-32B" none en data/en_dental/test.jsonl
eval_zero "Llama-3.3-70B"               "$M/Llama-3.3-70B-Instruct"      4bit en data/en_dental/test.jsonl

echo ""
echo "[$(date +%H:%M:%S)] 零样本基线测量完成"
