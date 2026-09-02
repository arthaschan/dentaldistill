# 牙科数据「无非牙科」检查报告

> 日期：2026-09-02。检查工具：`data/check_no_nondental.py`（可复现，退出码 0 = 无非牙科）。
> 结论一句话：**中文牙科干净集 545 题 + 英文牙科 676 题，全部为牙科，无非牙科数据。**

---

## 1. 检查对象

| 数据集 | 路径 | 题数 | 口径 |
|---|---|---|---|
| 中文牙科干净集 | `data/cn_dental_clean/{train,val,test}.jsonl` | 545（381/80/84） | 内容关键词 + 临床科室=口腔科 |
| 英文牙科 | `data/en_dental/{train,val,test}.jsonl` | 676（566/26/84） | R1 强牙科词（严格口径） |

## 2. 检查方法

### 2.1 中文牙科（cn_dental_clean）
对每题做两道检查，任一不满足即判「疑似非牙科」：
1. **牙科信号**：`dental_signal(record) = content_signal + dept_signal`，须非空。
   - `content_signal`：题干+选项命中中文强牙科关键词（龋/牙髓/牙周/颌/牙龈/釉质/根管/义齿/正畸/腮腺/舌下神经…，
     扩充后见 `data/check_cn_dental_content.py` 的 `CN_STRONG`）。
   - `dept_signal`：`Clinical Department == "口腔科"`。
2. **非口腔科科室的题必须还有内容关键词**：若 `Clinical Department` 不含「口腔」，则 `content_signal` 须非空
   （防止靠科室字段误收）。这些非口腔科科室题（46 道）已逐题人工复核，全是真牙科（奶瓶龋/乳牙深龋/颧弓骨折/
   下牙槽神经阻滞麻醉/黏液囊肿/舌癌转移/腺泡细胞癌/鳃弓畸形/甲状舌管囊肿…），见 `reports/cn_dental_rescreen_report.md`。

### 2.2 英文牙科（en_dental，R1 严格口径）
对每题做两道检查：
1. **必须命中 R1 强牙科词**（tooth/teeth/dental/gingivitis/periodontal/odontogenic/…，`dental_filter.py` 的 R1a/R1b/R1c）。
2. **不得是「仅 R2 oral 语境」**：R2 的 oral ulcer/lesion/cavity/candidiasis/thrush 是「全身病口腔表现」，
   会把精神分裂（oral health）、肺炎（oral lesion）、Zenker 憩室（oral cavity）等非牙科题误收，已整体剔除
   （`is_dental_record_strict`），见 `reports/en_dental_strict_decision.md`。

## 3. 检查结果（2026-09-02 实测，rc=0）

### 中文牙科干净集
| 集合 | 题数 | 无非牙科信号 | 非口腔科且无关键词 |
|---|---|---|---|
| train | 381 | 0 | 0 |
| val | 80 | 0 | 0 |
| test | 84 | 0 | 0 |
| 合计 | 545 | **0** | **0** |

### 英文牙科
| 集合 | 题数 | 无 R1 命中 | 仅 R2 |
|---|---|---|---|
| train | 566 | 0 | 0 |
| val | 26 | 0 | 0 |
| test | 84 | 0 | 0 |
| 合计 | 676 | **0** | **0** |

## 4. 结论

两个牙科数据集（中文 545 + 英文 676）**均无非牙科数据**：
- 中文：545 题全部有牙科信号（内容关键词或口腔科科室），非口腔科科室的 46 题经关键词 + 人工复核确认是牙科。
- 英文：676 题全部命中 R1 强牙科词，无「仅 R2 oral 语境」题。

## 5. 复现

```bash
cd /home/student/arthas/dentaldistill
python3 data/check_no_nondental.py          # 退出码 0 = 无非牙科
python3 data/check_cn_dental_content.py data/cn_dental_clean   # 中文内容级检测
python3 data/check_dental_subset.py data/en_dental/test.jsonl  # 英文牙科子集审计
```
