# 英文牙科：Qwen2.5-32B / Llama-3.3-70B 学生超越 Qwen3-32B 弱教师

## 实验规格
- 老师：Qwen3-32B（开源弱教师）
- 学生：Qwen2.5-32B / Llama-3.3-70B（α=0 纯标准答案蒸馏，seed 42）
- 说明：本仓库**用牙科专属数据重新训练**（不同于 mentalDistill 28 复用 27 的 adapter），
  且已修复 "oral" 误判、并入 3 本书。

## 数据（data/en_dental/，已审计全牙科）
| 集合 | 条数 | 来源 |
|---|---|---|
| train | 497 | MedQA/MMLU 牙科 219 + 书籍(BoF/NBDE) 278 |
| val | 26 | MedQA/MMLU 牙科 |
| test | 85 | MedQA/MMLU 牙科 |

> 牙科判定：R1 强关键词 + R2 "oral" 口腔语境（裸 "oral" 排除），见 `data/dental_filter.py`。
> 生成：`data/prepare_en_dental.py`（依赖 `books/extract_*.py` + `books/normalize_books.py`）。
> 审计：`python3 data/check_dental_subset.py data/en_dental/test.jsonl`（应 [PASS]）。

## 训练参数
Choice-Head 蒸馏，α=0；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch；seed 42；Llama-70B QLoRA 4bit。

## 复现
```bash
bash experiments/en_dental/scripts/run_train.sh         # Qwen2.5-32B
bash experiments/en_dental/scripts/run_train_llama.sh   # Llama-3.3-70B (QLoRA)
```

## 如何核对参数
`experiments/en_dental/scripts/run_train*.sh` 里的 `--rank 16 --lora_alpha 32 --learning_rate 1e-4
--batch_size 1 --gradient_accumulation_steps 8 --num_epochs 1 --alpha 0.0`。
