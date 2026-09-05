# 牙科数据报告：中文牙科 & 英文牙科（过滤原则 / 来源 / 拆分 / 训练 / 打平参数）

> 本报告为 CPU 只读分析，未占用 GPU。数据截至 2026-09-04。
> 覆盖两个牙科场景：中文牙科（cn_dental）、英文牙科（en_dental）。

---

## 1. 过滤原则

### 1.1 英文牙科（data/en_dental/）

判定模块：`data/dental_filter.py`（v2，修复 v1 的词干误配 + 歧义词假阳性）。一条题（题干+选项拼接）判为「牙科」，当且仅当命中下列任一：

| 规则 | 内容 | 举例 |
|---|---|---|
| R1a | 精确牙科词（完整词边界，无歧义） | tooth, teeth, dental, enamel, caries, denture, amalgam, incisor, gingiva, periodontitis, mandible, maxilla, molar, canine…（约 55 词） |
| R1b | 词干（词首边界，匹配派生词） | gingiv, periodont, mandib, maxill, endodont, orthodont, prosthodont, odonto, palat |
| R1c | 歧义词的牙科限定短语 | "alveolar bone/ridge/socket/nerve"、"dental pulp"、"inferior alveolar nerve" |
| R2 | "oral" 口腔语境（明确口腔疾病/解剖） | oral cavity / oral health / oral thrush / oral cancer / oral surgery / oral implant…（约 26 短语） |

**明确排除（不判牙科）：**
- 裸 "oral"（口服 oral medication / oral contraceptive / oral rehydration 等）
- 裸 "mucosa" / "crown"
- "molar pregnancy" / "hydatidiform"（葡萄胎，molar 非牙科）
- 裸 "alveolar"（肺泡）、裸 "pulp"（脾髓）——须带牙科限定词（R1c）

> 背景：旧 mentalDistill 用 `\boral\b`，把「oral=口服」误判成牙科，旧 501 题里 311 道非牙科；本仓库收紧重做。

### 1.2 中文牙科（data/cn_dental_clean/）

两阶段：

**第一层（旧口径，已作废）**：学科字段 `Medical Discipline == "口腔医学"`。
→ 检测发现该字段是「口腔执业医师整卷分类」，含 **35%–42% 通科医学题**（药理/儿科/妇产/统计/伦理/传染病），不可靠。

**第二层（干净口径，当前使用）**：`data/prepare_cn_dental_clean.py` + `data/check_cn_dental_content.py`，逐题内容级判定，任一命中即保留：

| 规则 | 内容 |
|---|---|
| C1 | 中文强牙科关键词（约 200 词）：龋/牙髓/牙周/牙体/牙槽/牙龈/釉质/根管/牙菌斑/窝洞/根尖/牙齿/智齿/乳牙/磨牙/切牙/颌/颞下颌/口腔/腭/阿弗他/白斑/舌癌/咬合/义齿/正畸/拔牙/银汞/固定桥/烤瓷/全冠/嵌体/含氟/唾液腺/三叉神经/鳃裂/颌骨骨髓炎/牙胚/成釉器…（见 `check_cn_dental_content.py` 的 `CN_STRONG`） |
| C3 | 英文 R1/R2 关键词（复用 dental_filter，防英文题混入） |
| D3 | 临床科室 `Clinical Department == "口腔科"`（覆盖关键词表未收录专业术语的边界题） |

> 中文关键词刻意排除歧义词：裸「口」（口服）、「面/舌/唇」（中医舌诊）、「种植/修复/冠」（种植转移/冠心病）等，避免误报。

**审计（两份数据均 PASS，退出码 0）：**
- `python3 data/check_no_nondental.py` → 中文牙科 545 题 + 英文牙科 676 题全部为牙科，无非牙科。
- `python3 data/check_dental_subset.py <test.jsonl>` → 中文 84/84、英文 84/84 [PASS]。

---

## 2. 来源

### 2.1 英文牙科（train 566 / val 26 / test 84，共 676 题）

| 集合 | 条数 | source 分布 |
|---|---|---|
| train | 566 | MedQA 200 + MMLU 1 + **BoF 142 + NBDE 223**（2 本教材） |
| val | 26 | MedQA 25 + MMLU 1 |
| test | 84 | MedQA 36 + MMLU 48 |

- 上游：`data/en_general/`（MedQA + MMLU，无印度 MedMCQA），用收紧判定筛出牙科题；
  再并入 2 本教材牙科题（Best of Fives for Dentistry = BoF、Mosby's NBDE Part Two = NBDE），仅并入 train（去重、避开 test）。
- 第 3 本教材「MCQs for Dentistry」是 true/false 多选，与单候选任务格式不兼容，**未并入**。

### 2.2 中文牙科（train 381 / val 80 / test 84，共 545 题）

| 集合 | 条数 | 学科 |
|---|---|---|
| train | 381 | 口腔医学 |
| val | 80 | 口腔医学 |
| test | 84 | 口腔医学 |

- 上游：CMExam（学科字段「口腔医学」）→ 内容级关键词 + 临床科室=口腔科 重筛。
- 相比初版干净集（340/73/76）多回收 56 题真牙科（详见 `reports/cn_dental_rescreen_report.md`）。

---

## 3. 拆分比例

| 数据集 | train | val | test | 合计 | train/val/test 比例 |
|---|---|---|---|---|---|
| 中文牙科 cn_dental_clean | 381 | 80 | 84 | 545 | **69.9% / 14.7% / 15.4%** |
| 英文牙科 en_dental | 566 | 26 | 84 | 676 | **83.7% / 3.8% / 12.4%** |

