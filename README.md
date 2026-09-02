# dentaldistill — 牙科/医学选择题"学生超越教师"蒸馏实验（可审计复现版）

把 `mentalDistill` 里"学生超越教师"的 4 个场景，重建成干净、可审计、可复现的仓库。
核心承诺：**每个实验明确「数据来源 / 数据条数 / 实验参数」，并能回答"这些数字在代码的哪里、怎么查"，供人工与 AI 逐项核对。**

---

## 四场景总览

| 场景 | 老师 | 学生 | 数据来源 | train/val/test |
|---|---|---|---|---|
| 中文全科 | DeepSeek-V4-flash | Qwen2.5-14B | CMExam 全科重分割 | 4608 / 991 / 991 |
| 中文牙科 | DeepSeek-V4-flash | Qwen2.5-32B | CMExam「口腔医学」学科 → 干净集 | 381 / 80 / 84 |
| 英文全科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | MedQA + MMLU（无印度）+ 2 本书 | 9789 / 1017 / 4110 |
| 英文牙科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | MedQA+MMLU 牙科 + 2 本书（R1 严格） | 566 / 26 / 84 |

> 训练参数（四场景统一）：Choice-Head 蒸馏，α=0（纯标准答案监督）；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch。唯一差异：Llama-3.3-70B 用 QLoRA 4bit。

---

## 当前结果（2026-09-02）

| 场景 | 教师(零样本) | 学生 | 结论 |
|---|---|---|---|
| 中文牙科(84 干净) | DeepSeek-V4-flash 86.90% | Qwen2.5-32B 86.90%（3seed） | **打平**（Qwen3-32B 仅 79.76%） |
| 英文全科(4110) | Qwen3-32B 80.22% | Qwen2.5-32B 82.09% / Llama-70B 81.39% | **双超越** ✅ |
| 英文牙科(84 严格) | Qwen3-32B 66.67% | Llama-70B 67.86%（3seed） / Qwen2.5-32B 64.29% | 仅 Llama 微弱超 ⚠️ |

> 完整结果与复现见 `TASK_STATUS.md` 与各 `experiments/*/RESULTS_*.md`。
> 牙科数据「无非牙科」已核实：`python3 data/check_no_nondental.py`（退出码 0），见 `reports/data_check_report.md`。

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

---

## 另一个重要背景：中文牙科学科字段「口腔医学」也不可靠（2026-09-01 检测发现）

中文牙科按 `Medical Discipline == "口腔医学"` 拆分，但该字段是口腔执业医师的**整卷分类**，
含大量通科医学题（药理学/儿科学/妇产科学/统计学/卫生法规/医学伦理/传染病学等）。内容级检测
（`data/check_cn_dental_content.py`）发现 **约 35%–42% 是非牙科**。已产出干净子集
`data/cn_dental_clean/`（train 381 / val 80 / test 84，扩充关键词 + 临床科室=口腔科信号重筛），
训练/消融改用此集。详见 `reports/cn_dental_rescreen_report.md` 与 `reports/data_check_report.md`。

---

## 三本书（books/）题目情况与安排

3 本牙科教材：Best of Fives（单选 272）、NBDE（单选 366）、MCQs for Dentistry（**true/false
多选 401**）。单选并入英文牙科 train（净 +278）；**多选与单候选任务格式不兼容（训练给错监督、
评估不可评分），不并入**。详见 `books/BOOKS_ARRANGEMENT.md`。
