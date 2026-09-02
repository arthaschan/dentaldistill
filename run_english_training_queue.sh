#!/usr/bin/env bash
# 英文训练队列：英文全科 + 英文牙科，各 2 个学生（Qwen2.5-32B / Llama-3.3-70B）。
# 单卡 H100 95GB，串行执行避免 OOM。
# 数据：en_general（train 9789 / val 1017 / test 4110，含 2 本单选书）
#       en_dental（train 566 / val 26 / test 84，R1 严格口径零非牙科，含 2 本书牙科题）
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"   # -> dentaldistill/（本脚本就在根目录）
PY="${EASYEDIT_PY:-$HOME/anaconda3/bin/python3}"

run_one() {
  local tag="$1"; shift
  echo ""
  echo "================================================================"
  echo "[$(date +%H:%M:%S)] === $tag ==="
  echo "================================================================"
  "$@" || { echo "[FATAL] $tag 失败 rc=$?"; return 1; }
}

# 1) 英文全科 Qwen2.5-32B
run_one "en_general Qwen2.5-32B" bash experiments/en_general/scripts/run_train.sh || exit 1

# 2) 英文全科 Llama-70B (QLoRA)
run_one "en_general Llama-70B" bash experiments/en_general/scripts/run_train_llama.sh || exit 1

# 3) 英文牙科 Qwen2.5-32B
run_one "en_dental Qwen2.5-32B" bash experiments/en_dental/scripts/run_train.sh || exit 1

# 4) 英文牙科 Llama-70B (QLoRA)
run_one "en_dental Llama-70B" bash experiments/en_dental/scripts/run_train_llama.sh || exit 1

echo ""
echo "[$(date +%H:%M:%S)] === 英文训练队列全部完成 ==="
