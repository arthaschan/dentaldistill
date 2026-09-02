# 中文全科训练结果 — Qwen2.5-14B

> 数据：`data/cn_general/`（train 4608 / val 991 / test 991，CMExam 全科重分割）。
> 学生：Qwen2.5-14B；Choice-Head 蒸馏，α=0，LoRA rank16/alpha32，lr 1e-4，batch 1×8，1 epoch，3 seed(11/42/8)。
> 复现：`bash experiments/cn_general/scripts/run_train.sh`。

## 结果（2026-09-01）

| seed | val acc | test acc |
|---|---|---|
| 11 | 90.11% | 89.51% |
| 42 | 89.00% | 88.80% |
| 8  | 88.40% | 88.60% |
| **均值** | **89.17%** | **88.97%** |

## 与历史/教师对比

- 历史结果（mentalDistill 15）：学生 88.67%（3-seed 均值，best 89.10%）vs 教师 DeepSeek-V4-flash 87.18%（+1.49pp）。
- 本次 test 均值 **88.97%**，与历史口径一致（略高），学生仍高于教师 87.18% 约 +1.79pp。
- 训练产物：`experiments/cn_general/runs/14B_a00_s{11,42,8}/`（gitignored）。
