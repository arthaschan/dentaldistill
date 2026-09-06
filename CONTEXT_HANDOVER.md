# 会话上下文 / 交接文档（2026-09-05）

> 用途：让一个新的会话（或人）读完本文件即可接续本项目。记录了项目全貌、数据文件、过滤规则、
> 所有实验结果、当前运行中的任务、待办与下一步。

---

## 0. 项目一句话

`dentaldistill`：把 mentalDistill 里「学生超越教师」的 4 个蒸馏场景（中文全科/中文牙科/英文全科/英文牙科）
重建成干净、可审计、可复现的仓库。**核心结论（2026-09-06 定稿，含英文干净重做）：中文全科/英文全科/中文牙科
三场景学生显著超越教师；英文牙科干净重做后数值 +5.71pp 但统计不显著（干净测试集仅 70 题，硬上限所致）。**
详见 `REPORT_dental_final_v2.md`、`REPORT_dental_tie_analysis.md`。

---

## 1. 四场景最终结果（干净口径）

| 场景 | 教师(零样本) | 学生(蒸馏后) | 结论 |
|---|---|---|---|
| 中文全科 | DeepSeek-V4-flash 87.18% | Qwen2.5-14B 88.97% | 超越 +1.79 ✅ |
| 英文全科 | Qwen3-32B 80.22% | Qwen2.5-32B 82.09% / Llama-70B 81.39% | 超越 ✅ |
| 中文牙科(1386题) | DeepSeek-V4-flash 87.59% | Qwen2.5-32B 89.76% | **超越 +2.17pp ✅（2/3 seed p<0.01）** |
| 英文牙科(70题干净) | Qwen3-32B 84.29% | Llama-70B 90.00% | 数值 +5.71pp，不显著（p>0.09） |

机制：学生超越教师 ⇔ 蒸馏增益 gain > 教师零样本领先幅度 headroom。中文牙科效应真实但小（~2pp），
旧 84 题测试噪声把它淹没，放大测试集后显著。英文牙科无干净大测试集（MedQA 牙科 test 仅 36 题），
扩大会混入书籍题导致背题泄漏，故干净口径下只能打平。

---

## 2. 数据文件全景（data/ 下，均已落盘）

### 2.1 原始干净数据（训练/评测的基准）

| 文件 | 条数 | 组成 |
|---|---|---|
| `data/cn_dental_clean/train.jsonl` | 381 | CMExam 口腔医学 → 内容级重筛（纯牙科） |
| `data/cn_dental_clean/val.jsonl` | 80 | 同上 |
| `data/cn_dental_clean/test.jsonl` | 84 | 同上 |
| `data/en_dental/train.jsonl` | 566 | MedQA 200 + MMLU 1 + BoF 142 + NBDE 223（R1 严格牙科） |
| `data/en_dental/val.jsonl` | 26 | MedQA 25 + MMLU 1（纯 MedQA/MMLU，无书） |
| `data/en_dental/test.jsonl` | 84 | MedQA 36 + MMLU 48（纯 MedQA/MMLU，无书） |
| `data/en_general/{train,val,test}.jsonl` | 9789/1017/4110 | MedQA+MMLU 无印度 + BoF 272 + NBDE 366（全科） |

### 2.2 扩充/实验衍生文件（原始数据未被动，都写在新文件）

| 文件 | 条数 | 说明 |
|---|---|---|
| `data/cn_dental_clean/train_aug.jsonl` | 930 | 381 原 + 549 英译中（跨域互译，结果变差） |
| `data/en_dental/train_aug.jsonl` | 944 | 566 原 + 378 中译英（变差） |
| `data/en_dental/train_mcq.jsonl` | 1053 | 566 + 59 五选项 + 428 判断题（变差） |
| `data/en_dental/train_mcq5.jsonl` | 914 | 566 + 348 重组五选项（变差/降回教师） |
| `data/en_dental/train_v3.jsonl` | **631** | **放宽 R1 后重建：MedQA 269 + MMLU 1 + BoF 150 + NBDE 211（回收 81 题口腔内科）** |
| `data/cn_dental_clean/train_v2.jsonl` | **6762** | **挖矿 CMExam train/val 切分扩充：原 381 + 新挖 6381（严格过滤，precision 87.3%）** |
| `data/translate_en2zh_train.jsonl` | 549 | 英译中产物（Qwen2.5-32B 本地翻译） |
| `data/translate_zh2en_train.jsonl` | 378 | 中译英产物 |

### 2.3 书籍数据（books/）

- `books_singlebest.jsonl`：BoF 272 + NBDE 366 = 638（单候选池）
- `books_tf.jsonl`：MCQ 书 401 题（true/false 多选）
- `books_mcq_single.jsonl`：拆成 2003 道判断题
- `books_mcq_single_dental.jsonl`：428（R1 严格）
- `books_mcq_5option_dental.jsonl`：59（which-ONE 五选项）
- `books_mcq_recombined_5option.jsonl`：348（重组五选项，答案全对）
- 拆分脚本：`books/split_mcq_tf.py`、`books/recombine_mcq_5option.py`、`books/convert_mcq_to_single.py`

---

## 3. 过滤规则

### 3.1 英文牙科 —— `data/dental_filter.py`（**v3 已放宽**）

