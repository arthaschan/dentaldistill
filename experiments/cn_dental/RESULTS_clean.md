# 中文牙科（干净子集）训练结果 — Qwen3-32B

> 数据：`data/cn_dental_clean/`（train 340 / val 73 / test 76，内容级重筛纯牙科）。
> 学生：Qwen3-32B；Choice-Head 蒸馏，α=0，LoRA rank16/alpha32，lr 1e-4，batch 1×8，1 epoch，3 seed(11/42/8)。
> 复现：`bash experiments/cn_dental/scripts/run_train_clean.sh`。

## 结果（2026-09-01）

| seed | val acc | test acc |
|---|---|---|
| 11 | 80.82% | 77.63% |
| 42 | 75.34% | 80.26% |
| 8  | 82.19% | 80.26% |
| **均值** | **79.45%** | **79.38%** |

## 说明

- 这是**干净牙科子集**（剔除约 41% 通科医学污染）上的结果，与历史 mentalDistill 22 的
  「82.40%±0.80 vs 教师 79.20%」不可直接比较（数据/测试集已不同）。
- 教师 DeepSeek-V4-flash 在本干净测试集（76 题）上的零样本 baseline 尚未重跑（需 API），
  「学生是否超越教师」待教师基线补跑后再判定。
- 训练产物：`experiments/cn_dental/runs/Qwen3_cn_a00_clean_s{11,42,8}/`（gitignored）。

## 污染检测结论（关联）

原 `data/cn_dental/`（学科字段「口腔医学」拆分）经内容级检测发现约 **35%–42% 非牙科**
（药理/儿科/妇产/统计/伦理/传染病等通科题），详见 `reports/cn_dental_content_report.md`。
