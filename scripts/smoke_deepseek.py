#!/usr/bin/env python3
"""DeepSeek 官方 API 冒烟测试 + 余额查询（不打印 key）。
用法: python3 scripts/smoke_deepseek.py
"""
import json
import re
import sys

import requests

# 从 mentalDistill/setup.env 读 key（不打值）
key = ""
for line in open("/home/student/arthas/mentalDistill/setup.env", encoding="utf-8"):
    m = re.match(r'^export\s+DEEPSEEK_API_KEY="([^"]*)"', line.strip())
    if m and m.group(1):
        key = m.group(1)
        break

if not key:
    print("[FATAL] 未找到 DEEPSEEK_API_KEY")
    sys.exit(1)
print(f"key 长度: {len(key)}（前缀 {key[:6]}...）")

BASE = "https://api.deepseek.com"
H = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# 1) 余额
try:
    r = requests.get(BASE + "/user/balance", headers=H, timeout=20)
    print("[balance]", r.status_code, r.text[:300])
except Exception as e:
    print("[balance ERR]", e)

# 2) 冒烟对话
try:
    r = requests.post(
        BASE + "/v1/chat/completions",
        headers=H,
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "只回复字母A"}],
              "max_tokens": 4, "temperature": 0},
        timeout=30,
    )
    print("[chat]", r.status_code, r.text[:300])
except Exception as e:
    print("[chat ERR]", e)
