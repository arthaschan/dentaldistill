# 数据挖掘评估：data/cmexam 三个 CSV 中是否还有未用的牙科题

> 用户问题：data/cmexam 文件夹的中文题，之前应该只用了 train.csv，另两个文件（val.csv / test_with_annotations.csv）
> 没用。看能否找到更多牙科题。本文给出逐文件审核结论与量化评估。

---

## 1. 结论先行（重要，与用户原假设相反）

| 用户原假设 | 实际情况 |
|---|---|
| 「只用了 train.csv」 | **错——实际用的是 `test_with_annotations.csv`（含学科标签的那个），train.csv / val.csv 反而从没被用过** |

证据链：
- 当前 `data/cn_dental/`（train 580 + val 125 + test 125 = 830 题）的记录字段含
  `Medical Discipline / Clinical Department / Disease Group` —— 这些字段**只有 test_with_annotations.csv 有**。
- 830 题的 uid 与 `test_with_annotations.csv` 里 `Medical Discipline==口腔医学` 的 830 题 **100% 重叠**；
  与 train.csv / val.csv 的内容命中 **0 重叠**。
- 旧管线真正读的源是 `mentalDistill/shared/cmexam_full.csv`（6811 行，830 口腔医学），
  它就是 test_with_annotations.csv 的副本（6811 行、830 口腔医学，完全一致）。

---

## 2. 三个文件的基本盘（csv 模块按行解析，非 wc -l）

| 文件 | 真实行数 | 列 | 状态 |
|---|---|---|---|
| `train.csv` | 54497 | Question/Options/Answer/Explanation（**无学科标签**） | **从未使用** |
| `val.csv` | 6811 | Question/Options/Answer/Explanation（**无学科标签**） | **从未使用** |
| `test_with_annotations.csv` | 6811 | + Disease Group/…/Medical Discipline/Clinical Department/Difficulty | **已用（830 口腔医学全用）** |

三文件按 uid（md5(Question||Options)[:12]）**两两互不相交**（train∩val=train∩test=val∩test=0），
是 CMExam 的 train/val/test 三个独立切分。

---

## 3. 未挖掘的牙科题量（关键数字）

### 3.1 内容级关键词命中（train.csv / val.csv 无标签，只能用关键词估算）

| 文件 | 总行数 | 内容命中牙科词 | 与已用 830 重叠 |
|---|---|---|---|
| `train.csv` | 54497 | **6848** | 0 |
| `val.csv` | 6811 | **832** | 0 |

### 3.2 精度/召回校准（用 test_with_annotations.csv 的地面真值学科标签做混淆矩阵）

内容级关键词 vs `Medical Discipline==口腔医学`：

- TP 538 / FP 164 / FN 292 / TN 5817
- **Precision（命中里真牙科）= 76.6%**
- **Recall（牙科里被命中）= 64.8%**

### 3.3 真牙科题量估计

- 按比例（test 里口腔医学占 12.19%）：train.csv ≈ **6650**，val.csv ≈ **830**，合计 ≈ **7500**
- 按关键词命中×精度保守估：train.csv ≈ **5250**，val.csv ≈ **640**，合计 ≈ **5900**

**结论：train.csv + val.csv 里约有 5900～7500 道牙科题未被使用，是当前 830 题的 7～9 倍，
是当前干净训练集 381 题的 15～20 倍。** 这正是交接文档里说的「同域加数据（更多 CMExam 口腔题）」
——之前以为没有，实际有近万道。

---

## 4. 唯一障碍：train/val 没有学科标签，只能靠内容关键词

内容级过滤（`check_cn_dental_content.CN_STRONG`）精度 76.6%、召回 64.8%，即：
- 命中里约 1/4 是假阳性；
- 真牙科里约 1/3 会漏掉。

假阳性主要来自少数歧义词（在 test 上统计的 FP 高频词）：

| 词 | FP 数 | 原因 |
|---|---|---|
| 三叉神经 | 28 | 神经内科，非牙科 |
| 齿 | 23 | 齿状线（肛肠）、齿摇发脱（中医衰老证） |
| 面神经 | 19 | 神经科 |
| 颌 | 19 | 下颌角解剖肌止点（解剖通科） |
| 腭 | 16 | 软腭麻痹（神经核） |
| 口腔 | 15 | 口腔给药、SLE 口腔溃疡、胃镜「口腔」 |
| 切开引流 | 7 | 普外科阑尾/脓肿 |
| 海绵窦 | 6 | 神经解剖 |
| 流涎 | 5 | 毛果芸香碱副作用 |

漏掉的牙科题（FN 292）主要是无关键词的牙科专业题（口腔材料、术式、器械等）。

---

## 5. 建议下一步（若要挖这批数据）

1. **收紧关键词**：去掉/降级 FP 高频词——`三叉神经 / 面神经 / 海绵窦 / 切开引流 / 流涎` 单独命中不算，
   单字 `齿/颌/腭/口腔` 改为「必须命中牙科复合词」（如 颌骨/下颌骨/上颌/口腔黏膜/口腔溃疡…），
   预期把 precision 从 76.6% 提到 ~90% 以上。
2. **采样验证**：在 train.csv 上抽 100 条人工/关键词复核 precision，达标后再落地。
3. **落地**：产出 `data/cmexam/dental_train.csv` / `dental_val.csv`（或直接 jsonl），
   与现有 `cn_dental` 按 uid 去重后并入中文牙科训练集。
4. **注意切分正确性**：train.csv 是「真训练切分」，test_with_annotations.csv 是「真测试切分」。
   用 train.csv 扩训练、测试保持原 84 题，切分比现在更干净（现在 train/val/test 都来自 test 切分内部重切）。

---

## 6. 复现脚本

- `data/audit_cmexam_unused.py` —— 逐文件统计内容命中 + 与已用 830 的 uid 重叠。
- `data/audit_cmexam_precision.py` —— 混淆矩阵（精度/召回校准）+ FP 高频词 + 三文件重叠。

运行（用 anaconda python）：
```
/home/student/anaconda3/bin/python3 data/audit_cmexam_unused.py
/home/student/anaconda3/bin/python3 data/audit_cmexam_precision.py
```
