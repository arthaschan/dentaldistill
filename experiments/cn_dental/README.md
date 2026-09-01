# 中文牙科：Qwen3-32B 学生超越 DeepSeek-V4-flash 教师

## 实验规格
- 老师：DeepSeek-V4-flash（deepseek-chat API），中文牙科零样本 **79.20%**
- 学生：Qwen3-32B（α=0 纯标准答案蒸馏，3 seed）
- 历史结果（mentalDistill 22 口径）：学生 **82.40%±0.80** 超老师 +3.20pp（3-seed 全超）

## 数据（data/cn_dental/）
| 集合 | 条数 | 来源 | 牙科判定 |
|---|---|---|---|
| train | 580 | CMExam 全科拆「口腔医学」 | D1 学科字段 |
| val | 125 | CMExam val_dental | D1 学科字段 |
| test | 125 | CMExam test_dental | D1 学科字段 |

> 拆分方法：`Medical Discipline == "口腔医学"`（学科字段，非关键词，无 oral 误判风险）。
> 生成：`data/prepare_cn_dental.py`；审计：`data/check_dental_subset.py`（应 [PASS]）。

## 训练参数
Choice-Head 蒸馏，α=0；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch；3 seed(11/42/8)；
Qwen3 关思考模式（DISTILL_USE_CHAT_TEMPLATE=1 + enable_thinking=False）。

## 复现
```bash
bash experiments/cn_dental/scripts/run_train.sh
```
训练产物：`experiments/cn_dental/runs/Qwen3_cn_a00_s{seed}/`（gitignored）。

## 如何核对参数
`experiments/cn_dental/scripts/run_train.sh` 里的 `--rank 16 --lora_alpha 32 --learning_rate 1e-4
--batch_size 1 --gradient_accumulation_steps 8 --num_epochs 1 --alpha 0.0`。
