# 英文全科：Qwen2.5-32B / Llama-3.3-70B 学生超越 Qwen3-32B 弱教师

## 实验规格
- 老师：Qwen3-32B（开源弱教师，零样本 80.22%）
- 学生：Qwen2.5-32B / Llama-3.3-70B（α=0 纯标准答案蒸馏，seed 42）
- 历史结果（mentalDistill 27 口径）：82.19% / 82.09% vs 80.22%（+1.97 / +1.87）

## 数据（data/en_general/）
| 集合 | 条数 | 来源 |
|---|---|---|
| train | 9151 | MedQA 8876 + MMLU 275 |
| val | 1017 | MedQA 986 + MMLU 31 |
| test | 4110 | MedQA 1273 + MMLU 2837 |

> 无印度（去掉 MedMCQA）；生成 `data/prepare_en_general.py`（test 固定，train 按 source 分层切 val）。

## 训练参数
Choice-Head 蒸馏，α=0；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch；seed 42；
Llama-70B 用 QLoRA 4bit（`--quantize 4bit`）。

## 复现
```bash
bash experiments/en_general/scripts/run_train.sh         # Qwen2.5-32B
bash experiments/en_general/scripts/run_train_llama.sh   # Llama-3.3-70B (QLoRA)
```

## 如何核对参数
`experiments/en_general/scripts/run_train*.sh` 里的 `--rank 16 --lora_alpha 32 --learning_rate 1e-4
--batch_size 1 --gradient_accumulation_steps 8 --num_epochs 1 --alpha 0.0`。