- 中文牙科：划分继承自 CMExam 原 580/125/125 切分，经内容级过滤后变成 381/80/84。
- 英文牙科：test 固定（MedQA 36 + MMLU 48），val 从 MedQA 切出，仅 26 题（**明显偏小**，这也是后面细扫只能「在 test 上挑」的原因之一）。

---

## 4. 做了哪些训练

统一：Choice-Head 蒸馏，α=0（纯标准答案监督）；LoRA；batch 1×8；1 epoch；Llama-70B 用 QLoRA 4bit。

### 4.1 中文牙科（教师 DeepSeek-V4-flash 零样本 86.90%）

| # | 学生 | 配置 | 结果 |
|---|---|---|---|
| 1 | Qwen3-32B | rank16/lr1e-4 3-seed | 79.76%（大幅落后） |
| 2 | Qwen2.5-32B | rank16/lr1e-4 3-seed | 86.51% |
| 3 | Qwen2.5-32B | rank16/lr2e-4 3-seed | **86.90%** |
| 4 | Qwen2.5-32B | 细扫 24 组（rank{4,8,16}×lr{1e-4..5e-4}×e{1,2}） | test 封顶 88.1% |
| 5 | Qwen3-32B | α 消融（α{0,0.15,0.35}×rank{8,16,64}×lr{1e-4,3e-4}×e{1,3}） | α=0 最优 |

### 4.2 英文牙科（教师 Qwen3-32B 零样本 66.67%）

| # | 学生 | 配置 | 结果 |
|---|---|---|---|
| 1 | Qwen2.5-32B | 默认 rank16/lr1e-4 单 seed | 64.29% |
| 2 | Llama-70B | 默认 rank16/lr1e-4 3-seed | 67.86% |
| 3 | Qwen2.5-32B | 细扫 24 组（rank{4,8,16}×lr{1e-4..5e-4}×e{1,2}） | 最优单点 rank8/lr3e-4 = 70.24% |
| 4 | Qwen2.5-32B | 最优 rank8/lr3e-4 3-seed | 66.27% |
| 5 | Llama-70B | 细扫 12 组（rank{4,8,16}×lr{1e-4..5e-4}×e1） | 最优单点 = 默认 rank16/lr1e-4 = 69.05% |
| 6 | Llama-70B | 默认 rank16/lr1e-4 3-seed ×2（共 6 seed） | **67.06%** |

---

## 5. 哪个训练参数下学生「最多和老师打平」

### 5.1 中文牙科（教师 86.90%，73/84）

**最接近/完全打平：Qwen2.5-32B，rank16 / lr2e-4 / 1ep / α0，3-seed**

| seed | test |
|---|---|
| 11 | 88.10% (74/84) |
| 42 | 88.10% (74/84) |
| 8  | 84.52% (71/84) |
| **均值** | **86.90% (73/84)** |

→ 均值与教师 **完全相等（Δ=0.00pp）**，这是「最多打平」的配置。

- 次优：rank16/lr1e-4 3-seed = 86.51%（Δ=−0.39）。
- 细扫单点能到 88.1%（+1.2pp），但那是单 seed 噪声，3-seed 均值回落 86.90%。
- 结论：**中文牙科天花板就是 86.90%（=教师），调参换不出稳定超越。**

### 5.2 英文牙科（教师 66.67%，56/84）

**最接近：Llama-70B，rank16 / lr1e-4（默认）/ 1ep / α0，6-seed（两轮 3-seed）**

| 轮次 | seed 11 | seed 42 | seed 8 | 均值 |
|---|---|---|---|---|
| 第 1 轮 | 69.05% | 67.86% | 66.67% | 67.86% |
| 第 2 轮 | 67.86% | 64.29% | 66.67% | 66.27% |
| **合并** | — | — | — | **67.06%（338/504）** |

→ 均值 **67.06% vs 教师 66.67%（Δ=+0.40pp，≈1 题，噪声内打平）**。

- Qwen2.5-32B 次优：rank8/lr3e-4 3-seed = 66.27%（Δ=−0.40，同样打平）。
- 细扫单点 rank8/lr3e-4 = 70.24%（+3.57）**不可复现**（3-seed 回落 66.27%）。
- 结论：**英文牙科两个学生都只能打平教师，无稳定超越。**

---

## 6. 一句话总结

| 场景 | 教师 | 最优打平配置 | 学生均值 | Δ |
|---|---|---|---|---|
| 中文牙科 | 86.90% | Qwen2.5-32B rank16/lr2e-4（3-seed） | 86.90% | **0.00 完全打平** |
| 英文牙科 | 66.67% | Llama-70B rank16/lr1e-4（6-seed） | 67.06% | +0.40 噪声内打平 |

**牙科两个场景的「学生超越教师」都不成立，最多做到「打平」；真正稳定超越只出现在全科场景（中文全科 +1.79、英文全科 +1.17~1.87）。**

---

## 7. 关键文件索引

- 过滤规则：`data/dental_filter.py`（英文）、`data/check_cn_dental_content.py`（中文内容级）
- 数据准备：`data/prepare_en_dental.py`、`data/prepare_cn_dental_clean.py`
- 审计：`data/check_dental_subset.py`、`data/check_no_nondental.py`
- 数据说明：`data/README.md`
- 结果：`experiments/cn_dental/RESULTS_qwen25_best_3seed.md`、`experiments/en_dental/RESULTS_llama_3seed.md`、`ablation/RESULTS_sweep_en_dental_*.md`、`ablation/RESULTS_sweep_qwen25.md`
- 夜间坐实过程：`OVERNIGHT_REPORT_2026-09-03.md`
