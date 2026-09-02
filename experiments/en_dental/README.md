# 英文牙科：Qwen2.5-32B / Llama-3.3-70B 学生超越 Qwen3-32B 弱教师

## 实验规格
- 老师：Qwen3-32B（开源弱教师）
- 学生：Qwen2.5-32B / Llama-3.3-70B（α=0 纯标准答案蒸馏，seed 42）
- 说明：本仓库**用牙科专属数据重新训练**（不同于 mentalDistill 28 复用 27 的 adapter），
  且已修复 "oral" 误判、并入 3 本书。

## 数据（data/en_dental/，R1 严格口径零非牙科）
| 集合 | 条数 | 来源 |
|---|---|---|
| train | 566 | MedQA 200 + MMLU 1 + 书籍(BoF 142 / NBDE 223) |
| val | 26 | MedQA/MMLU 牙科 |
| test | 84 | MedQA/MMLU 牙科 |

> 牙科判定：`data/dental_filter.py` 的 **R1 严格口径**（`is_dental_record_strict`，只用强牙科词
> tooth/dental/gingivitis/periodontal/…，**剔除 R2 "oral" 语境**）。
> 原因：R2 的 oral ulcer/lesion/cavity/candidiasis/thrush 是「全身病的口腔表现」，会把精神分裂
> （oral health）、肺炎（oral lesion）、Zenker 憩室（oral cavity）等非牙科题误判为牙科。
> 详见 `reports/en_dental_audit.md`（含 50 道 R2 边界题清单与严格/宽两种口径的取舍）。
> 生成：`data/prepare_en_dental.py`（已改严格口径）；审计：`python3 data/audit_en_dental.py data/en_dental`。

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
