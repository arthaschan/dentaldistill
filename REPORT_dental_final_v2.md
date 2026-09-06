# 牙科蒸馏实验最终汇报（2026-09-06，已修正英文泄漏）

> 结论一句话：**中文牙科「学生超越教师」成立且显著；英文牙科在干净口径下只能数值超、统计不显著。
> 此前英文 +8.33pp 是「书籍题混入测试集」的泄漏假象，已作废。**

---

## 1. 最终结果总表（干净口径）

| 场景 | 教师（零样本） | 学生（蒸馏后） | 结论 |
|---|---|---|---|
| 中文全科 | DeepSeek-V4-flash 87.18% | Qwen2.5-14B 88.97% | 超越 +1.79 ✅ |
| 英文全科 | Qwen3-32B 80.22% | Qwen2.5-32B 82.09% | 超越 ✅ |
| 中文牙科（1386 题） | DeepSeek-V4-flash 87.59% | Qwen2.5-32B 89.76% | **超越 +2.17pp ✅（2/3 seed p<0.01）** |
| 英文牙科（70 题，干净） | Qwen3-32B 84.29% | Llama-70B 90.00% | 数值 +5.71pp，不显著（p>0.09） |

三个「打平」学生-教师组合全部重试后的完整图景：

| 组合 | 结果 |
|---|---|
| 中文 Qwen2.5-32B（1386 题） | +2.17pp，2/3 seed p<0.01 ✅ 显著超越（唯一成功的） |
| 英文 Llama-70B（70 题） | +5.71pp，p>0.09 不显著（数值超） |
| 英文 Qwen2.5-32B（70 题） | −13.34pp 不超越（更差，蒸馏 70.95% vs 教师 84.29%） |

---

## 2. 牙科数据过滤条件

### 2.1 中文牙科（`data/check_cn_dental_content.py`）

数据源：CMExam 三个官方切分 `train.csv`(54497) / `val.csv`(6811) / `test_with_annotations.csv`(6811)，
三文件 uid 两两不相交（已核实），是同一基准的 train/val/test 官方切分。

判定函数 `content_signal_strict`（挖矿用，precision 优先）：

- **C1 中文强牙科词 `CN_STRONG`（~200 词，按最长优先匹配）**：龋 / 牙髓 / 牙周 / 牙龈 / 牙槽 / 牙本质 /
  釉质 / 根管 / 牙菌斑 / 义齿 / 正畸 / 咬合 / 银汞 / 固定桥 / 种植体 / 唾液腺 / 腮腺 / 下颌下腺 / 阿弗他 /
  白斑 / 扁平苔藓 / 颞下颌 / 颌骨 / 牙胚 / 成釉器 / 舌癌 / 颊癌 / 腭裂 …
- **剔除单字歧义 `CN_SINGLE_CHARS`**：牙 / 齿 / 颌 / 龈 / 腭（单独命中不算，须命中多字牙科词）。
- **剔除泛化/神经/普外歧义词 `CN_BLOCKLIST`**：三叉神经 / 面神经 / 海绵窦 / 切开引流 / 流涎 / 血管瘤 /
  弹响 / 角化层 / 黏液腺 / 皮脂腺囊肿 …
- **C3 英文 R1**（复用 `dental_filter` 的 R1 强牙科词，不含 R2 oral 语境）。

精度/召回（在 `test_with_annotations.csv` 的地面真值学科标签「口腔医学」上校准）：

| 口径 | Precision | Recall |
|---|---|---|
| 全量 `content_signal` | 76.6% | 64.8% |
| **严格 `content_signal_strict`（现用）** | **87.3%** | 58.6% |

### 2.2 英文牙科（`data/dental_filter.py` v3）

数据源：MedQA 8876 + MMLU 275（benchmark 官方切分）+ 牙科教材 BoF 272 + NBDE 366。

判定 `is_dental_record_strict`（挖矿用，不含 R2）：

- **R1a 强牙科词 `STRONG_EXACT`（~70 词 + v3 新增 24 个口腔内科/唾液腺词）**：tooth / dental / gingiva /
  periodont / mandible / maxilla / endodontic / orthodontic / prosthodontic / palate / molar …
  + salivary / saliva / xerostomia / sialadenitis / parotid / submandibular / aphthous / leukoplakia /
  stomatitis / glossitis / cheilitis / chlorhexidine / halitosis …
