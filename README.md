# dentaldistill — 牙科/医学选择题"学生超越教师"蒸馏实验（可审计复现版）

把 `mentalDistill` 里"学生超越教师"的 4 个场景，重建成干净、可审计、可复现的仓库。
核心承诺：**每个实验明确「数据来源 / 数据条数 / 实验参数」，并能回答"这些数字在代码的哪里、怎么查"，供人工与 AI 逐项核对。**

---

## 四场景总览

| 场景 | 老师 | 学生 | 数据来源 | train/val/test |
|---|---|---|---|---|
| 中文全科 | DeepSeek-V4-flash | Qwen2.5-14B | CMExam 全科重分割 | 4608 / 991 / 991 |
| 中文牙科 | DeepSeek-V4-flash | Qwen3-32B | CMExam「口腔医学」学科 | 580 / 125 / 125 |
| 英文全科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | MedQA + MMLU（无印度） | 9151 / 1017 / 4110 |
| 英文牙科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | MedQA+MMLU 牙科 + 3 本书 | 497 / 26 / 85 |

> 训练参数（四场景统一）：Choice-Head 蒸馏，α=0（纯标准答案监督）；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch。唯一差异：Llama-3.3-70B 用 QLoRA 4bit。

---

## 快速开始

```bash
# 0. 环境（anaconda，含 torch/transformers/peft）
export PY=/home/student/anaconda3/bin/python3

# 1. 准备数据（从 mentalDistill 派生，输出 data/<场景>/train|val|test.jsonl）
$PY data/prepare_cn_general.py
$PY data/prepare_cn_dental.py
$PY data/prepare_en_general.py
$PY data/prepare_en_dental.py        # 依赖 books/ 提取产物（见 books/README.md）

# 2. 审计牙科子集（应全部 [PASS]）
$PY data/check_dental_subset.py data/cn_dental/train.jsonl
$PY data/check_dental_subset.py data/en_dental/test.jsonl

# 3. 训练 + 评估（见 experiments/<场景>/README.md）
#   例如中文牙科：bash experiments/cn_dental/scripts/run_train.sh
```

---

## 目录结构

```
dentaldistill/
├── README.md              # 本文件
├── PLAN.md                # 落地方案
├── HANDOVER.md            # 交接/审计文档（给 AI 审计）
├── data/                  # 数据 + 管线 + 审计工具
│   ├── README.md          # 数据来源/条数/查询方法/判定依据
│   ├── dental_filter.py   # 牙科判定（修复 oral 误判）
│   ├── check_dental_subset.py  # 检查工具（证明无非牙科数据）
│   ├── prepare_*.py       # 各场景数据准备
│   └── split_train_val_test.py
├── books/                 # 3 本教材 + 提取脚本
├── shared/                # 训练/评估脚本
├── experiments/           # cn_general / cn_dental / en_general / en_dental
└── ablation/              # 消融实验
```

---

## 关键文档索引

- 数据来源/条数/查询方法：`data/README.md`
- 牙科判定规则 + 判断依据：`data/dental_filter.py`（顶部 docstring）
- 完整方案与落地状态：`PLAN.md`
- 面向 AI 审计的交接：`HANDOVER.md`
- 每个实验的复现：`experiments/<场景>/README.md`

---

## 一个重要背景：牙科子集的 "oral" 误判已修复

旧 mentalDistill 用 `\boral\b` 关键词筛牙科，把"oral = 口服/oral medication"的题误判成牙科（实测英文牙科 501 题里 311 道是非牙科）。本仓库用**收紧后的判定**（强关键词 + "oral" 口腔语境，裸 "oral" 排除）+ **学科字段**（中文「口腔医学」、MedMCQA「Dental」），并提供 `check_dental_subset.py` 逐题审计。详见 `PLAN.md` 第 3 节。
