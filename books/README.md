# 3 本牙科教材（books/）

> 来源：`mentalDistill/fullEnglish/book/`。版权教材，PDF 不提交 git（.gitignore 排除 `*.pdf`），
> 仅保留提取脚本与规整后的 jsonl 由脚本重建。
>
> **题目情况、多选题影响评估、最终安排（哪些进英文牙科/全科、哪些不并入）见
> `books/BOOKS_ARRANGEMENT.md`（权威文档）。**

## 三本书

| 书 | 文件 | 题型 | 提取脚本 | 有效题（规整后） |
|---|---|---|---|---|
| Best of Fives for Dentistry (3rd ed.) | `Best of Fives for Dentistry.pdf` | 单选 A–E | `extract_bestoffives.py` | BoF 272 |
| Mosby's Review for the NBDE Part Two | `Mosby’s Review for the NBDE Part Two ( PDFDrive ).pdf` | 单选 A–E | `extract_nbde.py` | NBDE 366 |
| MCQs for Dentistry | `MCQs for Dentistry.pdf` | true/false 多选 | `extract_mcqs.py` | MCQ 401 |

## 处理流程

```bash
# 1. 提取（pdftotext -> 结构化 jsonl）
python3 books/extract_bestoffives.py   # -> books/books_bof.jsonl
python3 books/extract_nbde.py          # -> books/books_nbde.jsonl
python3 books/extract_mcqs.py          # -> books/books_mcq.jsonl

# 2. 规整字段 + 区分单选/多选
python3 books/normalize_books.py
#    -> books/books_singlebest.jsonl（BoF+NBDE 单选，并入牙科训练池）
#    -> books/books_tf.jsonl        （MCQ 多选，辅助集，不并入单选）

# 3. 并入英文牙科数据（去重、避开 test，再用牙科判定过滤）
python3 data/prepare_en_dental.py

# 4. 多选题影响评估（演示为什么 MCQ 多选不并入单选）
python3 books/eval_multiselect_impact.py
```

## 说明

- 书籍题用 `data/dental_filter.py` 的 R1/R2 规则二次过滤（书里"Human Disease/Pharmacology"章节有少量非牙科题，会被剔除）。
- 单选（BoF+NBDE）并入英文牙科 train（净 +278：BoF 93 + NBDE 185）；true/false（MCQ）为不同任务，作为辅助集保留，不混入单选蒸馏。
- **MCQ 是 true/false 多选（84% 答案为多字母集合如 "ADE"），与单候选 A–E 任务格式不兼容：训练会给错监督、评估不可评分，故不并入英文训练/测试**（详见 `BOOKS_ARRANGEMENT.md` §2 与 `eval_multiselect_impact.py`）。
- 字段统一为 `uid, Question, Options("A …\nB …"), Answer, n_options, source, subject`（与 MedQA/MMLU 一致）。
