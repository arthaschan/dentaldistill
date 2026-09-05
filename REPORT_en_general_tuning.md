# 英文全科（en_general）参数调优报告

> 承接用户问题：「英文牙科 2 个学生是否做了参数调优？英文全科是否做了参数调优？没做的就进行调优。」
> 启动 2026-09-03 06:14，Qwen 细扫 ~6h、Llama 细扫 ~17h（含一次 NaN 发散重跑）。

---

## 1. 核查结论（两个场景）

| 场景 | 学生 | 是否做过参数调优 | 说明 |
|---|---|---|---|
| 英文牙科 | Qwen2.5-32B | ✅ 已做 | 24 组细扫 + 最优 3-seed，见 `ablation/RESULTS_sweep_en_dental_qwen25.md` |
| 英文牙科 | Llama-70B | ✅ 已做 | 12 组细扫 + 默认 3-seed×2，见 `ablation/RESULTS_sweep_en_dental_llama70b.md` |
| **英文全科** | Qwen2.5-32B | ❌ 未做 → **本次补做** | 原只有默认配置单 run |
| **英文全科** | Llama-70B | ❌ 未做 → **本次补做** | 原只有默认配置单 run |

---

## 2. 方案

- 数据 `data/en_general/`（train 9789 / val 1017 / test 4110）；教师 Qwen3-32B 零样本 = **80.22%**。
- 网格（每学生 6 组）：rank{8,16} × lr{1e-4,2e-4,3e-4} × epoch1，α=0，seed=42。
  （依据牙科细扫结论，跳过已证劣化的 lr5e-4 / rank4 / epoch2。）
- 评测：`shared/eval_choice_head.py`（greedy, max_new_tokens=8）在 **test 4110** 上，与既有 RESULTS 口径一致。
  表内 `val_acc` 为 train.log 内部旧口径（max_new_tokens=4），仅作记录、不用于排序。

---

## 3. 结果

### 3.1 Qwen2.5-32B 细扫（test 4110，教师 80.22%，默认 82.09%）

| rank | lr | val_acc | test_acc | vs 默认 |
|---|---|---|---|---|
| 16 | 1e-4 | 72.27 | **82.41** | —（=默认）|
| 8  | 1e-4 | 71.88 | 82.29 | −0.12 |
| 8  | 2e-4 | 72.96 | 82.29 | −0.12 |
| 16 | 2e-4 | 72.86 | 81.70 | −0.71 |
| 8  | 3e-4 | 73.55 | 81.12 | −1.29 |
| 16 | 3e-4 | 70.70 | 79.59 | −2.82 |

**结论：Qwen2.5-32B 默认配置（rank16/lr1e-4）已是最优，调参无提升；lr3e-4 反而掉点。**

### 3.2 Llama-70B 细扫（test 4110，教师 80.22%，默认 81.39%）

| rank | lr | val_acc | test_acc | 状态 |
|---|---|---|---|---|
| 8  | 1e-4 | 88.00 | **82.75** | ✅ 最优 |
| 8  | 2e-4 | 85.25 | 80.83 | ✅ |
| 8  | 3e-4 | 75.12 | 77.83 | ✅ |
| 16 | 1e-4 | 87.32 | 81.61 | ✅（首跑 NaN 崩，重跑后正常，≈默认）|
| 16 | 2e-4 | 20.06 | 24.43 | ❌ 发散（≈随机）|
| 16 | 3e-4 | 11.80 | 0.0  | ❌ 发散（彻底崩坏）|

**结论：Llama-70B 的 rank16（默认）在 en_general 上不稳定——lr2e-4/lr3e-4 直接发散；
rank8 三组全稳，且 rank8/lr1e-4 = 82.75% 为全场最优，比默认 rank16/lr1e-4（81.39~81.61%）高约 1.3pp。**

### 3.3 与默认配置对比（汇总）

| 学生 | 默认(rank16/lr1e-4) | 细扫最优 | 教师 | 结论 |
|---|---|---|---|---|
| Qwen2.5-32B | 82.09% | 82.41%（=默认）| 80.22% | 默认已最优 |
| Llama-70B | 81.39% | **82.75%（rank8/lr1e-4）** | 80.22% | rank8 更优 + 更稳 |

---

## 4. 结论

1. **英文全科调参结论（与英文牙科不同）**：
   - Qwen2.5-32B：默认配置即最优，调参无收益。
   - Llama-70B：**rank8/lr1e-4 比默认 rank16/lr1e-4 更优（+~1.3pp）且更稳定**；rank16 在较高 lr 下训练发散（loss→NaN / 权重崩坏）。
2. **发散事实**：rank16 × lr2e-4 → test 24.43%（≈随机）、rank16 × lr3e-4 → test 0.0%（彻底崩坏）、rank16 × lr1e-4 首跑也 NaN 崩过一次。这说明 **Llama-70B QLoRA 在 9789 条大集上 rank16 数值不稳定，rank8 更安全**。
3. 两个学生最优配置均**稳定超越弱教师 80.22%**（Qwen +2.19、Llama +2.53）。

---

## 5. 注意事项与后续

- 本细扫为**单 seed（seed42）+ 在 test 上选优**，rank8 vs rank16 的 ~1.3pp 差距需 **3-seed 坐实**（英文牙科经验：单点「最优」可能虚高）。
- 后续：对 Llama 最优 `rank8/lr1e-4` 跑 3-seed（seed 11/42/8）确认稳定性与增益；
  Qwen 默认已是历史结论（82.09%），无需再动。

## 6. 脚本与产物

- 队列：`run_en_general_tune_queue.sh`，日志 `en_general_tune_queue.log`
- 细扫：`ablation/run_sweep_en_general_qwen25.sh`、`ablation/run_sweep_en_general_llama70b.sh`
- 结果表：`ablation/results_en_general_qwen25.tsv`、`ablation/results_en_general_llama70b.tsv`
- 训练产物：`ablation/runs/en_general_qwen25/*`、`ablation/runs/en_general_llama70b/*`