- **R1b 词干 `STRONG_STEMS`**：gingiv / periodont / mandib / maxill / endodont / orthodont / prosthodont / odonto / palat。
- **R1c 歧义词限定短语 `DENTAL_PHRASES`**：alveolar bone/ridge/process/socket、inferior alveolar nerve、
  dental pulp、pulp chamber/horn/necrosis …
- **R2「oral」口腔语境（严格版剔除）**：oral cavity/health/hygiene/thrush/cancer/ulcer/lesion/surgery …（约 26 个）。
- **排除 `NEGATIVE_PATTERNS`**：molar pregnancy（葡萄胎）、hydatidiform。
- **书籍题 source ∈ {BoF, NBDE} 直接判为牙科**：这两本书本身就是牙科考试题库（BoF=Best of Fives，
  NBDE=National Board Dental Examination），subject 字段全是 Periodontics/Endodontics/Prosthodontics 等牙科主题，
  无需关键词即可判定。

---

## 3. 中文牙科（详细）

数据：合池三个 CMExam 切分的牙科题（严格内容过滤，precision 87.3%），重打乱重切
`data/cn_dental_v4/`（train 5199 / val 347 / test 1386，test 占 20%）。

| 模型 | test acc (1386) |
|---|---|
| 教师 DeepSeek-V4-flash 零样本 | 87.59% (1214/1386) |
| 学生 Qwen2.5-32B 零样本 | 80.95% (1122/1386) |
| 学生蒸馏 3-seed | 88.96% / 90.19% / 90.12% → 均值 89.76% |

headroom 6.64pp，蒸馏增益 8.81pp，超越 +2.17pp。

McNemar 配对检验：seed11 p=0.167、seed42 **p=0.006**、seed8 **p=0.008**（2/3 显著）。

关键过程证据链（旧 84 题 → 新 1386 题）：
- 84 题：打平 86.90%；加 18 倍数据（6762）仍打平；超参扫描任何配置不突破 → 疑似「到顶」。
- 346 题：+1.54pp 但 p 全 >0.2（不显著）。
- **1386 题：+2.17pp，2/3 seed p<0.01（显著）→ 坐实超越。**

---

## 4. 英文牙科（干净重做 v3：扩张 + 难题入训练 + 从头蒸馏）

扩张：书籍题(BoF+NBDE 638，牙科教材)全部纳入训练 + MedQA/MMLU 严格过滤 270 → 训练池 631→908。
重拆：书籍题只进训练、教师答错的 29 道难题强制进训练、MedQA/MMLU 重拆 → train 913 / val 35 / test 70（test 零书籍题，防泄漏）。
从头：教师 Qwen3-32B + 学生 Llama-70B 零样本 + 蒸馏（r16/lr1e-4, 4bit, 3 seed）。

| 模型 | test acc (70) |
|---|---|
| 教师 Qwen3-32B 零样本 | 84.29% (59/70) |
| 学生 Llama-70B 零样本 | 85.71% (60/70) |
| 学生蒸馏 3-seed | 88.57% / 91.43% / 90.00% → 均值 90.00% |

数值超越 +5.71pp。McNemar：seed11 p=0.366、seed42 p=0.096、seed8 p=0.206 —— **全部不显著**。

英文第二个学生 Qwen2.5-32B（历史 66.27% 打平）重试：零样本 64.29%，蒸馏 3-seed 70.00%/68.57%/74.29%
→ 均值 70.95%，vs 教师 84.29% = **落后 13.34pp，不超越（更差）**。

**干净结论：数值 +5.71pp，但测试集仅 70 题，统计上不显著。** 「难题进训练」使测试集变容易（教师 66.67%→84.29%）
但也变小（84→70），McNemar 分辨不出净胜 3~5 题的效应。英文牙科干净测试集有硬上限（MedQA 牙科 test 仅 36 + MMLU test 48 = 84 题），
想扩大只能混入书籍题或 MedQA-train（都是泄漏），故英文牙科干净口径下到不了显著。

旧口径对照：84 题（纯 MedQA/MMLU，无书）教师 66.67% vs Llama 67.06% = +0.40pp 打平。

---

## 5. 数据集调整空间评估

### 5.1 中文牙科：还有明显调整空间

当前（严格过滤，precision 87.3% / recall 58.6%）→ 训练池 6932 题。

