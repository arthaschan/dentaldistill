# 数据说明（来源 / 条数 / 查询方法 / 牙科判定依据）

> 本文件回答：每个实验的**数据从哪来、有多少条、在哪一步生成、怎么核对**。
> 所有数据由 `data/prepare_*.py` 从 `mentalDistill` 的原始数据派生，可复现；中间 jsonl 被 `.gitignore` 忽略（版权/可重建），以脚本为准。

---

## 1. 四场景数据总览

| 场景 | 目录 | 来源 | train | val | test | 老师 | 学生 |
|---|---|---|---|---|---|---|---|
| 中文全科 | `experiments/cn_general` | CMExam 全科重分割 | 4608 | 991 | 991 | DeepSeek-V4-flash | Qwen2.5-14B |
| 中文牙科 | `experiments/cn_dental` | CMExam「口腔医学」学科 | 580 | 125 | 125 | DeepSeek-V4-flash | Qwen3-32B |
| 英文全科 | `experiments/en_general` | MedQA + MMLU（无印度）+ 2 本书 | 9789 | 1017 | 4110 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B |
| 英文牙科 | `experiments/en_dental` | MedQA+MMLU 牙科 + 2 本书 | 603 | 30 | 93 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B |

> 训练参数（四场景统一）：Choice-Head 蒸馏，α=0；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch；Llama-70B 用 QLoRA 4bit。

---

## 2. 数据来源与条数（可核对）

### 2.1 中文全科（CMExam 全科）
- 上游原始文件：`mentalDistill/15_fulldata_resplit/data/{train,val,test}.jsonl`
- 条数：train 4608 / val 991 / test 991（`prepare_cn_general.py` 直接拷贝，不改划分）
- 字段：`Question, Options, Answer, Explanation, Medical Discipline, ...`
- 查询命令：
  ```bash
  wc -l data/cn_general/{train,val,test}.jsonl          # 条数
  # 学科分布
  python3 -c "import json;from collections import Counter;c=Counter(json.loads(l).get('Medical Discipline') for l in open('data/cn_general/train.jsonl'));print(c)"
  ```

### 2.2 中文牙科（CMExam「口腔医学」学科）
- 上游：同 2.1 的 CMExam 全科，按 `Medical Discipline == "口腔医学"` 拆出牙科。
- 条数：train 580 / val 125 / test 125（= mentalDistill 22 的 580 + val_dental 125 + test_dental 125，总量 830）
- **⚠️ 拆分方法修正（2026-09-01 检测发现）**：学科字段 `口腔医学` **不可靠**——它是口腔执业医师
  整卷分类，含大量通科医学题（药理/儿科/妇产/统计/伦理/传染病等）。内容级检测发现约 **35%–42%**
  是非牙科。详见 `reports/cn_dental_content_report.md` 与 `data/check_cn_dental_content.py`。
- **干净子集**：`data/prepare_cn_dental_clean.py` 用「内容级牙科关键词（扩充后）+ 临床科室=口腔科」重筛，
  产出 `data/cn_dental_clean/`（train 381 / val 80 / test 84），训练/消融改用此集。
  相比初版干净集（340/73/76）多回收 56 题真牙科，详见 `reports/cn_dental_rescreen_report.md`。
- 查询：
  ```bash
  python3 data/check_dental_subset.py data/cn_dental/test.jsonl   # 旧工具：应 [PASS]（但只查学科字段，见下）
  python3 data/check_cn_dental_content.py data/cn_dental          # 内容级检测（发现污染）
  ```

### 2.3 英文全科（MedQA + MMLU，无印度 MedMCQA）
- 上游：`mentalDistill/27_english_general_noindia/data/train_no_india_dentalsplit.jsonl`（10168 题，= MedQA 9862 + MMLU 306）与 `test_no_india.jsonl`（4110 题，= MedQA 1273 + MMLU 2837）
- **为什么无印度**：沿袭 mentalDistill 27/28 口径（印度 MedMCQA 是最难子集，已做无印度消融）。
- 划分：test 固定 4110；train 10168 由 `split_train_val_test.py` 按 `source` 分层切出 val（默认 10%）。
- 查询：
  ```bash
  wc -l data/en_general/{train,val,test}.jsonl
  python3 -c "import json;from collections import Counter;print(Counter(json.loads(l).get('source') for l in open('data/en_general/test.jsonl')))"
  ```

### 2.4 英文牙科（MedQA+MMLU 牙科 + 3 本书）
- 上游：从 2.3 的英文全科中，用**收紧后的牙科判定**（`dental_filter.py`）筛出牙科；再并入 3 本教材的牙科题（`books/`）。
- **拆分方法（英文牙科）**：R1 强关键词 + R2 "oral" 口腔语境；裸 "oral"（口服）明确排除——详见 `dental_filter.py` 顶部 docstring。
- **检查工具**：`python3 data/check_dental_subset.py data/en_dental/test.jsonl`，输出每题的命中明细；非牙科题会被显式列出并给出理由。
- 3 本书：Best of Fives for Dentistry（BoF，单选）、Mosby's NBDE Part Two（NBDE，单选）、MCQs for Dentistry（MCQ，true/false 多选），来源标注在 `source` 字段。

---

## 3. 如何核对"核心数字在代码哪里"

| 要核对的数字 | 在哪个文件 | 哪一步 |
|---|---|---|
| 中文条数 4608/991/991、580/125/125 | `data/prepare_cn_general.py`、`prepare_cn_dental.py` | 脚本打印 + 输出 jsonl 行数 |
| 英文条数 10168/4110 | `data/prepare_en_general.py` | 从 27 拷贝 + 打印 |
| train/val/test 划分比例 | `data/split_train_val_test.py` | `--val`/`--test`/`--seed` |
| 牙科判定规则 | `data/dental_filter.py` | `is_dental()` / `dental_match()` |
| 子集无非牙科数据 | `data/check_dental_subset.py` | 逐题判定 + 命中明细报告 |
| 训练超参 rank16/alpha32/lr1e-4/batch1×8/1ep/α0 | `experiments/<场景>/scripts/run_train.sh` | 命令行 `--rank ... --alpha 0.0 ...` |

---

## 4. 牙科判定依据（一句话）

> 中文牙科**不能只靠**学科字段「口腔医学」（2026-09-01 检测发现其含 35%–42% 通科医学题），
> 需用 `data/check_cn_dental_content.py` 的**内容级中文关键词**（龋/牙髓/牙周/颌/牙龈/釉质/根管/
> 口腔/义齿/正畸/咬合/银汞/固定桥/阿弗他/白斑/舌癌…）重筛 → `cn_dental_clean`。
> 英文牙科用 R1 强关键词（tooth/dental/caries/enamel/…）+ R2 "oral" 的明确口腔语境，
> **裸 "oral"（口服）与裸 "mucosa"/"crown" 一律不算牙科**。判定与命中明细由
> `dental_filter.py`（英文）+ `check_cn_dental_content.py`（中文内容级）给出。
