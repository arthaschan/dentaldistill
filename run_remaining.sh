#!/usr/bin/env bash
# 顺序执行：中文全科训练 -> 消融实验（干净中文牙科网格）。
# 注：中文牙科(干净)训练已单独完成（experiments/cn_dental/runs/Qwen3_cn_a00_clean_s*）。
# 顺序执行（非并发），避免单卡 H100 95GB OOM。
set -uo pipefail
cd /home/student/arthas/dentaldistill

echo "[$(date +%H:%M:%S)] === cn_general (Qwen2.5-14B, 3 seed) ==="
bash experiments/cn_general/scripts/run_train.sh || { echo "[FATAL] cn_general 失败"; exit 1; }

echo "[$(date +%H:%M:%S)] === ablation (干净中文牙科网格) ==="
bash ablation/run_ablation_clean.sh || { echo "[FATAL] ablation 失败"; exit 1; }

echo "[$(date +%H:%M:%S)] === ALL DONE ==="