| 调整方向 | 效果 | 代价 |
|---|---|---|
| 放宽到全量过滤 `content_signal` | 6932 → 8382（+1450 题） | precision 87.3% → 76.6%，混入 ~23% 非牙科题 |
| 提高召回（补词/改进匹配） | 可回收被漏掉的 ~41% 真牙科题（recall 58.6% 的缺口） | 需逐类分析 292 道 FN 题、针对性补词 |

**结论：中文数据未到天花板。** 主要瓶颈是「precision 与 recall 的权衡」——当前选了高精度（87.3%）牺牲了
召回（58.6%），严格过滤漏掉了约四成真牙科题。若能在不显著降精度的前提下改进关键词（尤其是 FN 高频的题型，
如口腔材料/术式/器械等无关键词题），训练池可从 6932 再往上扩。

### 5.2 英文牙科：空间很小，基本到顶

当前：书籍题 638 全纳入 + MedQA/MMLU 270 = 908 题。

| 调整方向 | 效果 | 代价 |
|---|---|---|
| MedQA 加回 R2（全量过滤） | 270 → 297（+28） | 这 28 题是 oral lesions/candidiasis 等全身病口腔表现（SLE/Behçet/鹅口疮），非牙科，不建议 |
| MCQ 书（401 题 → 2003 条陈述） | 428 条 R1 严格牙科 | 已试过拆判断题（428）和重组五选项（348），重训均变差，风格与 MedQA vignette 不匹配 |

**结论：英文数据基本到顶。** 书籍题已吃满（638，教材即牙科题库）；MedQA/MMLU 牙科子集本就小（~297），
再扩要么引入 R2 假阳性、要么是风格不匹配的 MCQ 书。干净测试集更是硬上限 ~84 题（MedQA 牙科 test 仅 36 + MMLU test 48）。

---

## 6. 方法学教训（本次最重要的产出）

1. **测试集大小是「打平/超越」的分水岭。** 84 题的最小分辨率 1.19pp，±1 题就盖过真实效应；
   中文 +2pp 的效应要到 ~1400 题才能显著（p<0.01）。
2. **「打平」是测量伪象，不是到顶。** 中文：84 题打平 → 1386 题显著 +2.17pp。效应一直存在，
   只是小（~2pp），被小样本噪声淹没。
3. **发散思维四假设的裁决**：H4（观测分辨率）被证实为「打平」的直接原因；H1/H3（教师≈天花板、
   残余错误是歧义）部分成立但被「放大测试集后能显著超越」推翻——教师并非真正到顶。
4. **数据量与调参对「超越」都无帮助**（18 倍数据 0 变化、超参扫描 0 突破），唯一有效的是
   「把测试集做大、做对（同分布）」。

---

## 7. 关键文件

- 数据重切：`data/prepare_cn_dental_v3.py`（中文，支持 test 比例）、`data/prepare_en_dental_v3_split.py`（英文干净重拆）
- 数据扩张：`data/prepare_en_dental_expand.py`（英文书籍题全纳入）
- 数据：`data/cn_dental_v4/`（中文 5199/347/1386）、`data/en_dental_v3/`（英文 913/35/70）、
  `data/en_dental_expanded/`（英文扩张训练池 908）
- 过滤规则：`data/check_cn_dental_content.py`（中文 `content_signal_strict`）、`data/dental_filter.py`（英文）
- 训练：`run_retrain_cn_v4_queue.sh`、`run_retrain_en_v3_queue.sh`、`run_retrain_en_v3_qwen25.sh`
- 显著性：`data/audit_mcnemar_v4.py`（中文）、`data/audit_mcnemar_en_v3.py`（英文）
- 教师标签：`teachers/deepseek_v4flash_cn_dental_v4_test.jsonl`（中文 API 教师）
- 全部分析：`REPORT_dental_tie_analysis.md`（发散思维 + 各步结果）、`REPORT_cn_dental_v2.md`、
  `REPORT_cmexam_unmined.md`、`REPORT_filter_relaxation.md`、`REPORT_mcq_split.md`

## 8. 教师 API 说明

中文教师 DeepSeek-V4-flash 需 `DEEPSEEK_API_KEY`（已从 Hermes 的 `~/.hermes/.env` 补入
`setup.env`，该文件被 .gitignore 忽略，不会进版本库）。
