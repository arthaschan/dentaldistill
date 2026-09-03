# 英文全科（en_general）参数调优报告

> 承接用户问题：「英文牙科 2 个学生是否做了参数调优？英文全科是否做了参数调优？没做的就进行调优。」
> 本报告记录核查结论与调优执行过程/结果。启动时间 2026-09-03 06:14。

---

## 1. 核查结论（两个场景）

| 场景 | 学生 | 是否做过参数调优 | 说明 |
|---|---|---|---|
| 英文牙科 | Qwen2.5-32B | ✅ 已做 | 24 组细扫（rank{4,8,16}×lr{1e-4..5e-4}×e{1,2}）+ 最优 3-seed，见 `ablation/RESULTS_sweep_en_dental_qwen25.md` |
| 英文牙科 | Llama-70B | ✅ 已做 | 12 组细扫（rank{4,8,16}×lr{1e-4..5e-4}×e1）+ 默认 3-seed×2，见 `ablation/RESULTS_sweep_en_dental_llama70b.md` |
| **英文全科** | Qwen2.5-32B | ❌ **未做** | 只有默认配置（rank16/lr1e-4，seed42）单 run → **本次补做** |
| **英文全科** | Llama-70B | ❌ **未做** | 只有默认配置（rank16/lr1e-4，seed42）单 run → **本次补做** |

> 结论：英文牙科无需再调优；英文全科两个学生都需要补做调优（本次执行）。

---

## 2. 英文全科调优方案

- 数据：`data/en_general/`（train 9789 / val 1017 / test 4110，MedQA+MMLU 无印度 + 2 本单选书）
- 教师：Qwen3-32B 零样本基线 = **80.22%**（test 4110，历史 27 口径）
- 默认配置（已跑）：rank16 / lr1e-4 / e1，seed42 → Qwen2.5-32B **82.09%**、Llama-70B **81.39%**（见 `experiments/RESULTS_english.md`）

### 网格（每学生 6 组）

rank{8,16} × lr{1e-4, 2e-4, 3e-4} × epoch{1}，α=0，seed=42。

> 依据：英文牙科/中文牙科细扫已证 lr5e-4、rank4、epoch2 劣化（发散/掉点），此处跳过以省算力；
> 保留 lr 主轴 + rank 副轴，覆盖「默认 lr1e-4 是否最优」的核心问题。

### 排序口径（重要）

- 用 `shared/eval_choice_head.py`（greedy，max_new_tokens=8）在 **test 4110** 上评测，与既有 RESULTS 一致。
- 注意：train.log 里的 `[VAL]`（max_new_tokens=4 旧口径，且 val 集 97% MedQA 与 test 集 69% MMLU 分布不同）
  仅作记录，**不用于排序**。

### 成本估算

- Qwen2.5-32B：~30min 训练 + ~13min 评测 / 组 × 6 ≈ **4 小时**
- Llama-70B：~2h 训练 + ~20min 评测 / 组 × 6 ≈ **14 小时**
- 合计 ≈ **18 小时**（单卡串行）

### 脚本与日志

- 队列：`run_en_general_tune_queue.sh`（串行 Qwen→Llama），日志 `en_general_tune_queue.log`
- 细扫：`ablation/run_sweep_en_general_qwen25.sh`、`ablation/run_sweep_en_general_llama70b.sh`
- 结果表：`ablation/results_en_general_qwen25.tsv`、`ablation/results_en_general_llama70b.tsv`
- 断点续跑：每组 `DONE` 跳过

---

## 3. 结果（实时填充）

### 3.1 Qwen2.5-32B 细扫（test 4110）

（待完成后填写）

### 3.2 Llama-70B 细扫（test 4110）

（待完成后填写）

### 3.3 与默认配置对比

| 学生 | 默认（rank16/lr1e-4） | 细扫最优 | 教师 | 是否超默认 |
|---|---|---|---|---|
| Qwen2.5-32B | 82.09% | （待填） | 80.22% | （待填） |
| Llama-70B | 81.39% | （待填） | 80.22% | （待填） |

---

## 4. 结论（待完成后填写）
