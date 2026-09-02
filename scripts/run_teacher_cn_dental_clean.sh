#!/usr/bin/env bash
# 任务2：生成 DeepSeek-V4-flash 教师在干净中文牙科测试集(76题)上的零样本标签。
# key 从 mentalDistill/setup.env 读取，不打值。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # -> dentaldistill/
PY="${EASYEDIT_PY:-/home/student/anaconda3/bin/python3}"

# 读取 DEEPSEEK_API_KEY（不打值）
KEY="$($PY - <<'PYEOF'
import re
for line in open("/home/student/arthas/mentalDistill/setup.env", encoding="utf-8"):
    m = re.match(r'^export\s+DEEPSEEK_API_KEY="([^"]*)"', line.strip())
    if m and m.group(1):
        print(m.group(1))
        break
PYEOF
)"
if [ -z "$KEY" ]; then
  echo "[FATAL] 未找到 DEEPSEEK_API_KEY"
  exit 1
fi
export DEEPSEEK_API_KEY="$KEY"
echo "key 已导入（长度 ${#KEY}）"

DATASET="data/cn_dental_clean/test.jsonl"
OUT="teachers/deepseek_v4flash_cn_dental_clean_test.jsonl"
CAND="teachers/deepseek_v4flash.json"
SP="shared/system_prompt_mcq_cn.txt"

echo "=== 教师标签生成: DeepSeek-V4-flash -> $DATASET ($(wc -l < "$DATASET") 题) ==="
"$PY" shared/generate_teacher_labels_api.py \
    --candidate "$CAND" --system_prompt "$SP" \
    --dataset "$DATASET" --output "$OUT" \
    --request_interval_sec 0.3 --max_retries 6 --rate_limit_cooldown_sec 30 \
    2>&1 | tail -6

echo "=== 教师同集准确率 ==="
"$PY" - "$OUT" <<'PYEOF'
import json, sys
n = c = 0
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    gt = str(r.get("OriginalAnswer") or r.get("Answer", "")).strip().upper()
    ta = str(r.get("TeacherAnswer") or "").strip().upper()
    if gt in "ABCDE" and ta in "ABCDE":
        n += 1
        c += int(gt == ta)
print(f"教师 DeepSeek-V4-flash 零样本: {100*c/n:.2f}% ({c}/{n})" if n else "0 题")
PYEOF
