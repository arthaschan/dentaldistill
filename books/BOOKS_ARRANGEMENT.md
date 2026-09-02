# 3 本牙科教材：题目情况与安排（BOOKS_ARRANGEMENT）

> 本文档回答：3 本书各有多少题、什么题型、质量如何；多选题是否会影响英文训练/测试正确率；
> 最终怎么安排（哪些进英文牙科、哪些进英文全科、哪些不用）。
> 提取脚本可复现：`books/extract_*.py` → `books/normalize_books.py` → `data/prepare_en_dental.py`。

---

## 1. 三本书题目情况（实测，2026-09-01 重跑）

| 书 | PDF | 题型 | 解析题数 | 有效题（有答案） | 规整后条数 |
|---|---|---|---|---|---|
| Best of Fives for Dentistry (3rd ed.) | `Best of Fives for Dentistry.pdf` | **单候选 A–E** | 298 | 272 (91%) | BoF 272 |
| Mosby's Review for the NBDE Part Two | `Mosby's Review for the NBDE Part Two ( PDFDrive ).pdf` | **单候选 A–E** | 396 | 372 (94%) | NBDE 366（6 题仅 3 选项被规整剔除） |
| MCQs for Dentistry | `MCQs for Dentistry.pdf` | **true/false 多选**（答案=为真陈述集合，如 "ADE"） | 408 | 401 (98%) | MCQ 401 |

### 1.1 单选题答案分布（BoF / NBDE）
- BoF 答案字母：A 48 / B 65 / C 63 / D 49 / E 48（较均匀）。
- NBDE 答案字母：A 76 / B 98 / C 84 / D 86 / E 28（E 偏少，正常）。

### 1.2 章节分布（含非牙科章节，需过滤）
- BoF：Human Disease 36、Pharmacology 35、Oral Pathology 32、Radiology 32、
  Restorative 30、Oral Medicine 29、Periodontics 29、Dental Materials 28、
  Child Dental 26、Oral Surgery 21。
- NBDE：Oral Diagnosis 69、Patient Management 58、Operative 50、Periodontics 48、
  Prosthodontics 46、OMFS 45、Endodontics 40、Pharmacology 40。
- MCQ：Restorative 72、Dental Materials 54、Human Disease 50、Oral Surgery 48、
  Oral Medicine 40、Oral Pathology 38、Child Dental 38、General Dentistry 34、Therapeutics 34。
- **注意**：三本书都含 Human Disease / Pharmacology / Patient Management 等**非牙科章节**，
  必须用 `data/dental_filter.py` 的 R1/R2 规则二次过滤（实测会剔除大量非牙科题，见 §3）。

---

## 2. 多选题是否影响英文训练/测试正确率？（评估结论：会，且不可评分 → 不并入）

MCQs for Dentistry 是 **true/false 多选**：每题 A–E 五条陈述，答案是「全部为真的陈述集合」
（如 "ADE"）。这与本仓库「单候选 A–E」任务（模型只输出一个字母）**格式不兼容**。

用 `books/eval_multiselect_impact.py` 沿真实代码路径演示（结论可复现）：

1. **训练路径**（`shared/train_choice_head_distill.py` 的 `DentalChoiceHeadDataset.__getitem__`）：
   多选答案 "ADE" 不在 `OPTION_LETTERS=["A".."E"]` 中 → 被强制置为 `"A"`，`gt_option=0`。
   → 会用「标准答案 A」去监督一道真值是「A、D、E 三条都真」的题，**主动教错**。
2. **评估路径**（`extract_answer_char`）：只取生成文本里出现的**第一个** A–E 字母。
   模型正确输出 "ADE" 时只取到 "A"，与存储答案 "ADE" 永远对不上 → **多选无法被单候选指标评分**。
3. **实测统计**：`books_mcq.jsonl` 408 题中，答案长度 1（单选）仅 57 题，长度 ≥2（多选）344 题
   （2→124 / 3→163 / 4→51 / 5→6）。即 **84% 是多选**。

**结论**：把 MCQ 多选并入单候选英文训练/测试，会（a）训练时给错误监督信号、（b）评估时不可评分，
两者都会拉低/无法反映正确率。因此 **MCQ true/false 多选不并入单选蒸馏**，作为辅助集保留
（`books/books_tf.jsonl`），未来如需做「多选/判断题」任务再单独用。

---

## 3. 最终安排

### 3.1 英文牙科（en_dental）—— 并入 BoF + NBDE 单候选（已落地，v2 过滤器重筛后口径）
- 单候选池 `books/books_singlebest.jsonl` = BoF 272 + NBDE 366 = 638。
- `data/prepare_en_dental.py` 对 638 题跑牙科判定（`dental_filter.py` v2：R1 强词 + R2 oral 语境，修复词干误配）
  + 去重 + 避开 test 后，**净并入 train 371 题**：
  - BoF 272 → 保留牙科 **147**（剔除 125：Human Disease/Pharmacology 等非牙科章节）
  - NBDE 366 → 保留牙科 **224**（剔除 142）
- `data/en_dental/train.jsonl` 现为 **603 = MedQA 231 + MMLU 1 + BoF 147 + NBDE 224**。
- val / test 仍是纯 MedQA/MMLU 牙科（30 / 93），**书籍题只进 train**（保证测试集干净、可对比）。
- 注：v1→v2 过滤器修复了词干误配（gingiv/periodont 等整词边界漏配）与歧义词假阳性（alveolar/pulp/molar），
  重筛后保留的牙科题数变化（MedQA 219→231、BoF 93→147、NBDE 185→224），详见 `reports/en_dental_audit.md`。

### 3.2 英文全科（en_general）—— 已并入（2026-09-01 决定）
- 2 本单选书（BoF 272 + NBDE 366 = 638）已并入 `data/en_general/train.jsonl`（**仅 train**，
  test 固定 4110 保持 MedQA/MMLU 不动、val 不动，保证评测可比）。
- 并入后 train = **9789**（medqa 8876 + mmlu 275 + BoF 272 + NBDE 366），按 uid 去重、与
  val/test 零重叠（脚本 `data/merge_books_into_en_general.py`，幂等可重跑）。
- 选项统一为 `A. text` 格式（与 MedQA/MMLU 一致）。
- 说明：书里 Human Disease/Pharmacology/Patient Management 等非牙科章节对「全科」也是有效
  题目，故并入时不加牙科过滤（如需只并入牙科题，加 `--filter-dental` 即可）。
- 注：此前默认不并入的理由（牙科教材会稀释「全科」语义）已按需求改为并入，理由仅作记录。

### 3.3 多选题（MCQ）—— 辅助集，不并入任何单选
- `books/books_tf.jsonl`（401 题）保留，标注 `format=true_false_multi`，供未来「多选/判断题」任务。

---

## 4. 复现命令

```bash
python3 books/extract_bestoffives.py    # -> books/books_bof.jsonl   (298/272)
python3 books/extract_nbde.py           # -> books/books_nbde.jsonl  (396/372)
python3 books/extract_mcqs.py           # -> books/books_mcq.jsonl   (408/401)
python3 books/normalize_books.py        # -> books_singlebest.jsonl(638) + books_tf.jsonl(401)
python3 data/prepare_en_dental.py       # 并入 en_dental train（净 +278）
python3 books/eval_multiselect_impact.py  # 多选影响演示（应展示训练/评估两处不兼容）

# 审计（应 [PASS]）
python3 data/check_dental_subset.py data/en_dental/test.jsonl
```

## 5. 关键数字速查

| 项 | 值 |
|---|---|
| 单候选池（BoF+NBDE） | 638 题 |
| 净并入 en_dental train | 371 题（BoF 147 + NBDE 224） |
| en_dental train 构成 | 603 = MedQA 231 + MMLU 1 + 书 371 |
| MCQ 多选 | 401 题（344 多选 + 57 单选），**不并入** |
| 多选影响 | 训练给错监督 + 评估不可评分 → 拉低/无法反映正确率 |
