# 中文全科：Qwen2.5-14B 学生超越 DeepSeek-V4-flash 教师

## 实验规格
- 老师：DeepSeek-V4-flash（deepseek-chat API），中文全科零样本 **87.18%**
- 学生：Qwen2.5-14B（α=0 纯标准答案蒸馏，3 seed）
- 历史结果（mentalDistill 15 口径）：学生 **88.67%**（3-seed 均值，best 89.10%）超老师 +1.49pp

## 数据（data/cn_general/）
| 集合 | 条数 | 来源 |
|---|---|---|
| train | 4608 | CMExam 全科重分割 |
| val | 991 | CMExam |
| test | 991 | CMExam |

> 生成：`data/prepare_cn_general.py`（直接拷贝 mentalDistill 15 的划分）。

## 训练参数
Choice-Head 蒸馏，α=0；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch；3 seed(11/42/8)。

## 复现
```bash
bash experiments/cn_general/scripts/run_train.sh
```

## 如何核对参数
`experiments/cn_general/scripts/run_train.sh` 里的 `--rank 16 --lora_alpha 32 --learning_rate 1e-4
--batch_size 1 --gradient_accumulation_steps 8 --num_epochs 1 --alpha 0.0`。
