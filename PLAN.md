# dentaldistill 落地方案（PLAN）

> 目标：把 `mentalDistill` 里"学生超越教师"的 4 个场景，重建成一个**干净、可审计、可复现**的新仓库。
> 核心承诺：每个实验明确「数据来源 / 数据条数 / 实验参数」，并能回答"这些数字在代码的哪里、怎么查"，让人工可逐项核对。

---

## 1. 四场景规格（老师 / 学生 / 数据来源）

| 场景 | 老师模型 | 学生模型 | 数据来源 | train/val/test |
|---|---|---|---|---|
| 中文全科 | DeepSeek-V4-flash | Qwen2.5-14B | CMExam 全科重分割 | 4608 / 991 / 991 |
| 中文牙科 | DeepSeek-V4-flash | Qwen3-32B | CMExam「口腔医学」学科 | 580 / 125 / 125 |
| 英文全科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | MedQA + MMLU（无印度 MedMCQA） | 待切 / 待切 / 4110 |
| 英文牙科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | 英文全科里筛出的牙科子集 + 3 本教材 | 待切 / 待切 / 待定 |

> 训练参数（四场景统一）：Choice-Head 蒸馏，α=0（纯标准答案监督）；LoRA rank16/alpha32；lr 1e-4；batch 1 × 梯度累积 8；1 epoch。唯一差异：Llama-3.3-70B 用 QLoRA 4bit。

---

## 2. 目录结构

```
dentaldistill/
├── README.md                 # 总览 + 快速开始
├── PLAN.md                   # 本文件
├── HANDOVER.md               # 交接文档（给 AI 审计用）
├── requirements.txt
├── setup.env.example
├── .gitignore
├── shared/                   # 自 mentalDistill/shared 移植的训练/评估脚本
│   └── train_choice_head_distill.py
├── data/                     # 数据 + 数据管线 + 审计工具
│   ├── README.md             # 数据来源/条数/查询方法/判断依据
│   ├── dental_filter.py      # 牙科判定（修复 oral 误判）
│   ├── check_dental_subset.py# 检查工具（证明子集无非牙科数据）
│   ├── prepare_cn_general.py # 中文全科
│   ├── prepare_cn_dental.py  # 中文牙科
│   ├── prepare_en_general.py # 英文全科
│   ├── prepare_en_dental.py  # 英文牙科（含书籍）
│   └── split_train_val_test.py # 通用 train/val/test 划分
├── books/                    # 3 本教材 PDF + 提取脚本
├── experiments/
│   ├── cn_general/           # 中文全科
│   ├── cn_dental/            # 中文牙科
│   ├── en_general/           # 英文全科
│   └── en_dental/            # 英文牙科
└── ablation/                 # 消融实验（默认参数是否最优）
```

---

## 3. 牙科判定（本方案核心，修复 `\boral\b` 误判）

**背景 bug**：mentalDistill 旧正则含 `\boral\b`，把"oral = 口服/oral administration"的题（如洋地黄中毒题选项 "oral activated charcoal"）误判成牙科。实测英文牙科 501 题里 295 题只命中 "oral"，多数非牙科。

**拆分方法（新）**：
- 中文：直接用 CMExam 的「口腔医学」学科字段（`Medical Discipline == "口腔医学"`），**不靠关键词**，100% 可靠。
- 英文：
  - MedMCQA：用 `subject == "Dental"` 学科字段（干净）。
  - MedQA / MMLU：无牙科学科字段，用**收紧后的关键词**判定。

**判定规则（可审计，每条命中都要给出"命中了哪个词/哪条规则"）**：
- R1 强牙科关键词（单独命中即可判牙科）：tooth, teeth, dental, dentine, dentin, enamel, pulp, molar, premolar, incisor, canine, gingiv*, periodont*, mandib*, maxill*, caries, occlus*, denture, endodont*, orthodont*, amalgam, prosthodont*, cementum, odonto*, root canal, fluoride, saliva, buccal, lingual, periapical, dentition, bruxism, malocclusion, alveolar, palat*
- R2 "oral" 必须出现在明确口腔语境才判牙科：oral cavity / oral mucosa / oral health / oral hygiene / oral thrush / oral candid* / oral cancer / oral carcinoma / oral squamous / oral lesion / oral ulcer / oral surgery / oral surgeon / oral examination / oral manifestation / oral infection / oral tissue / oral disease / oral trauma / oral rehabilitation / oral prosthesis / oral implant / oral microbiome / oral flora / oral antiseptic / oral rinse / oral vestibule / oral floor / oral tongue
- **裸 "oral"（口服/oral medication/oral contraceptive/oral rehydration 等）不判牙科**；"mucosa"/"crown" 不再作为独立关键词（牙科语境下它们必然伴随 R1/R2 命中）。

**检查工具**（`data/check_dental_subset.py`）：对任意牙科子集逐题跑判定，输出每题的命中关键词/规则；若发现非牙科题则**显式列出 + 给出理由**，做到"人工可复核、AI 可审计"。

---

## 4. train/val/test 划分

- 中文全科/牙科：沿用 mentalDistill 15/22 已有划分（train/val/test 已分离、零重叠）。
- 英文全科：固定 test 4110（MedQA 1273 + MMLU 2837），从 train 10168 中按 `seed=42` 分层切出 val（约 10%），train 其余。
- 英文牙科：从英文全科筛牙科后，同样 train/val/test 三分；书籍题并入时保证与现有题去重、与 test 零重叠。

---

## 5. 三本教材并入（fullEnglish/book/）

| 书 | 类型 | 提取脚本（旧，english/00_data/） | 提取量（旧统计） |
|---|---|---|---|
| Best of Fives for Dentistry | 单选 A–E | extract_bestoffives.py | 272 |
| Mosby's NBDE Part Two | 单选 A–E | extract_nbde.py | 364 |
| MCQs for Dentistry | true/false 多选 | extract_mcqs.py | 378 |

计划：把 PDF 复制到 `books/`，移植提取脚本（修正 PDF 路径），用收紧后的牙科判定过滤后再并入英文牙科数据；明确标注来源 `BoF/NBDE/MCQ` 与条数。

---

## 6. 消融实验（ablation/）

探索默认参数是否最优，至少覆盖：
1. α ∈ {0, 0.15, 0.35}（KL 权重，验证 α=0 是否最优）；
2. rank ∈ {8, 16, 64}（LoRA 秩）；
3. lr ∈ {1e-4, 3e-4}；
4. 1 vs 3 epoch。

以中文全科（Qwen2.5-14B）或中文牙科（Qwen3-32B）为主场景跑消融，报告均值与 seed 稳定性。

---

## 7. 文档体系

- `README.md`：总览、快速开始、四场景入口。
- `data/README.md`：每个数据集的来源、条数、字段、查询方法、牙科判定依据。
- 每个 `experiments/<场景>/README.md`：该场景的数据/参数/复现命令/结果/如何核对。
- `HANDOVER.md`：面向 AI 审计的完整交接文档（结论 + 关键数字 + 文件位置 + 如何验证）。

---

## 8. 落地步骤与状态

- [x] 仓库骨架 + git remote（已存在，无提交）
- [ ] PLAN.md（本文件）
- [ ] 牙科判定 `dental_filter.py` + 检查工具 `check_dental_subset.py`
- [ ] 数据管线 prepare_*.py + split_train_val_test.py + data/README.md
- [ ] 移植 shared/train_choice_head_distill.py + 各场景 scripts
- [ ] 各 experiments README + HANDOVER.md
- [ ] 三本书并入 books/
- [ ] 消融实验脚本 + 文档
- [ ] git 首次提交