- R1a 精确词 `STRONG_EXACT`（约 70 词）：tooth/dental/gingiva/periodont/mandible/maxilla/palate/molar… 
  **+ v3 新增 24 个口腔内科/唾液腺词**：salivary, saliva, sialadenitis, sialolith, sialorrhea, xerostomia,
  parotid, submandibular, sublingual, aphthous, aphthae, leukoplakia, stomatitis, gingivostomatitis,
  glossitis, cheilitis, pericoronitis, chlorhexidine, halitosis, mouthwash, mouthrinse, frenum, frenulum, frenectomy
- R1b 词干 `STRONG_STEMS`：gingiv/periodont/mandib/maxill/endodont/orthodont/prosthodont/odonto/palat
- R1c 限定短语 `DENTAL_PHRASES`：alveolar+X / inferior alveolar nerve / dental pulp / pulp+X
- R2 "oral" 语境 `ORAL_CONTEXT_PATTERNS`（约 26 个）：oral cavity/cancer/ulcer/surgery/…（严格版剔除 R2）
- 排除 `NEGATIVE_PATTERNS`：molar pregnancy / hydatidiform
- 判定函数：`is_dental_record_strict`（D1 学科 + D2 subject=="Dental" + **R1 不含 R2**）

### 3.2 中文牙科 —— `data/check_cn_dental_content.py`

- C1 中文强关键词 `CN_STRONG`（约 200 词，已含唾液腺/口腔黏膜/阿弗他/白斑/扁平苔藓等，较全面）
- C3 英文 R1/R2（复用 dental_filter，full 版非 strict）
- D3 临床科室 `Clinical Department == "口腔科"`
- 判定函数：`dental_signal = content_signal(C1+C3) + dept_signal(D3)`

> 审核结论：中文过滤准确（被剔除的 285 题全是内科/儿科/妇产等通科题）；英文原 R1 过严（漏口腔内科词），v3 已放宽。

---

## 4. 为「牙科超越」所做的全部努力（均未果，已诚实记录）

| 路径 | 尝试 | 结果 |
|---|---|---|
| 调参 | 中英牙科 36 组细扫 + α 消融 | 天花板=打平 |
| 换学生 | Qwen2.5/Qwen3/Llama/R1（R1 零样本=教师但蒸馏反降 60.71%） | 打平或更差 |
| 换蒸馏机制 | α∈{0,0.15,0.35} | α=0 已最优 |
| 加数据·跨域互译 | +549 中 / +378 英 | 变差/中性 |
| 加数据·多选拆分/重组 | +428 判断题 / +348 重组五选项 | 变差/降回教师 |
| 加数据·放宽过滤回收 | +81 MedQA 口腔内科（train_v3 631） | Qwen2.5 66.67% 打平 / Llama 61.9% 更差 |
| 加数据·同域挖矿扩充 | +6381 CMExam 牙科（中文 train_v2 6762） | **3-seed 均值 86.90% 打平，0.00 变化** |

---

## 5. 当前运行中的任务

- **无运行中任务**。全部实验已跑完。

## 6. 待办 / 下一步（新会话建议顺序）

1. **（已完成）最终结论定稿（已修正英文泄漏）**：中文全科/英文全科/中文牙科三场景学生超越教师；
   英文牙科干净口径下打平（+0.40pp）。中文牙科 1386 题 +2.17pp（2/3 seed p<0.01）显著。
   英文牙科曾测出 +8.33pp，实为「书籍题混入测试集」的背题泄漏，已作废。见 `REPORT_dental_final_v2.md`。
2. **（可选）把修正后结论同步进导师汇报** `REPORT_dental_final.md`（旧结论仍写「牙科打平」，需更新）。

---

## 7. 关键文件索引

- 数据说明：`data/README.md`
- 过滤规则：`data/dental_filter.py`（英文 v3）、`data/check_cn_dental_content.py`（中文）
- 数据重建：`data/prepare_en_dental_v3.py`、`data/prepare_en_dental.py`、`data/prepare_cn_dental_clean.py`
- 训练入口：`shared/train_choice_head_distill.py`、`shared/eval_choice_head.py`
- 结果汇报：`REPORT_dental_final.md`（导师汇报）、`REPORT_filter_relaxation.md`、`REPORT_mcq_split.md`、
  `REPORT_en_general_tuning.md`、`OVERNIGHT_REPORT_2026-09-03.md`、`DATA_REPORT_dental.md`
- 任务状态：`TASK_STATUS.md`、`HANDOVER.md`
- 环境：`setup.env`（模型路径 + DEEPSEEK_API_KEY 已补入；用 `/home/student/anaconda3/bin/python3`，torch/transformers/peft 已装）

---

## 8. 环境速查

- Python：`/home/student/anaconda3/bin/python3`（3.12.7，torch/transformers/peft/bitsandbytes 已装）
- GPU：NVIDIA H100 NVL 95GB（共享，用前 `nvidia-smi` 查空闲）
- 模型：`/home/student/arthas/mentalDistill/models/`（Qwen2.5-14B/32B、Qwen3-32B、Llama-3.3-70B、
  DeepSeek-R1-Distill-Qwen-32B、gemma-3-27b-it、phi-4；**Qwen3-32B-Instruct 目录为空，不可用**）
- 教师 API：DeepSeek-V4-flash（`teachers/deepseek_v4flash.json`，**API key 为空**，需补 `DEEPSEEK_API_KEY`）
