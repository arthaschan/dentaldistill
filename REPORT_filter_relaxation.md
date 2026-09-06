# 实验汇报：过滤审核、放宽过滤与数据集重建

> 用户提出两个问题：① CMExam 是否只用了 train、遗漏了其他文件？② 牙科过滤是否过严、误杀牙科题？
> 本报告给出审核结论 + 放宽过滤 + 新数据集组成 + 重训结果。

---

## 1. CMExam 数据审核结论

| 项 | 结论 |
|---|---|
| 源文件 | **单个** `mentalDistill/shared/cmexam_full.csv`（6811 行），**不是 train/val/test 三个 CSV** |
| 口腔医学题 | 830 题 |
| 已使用 | **全部使用**：train 580 + val 125 + test 125 |
| CSV 中不在 resplit 的 221 行 | 全是**非牙科**（药学 88 / 中药学 121 / 临床 6 / 中西医 3 / 公卫 2 / 中医 1），**0 口腔医学** |

**「只用了 train.csv、另外两个文件没用」不成立**：CMExam 没有分三个文件，830 道口腔医学题也已全部使用，没有遗漏的牙科数据。

## 2. 过滤是否过严？—— 中文准、英文过严

### 2.1 中文牙科：过滤准确，无误杀

被内容过滤剔除的 285 题（train 199 / val 45 / test 41），临床科室**全是非口腔科**（内科/儿科/妇产/传染/外科…），题干也无牙科关键词——确为「口腔医学标签下的通科题」，**不是牙科误杀**。中文词表 `CN_STRONG` 本就含唾液腺/口腔黏膜/阿弗他/白斑等词，较全面。

### 2.2 英文牙科：R1 词表过窄，误杀口腔内科题

英文 `R1` 原只含「硬牙科」（tooth/gum/jaw），**缺口腔内科/唾液腺词汇**（salivary/xerostomia/mucosa/aphthous/leukoplakia 等），把 Oral Medicine/Oral Surgery 类真牙科题误杀（MCQ 书 2003 条陈述里 1558 条无关键词，其中大量是口干/唾液腺/口腔黏膜病）。

## 3. 放宽过滤（dental_filter.py v3）

在 `STRONG_EXACT` 新增 24 个「口腔内科/唾液腺」精确词（避免歧义词）：

```
salivary, saliva, sialadenitis, sialolith, sialorrhea, xerostomia,
parotid, submandibular, sublingual, aphthous, aphthae, leukoplakia,
stomatitis, gingivostomatitis, glossitis, cheilitis, pericoronitis,
chlorhexidine, halitosis, mouthwash, mouthrinse, frenum, frenulum, frenectomy
```

- 有歧义的词（mucosa 胃黏膜、buccal/labial 给药途径、mucocele 阑尾/胆囊）**不加入**，避免重新引入假阳性。
- 验证：新词能命中 xerostomia/salivary/aphthous/leukoplakia/cheilitis，且不误判 pneumonia/stomach pain（非牙科）。

## 4. 新数据集组成

### 4.1 英文牙科（重建 train_v3，test 保持 84 不动）

放宽 R1 后从 en_general（MedQA/MMLU）与书籍（BoF/NBDE）重筛，重建训练集：

| 集合 | 旧（R1 严格） | 新（R1 v3 放宽） | 变化 |
|---|---|---|---|
| train | 566 | **631** | +65（去重后净 +81 新增） |
| val | 26 | 26（保持） | 0 |
| test | 84 | 84（保持） | 0 |

train_v3 来源分布：**MedQA 269 + MMLU 1 + BoF 150 + NBDE 211 = 631**（唯一 uid）。
新增 81 题来源：**MedQA 69 + BoF 8 + NBDE 4**——主体是放宽后回收的 MedQA 口腔内科牙科题（与测试同风格）。

### 4.2 中文牙科：无可扩展数据

审核确认：CMExam 830 题全用、过滤准确、285 剔除是通科题。**中文牙科没有可回收的遗漏牙科题**，暂不重建（原 train 381 已是准确口径）。

## 5. 重训结果

英文牙科两个学生，train_v3（631）重训，test 84 评测：

| 学生 | 配置 | 结果 | vs 原(566) | vs 教师 66.67% |
|---|---|---|---|---|
| Qwen2.5-32B | rank8/lr3e-4 | 66.67% | +0.40 | 0.00（=教师） |
| Llama-70B | rank16/lr1e-4 | 61.9% | −5.16 | −4.77 |

**结论：放宽过滤（回收 81 题口腔内科）没有帮助超越。** Qwen2.5 从 66.27% 微涨到 66.67%（=教师，打平），
Llama 反而从 67.06% 掉到 61.9%。与中文「同域加数据」结论一致：瓶颈是教师天花板，不是数据。

## 6. 关键文件

- 过滤规则（已放宽）：`data/dental_filter.py`（STRONG_EXACT v3）
- 重建：`data/prepare_en_dental_v3.py` → `data/en_dental/train_v3.jsonl`
- 重训：`run_retrain_v3_queue.sh`，日志 `retrain_v3_queue.log`
