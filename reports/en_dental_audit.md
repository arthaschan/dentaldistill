# 英文牙科子集审计 + 过滤原则（可接受其他 AI 审计）

> 结论：`data/en_dental/` 经 `dental_filter.py v2` 重筛后，**假阳性（非牙科误入）已清除**
> （v1 的 alveolar→肺泡、pulp→脾髓、molar→葡萄胎、oral examination 泛滥等已修）。
> 现为 train 603 / val 30 / test 93，其中 92% 命中强牙科词，8% 为「oral 口腔语境」边界题（列明供复核）。

---

## 1. 过滤原则（auditable）

`data/dental_filter.py` 判定一条题（题干+选项拼接）是否为牙科，命中任一即判牙科：

| 规则 | 内容 | 例子 |
|---|---|---|
| **D1** | 中文学科字段 `Medical Discipline == "口腔医学"` | 中文 CMExam |
| **D2** | 英文学科字段 `subject == "Dental"` | 英文 MedMCQA |
| **R1** | 强牙科词（精确词/词干/限定短语） | tooth, dental, caries, gingivitis, periodontal, pulpitis, alveolar bone, inferior alveolar nerve, endodontic, amalgam, denture… |
| **R2** | "oral" 的明确口腔语境（口腔疾病/解剖） | oral cavity, oral thrush, oral candidiasis, oral cancer, oral ulcer, oral surgery, oral hygiene… |

**明确排除（不算牙科）**：
- 裸 "oral"（口服/oral medication/oral contraceptive/oral rehydration）
- 裸 "mucosa"、"crown"（胃/肠黏膜、皇冠）
- "molar pregnancy" / "hydatidiform"（葡萄胎，molar 在此非牙科）
- "alveolar" 单独出现（肺泡）；"pulp" 单独出现（脾髓）——必须带牙科限定词（R1 短语）

**判定函数**：`dental_match(text)` 返回命中明细 `[(规则, 词), ...]`，`is_dental_record(record)`
返回 `(是否牙科, 明细)`。每条命中都给出「命中了哪个词/哪条规则」，可逐题复核。

## 2. v1 → v2 修复了什么（审计要核查的重点）

v1 有两类 bug（由 `data/audit_en_dental.py` 发现）：

| bug | 表现 | 后果 |
|---|---|---|
| **词干误配** | `gingiv/periodont/mandib/maxill/occlus` 用 `\b...\b` 当整词，匹配不到 gingivitis/periodontal/mandibular/occlusal | 漏掉真牙科题（假阴性） |
| **歧义词假阳性** | `alveolar`(肺泡)/`pulp`(脾髓)/`molar`(葡萄胎) 单独命中即判牙科；R2 `oral examination` 是常规体格检查用语 | 把呼吸科/血液/妇产科/通用体格检查题误判为牙科（假阳性） |

v2 修复：
- 词干改「词首边界」匹配（`\bgingiv` 匹配 gingival/gingivitis/gingivectomy）；
- `alveolar`/`pulp` 改为「牙科限定短语」（alveolar bone/ridge/process/socket/nerve、dental pulp、pulp chamber/horn/cap/…）；
- `molar` 保留（molar tooth）但加否定语境 `molar pregnancy`/`hydatidiform`；
- R2 删掉 `oral examination`、`oral mucosa`（太泛化）。

**验证**：`dental_filter.py` 顶部 docstring 的用法示例 + 单测
（splenic white pulp / alveolar hemorrhage / molar pregnancy / oral examination → 均判非牙科；
gingivitis / periodontal / alveolar bone / dental pulp / oral thrush → 均判牙科）。

## 3. 重筛后 en_dental 构成

| 集合 | 总数 | 命中 R1 强牙科词 | 仅 R2 oral 语境（边界） |
|---|---|---|---|
| train | 603 | 566 (94%) | 37 (6%) |
| val   | 30  | 26 (87%) | 4 (13%) |
| test  | 93  | 84 (90%) | 9 (10%) |
| 合计 | 726 | 676 (93%) | 50 (7%) |

train 来源：MedQA 231 + MMLU 1 + BoF 147 + NBDE 224（书题并入 train，见 §5）。

## 4. 剩余的 50 道「仅 oral 语境」边界题怎么处理

这 50 题只命中 R2「oral」语境（oral ulcer/oral candidiasis/oral cavity/oral cancer/…），
无强牙科词。它们是**口腔黏膜病/口腔表现**类题目，多数是「全身病的口腔表现」：
- oral ulcer → 复发性阿弗他溃疡、Behçet、Crohn、SLE（口腔黏膜病，属口腔医学/牙科教学范围）
- oral candidiasis/thrush → 免疫缺陷（SCID/HIV）的口腔念珠菌（口腔表现）
- oral cavity squamous cell carcinoma → 口腔癌（口腔颌面外科，明确牙科）
- oral lesion → 多形红斑/Steven-Johnson 的口腔损害（口腔表现）

**审计口径**：这些属「口腔医学」范畴但可能不是「牙/颌/齿」本体。清单已写入本报告附录
（`audit_en_dental.py --report` 输出），供审计方按「牙科」的定义逐题裁定，而非静默判定。
若采用**严格「牙/齿/颌」定义**，可只保留 R1 命中题（676 题）；若采用**宽「口腔医学」定义**，
保留 R1+R2（726 题）。默认采用宽定义（口腔医学含口腔黏膜病/口腔颌面外科）。

## 5. 与书籍/全科的关系

- 2 本单选书（BoF+NBDE）已并入 `en_general/train.jsonl`（见 `books/BOOKS_ARRANGEMENT.md`），
  并随 en_dental 重筛一起并入 en_dental/train（BoF 147 + NBDE 224）。
- MCQ（true/false 多选）不并入任何单选（格式不兼容，见 `books/BOOKS_ARRANGEMENT.md` §2）。

## 6. 复核命令（审计方）

```bash
# 1. 逐题命中明细（audit 报告）
python3 data/audit_en_dental.py data/en_dental --report reports/en_dental_audit_detail.md

# 2. 全子集牙科判定（应全部命中 R1 或 R2，无非牙科）
python3 data/check_dental_subset.py data/en_dental/test.jsonl --detail reports/en_dental_test_detail.txt

# 3. 过滤器单测（歧义词/词干修复验证）
python3 -c "from data.dental_filter import dental_match; \
  print(dental_match('splenic white pulp contains lymphocytes')); \
  print(dental_match('diffuse alveolar hemorrhage in the lung')); \
  print(dental_match('complete molar pregnancy')); \
  print(dental_match('What causes gingivitis in adults?'))"
```
