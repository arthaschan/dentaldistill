# 英文牙科子集「严格 R1-only」口径决定 + 证据

> 日期：2026-09-01。触发：用户要求英文牙科「不得包含非牙科数据」。

---

## 0. 一句话

原 `data/en_dental/`（603/30/93）用的是 **R1 + R2「oral 语境」宽口径**，其中 50 道「仅 R2」的
边界题**混有非牙科题**。为满足「零非牙科」，改为 **R1 严格口径**（只用强牙科词），
现为 **566/26/84 = 676 题**。

---

## 1. 问题：R2「oral 语境」仍会误收非牙科题

`dental_filter.py` 的 R2 规则（oral cavity / oral ulcer / oral lesion / oral health /
oral candidiasis / oral thrush / …）本意是「口腔语境」，但这些短语大量出现在**全身病的
口腔表现/症状**里，导致误收。实测 `reports/en_dental_audit_detail.md` 里 50 道 R2 边界题，
典型非牙科例子：

| uid | 题干主题 | 命中 | 真实科室 |
|---|---|---|---|
| medqa_train_004190 | 20 岁男「找摄像头」（精神分裂） | oral health | 精神科 |
| medqa_train_001115 | 55 岁男发热干咳（肺炎） | oral lesion | 呼吸科 |
| medqa_train_008341 | 68 岁女吞咽困难口臭（Zenker 憩室） | oral cavity | 消化科 |
| medqa_train_005490 | 40 岁女注意力不集中（抑郁） | oral lesion | 精神科 |
| medqa_train_009536 | 44 岁女吞咽痛（食管） | oral cavity | 消化科 |
| medqa_train_008591 | 66 岁男头痛发热（脑膜炎） | oral thrush | 神经/感染 |

这些题**不是牙科**，只是题干里顺带出现「oral 症状」。R2 的 oral ulcer/lesion/cavity/
thrush/candidiasis 是「全身病口腔表现」，而非「牙科本体」。

## 2. 决定：R1 严格口径（零非牙科）

- 新函数 `dental_filter.is_dental_record_strict()` / `dental_match_strict()`：只保留
  R1 强牙科词（tooth/dental/gingivitis/periodontal/odontogenic/…），**剔除全部 R2**。
- `data/prepare_en_dental.py` 改用严格口径重筛。

## 3. 重筛结果

| 集合 | 旧（R1+R2 宽） | 新（R1 严格） | 剔除（仅 R2） |
|---|---|---|---|
| train | 603 | 566 | 37 |
| val | 30 | 26 | 4 |
| test | 93 | 84 | 9 |
| 合计 | 726 | **676** | 50 |

新 train 来源 = MedQA 200 + MMLU 1 + BoF 142 + NBDE 223。

## 4. 证据（可复现）

```bash
# 1. 重筛（已改严格口径）
python3 data/prepare_en_dental.py          # -> 566/26/84

# 2. 审计：三集应全 PASS，且每题都命中 R1（无「仅 R2」题）
python3 data/audit_en_dental.py data/en_dental
python3 data/check_dental_subset.py data/en_dental/test.jsonl

# 3. 确认零「仅 R2」题：
python3 -c "
import sys,json
sys.path.insert(0,'data')
from dental_filter import dental_match, question_text
for split in ['train','val','test']:
    r2only=0
    for l in open(f'data/en_dental/{split}.jsonl'):
        hits=dental_match(question_text(json.loads(l)))
        if hits and all(h[0]=='R2' for h in hits): r2only+=1
    print(split,'仅R2题数=',r2only)   # 应全为 0
"
```

## 5. 取舍说明

- **代价**：R1 严格口径会连带剔除少数「确实牙科」的 R2 题（oral cancer / oral carcinoma /
  oral hygiene / oral surgery 等口腔颌面外科题，约十道），recall 略降。
- **收益**：保证**零非牙科**（precision=100%），满足用户硬性要求，且每条题都命中强牙科词、
  可逐题审计。
- 若后续要收回这些「真口腔颌面外科」题，可把 R2 收窄到 `oral cancer/carcinoma/squamous/
  surgery/surgeon/hygiene/prosthesis/implant` 等「明确牙科短语」，但当前按严格口径执行。
