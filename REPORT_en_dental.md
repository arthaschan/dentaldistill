# 英文牙科（en_dental）汇报

> 场景：英文牙科选择题，学生超越教师蒸馏实验。教师 = Qwen3-32B（开源弱教师），学生 = Qwen2.5-32B / Llama-3.3-70B。

---

## 1. 数据

| 集合 | 条数 | 来源 |
|---|---|---|
| train | 566 | MedQA + MMLU 牙科题（R1 严格）+ 2 本单选书（BoF 142 + NBDE 223）|
| val | 26 | 同上 |
| test | 84 | 同上 |

- R1 严格口径：强牙科关键词（tooth/dental/caries/enamel/pulp/periodont/…），裸 "oral"（口服）排除。
- 审计：`python3 data/check_dental_subset.py data/en_dental/test.jsonl` → `[PASS]` 84/84 牙科；`check_no_nondental.py` → `[PASS]`（退出码 0）。
- 背景：旧 mentalDistill 用 `\boral\b` 把「oral=口服」误判成牙科，旧 501 题里 311 道非牙科；本仓库收紧重做。

## 2. 训练参数

- Choice-Head 蒸馏，α=0；LoRA rank16/alpha32（默认）；lr 1e-4（默认）；batch 1×8；1 epoch。
- Llama-70B 用 QLoRA 4bit；中文牙科用 3 seed，英文牙科 seed 42。

## 3. 结果

教师 Qwen3-32B 零样本 = **66.67%**（56/84，test 84）。

| 学生 | 配置 | test acc | vs 教师 |
|---|---|---|---|
| Qwen2.5-32B | 默认 rank16/lr1e-4（单 seed） | 64.29% | −2.38 ❌ |
| Qwen2.5-32B | 细扫最优 rank8/lr3e-4（单 seed） | 70.24% | +3.57（不可复现，见下） |
| Qwen2.5-32B | 最优配置 **3-seed** | **66.27%** | −0.40 打平 |
| Llama-70B | 默认 rank16/lr1e-4（3-seed 第 1 轮） | 67.86% | +1.19（不可复现） |
| Llama-70B | 默认 **6-seed**（两轮各 3-seed） | **67.06%** | +0.40 打平 |

Qwen2.5-32B 最优配置（rank8/lr3e-4）3-seed 明细：

| seed | test acc |
|---|---|
| 11 | 65.48% (55/84) |
| 42 | 69.05% (58/84) |
| 8  | 64.29% (54/84) |
| **均值** | **66.27% (55.67/84)** |

Llama-70B 默认配置两轮 3-seed（6 seed）对照：

| 轮次 | seed 11 | seed 42 | seed 8 | 均值 |
|---|---|---|---|---|
| 第 1 轮 | 69.05% | 67.86% | 66.67% | 67.86% |
| 第 2 轮 | 67.86% | 64.29% | 66.67% | 66.27% |
| **合并** | — | — | — | **67.06%（338/504）** |

## 4. 结论

1. **英文牙科（严格 84 题）上，两个学生均「打平教师 66.67%」，无稳定超越：**
   - Qwen2.5-32B：细扫单点 70.24%（+3.57）**不可复现**，3-seed 均值 66.27%，与教师打平。
   - Llama-70B：默认配置两轮 3-seed 均值 67.86% / 66.27%，合并 67.06%，在教师 ±0.4pp 噪声内。
2. 原「Qwen 调参 +3.57」「Llama +1.19」均为单 seed/测试集选择 + 小样本（84 题 ±~5pp）噪声，**撤销**。
3. 与中文牙科同款现象：干净严格口径下，历史口径的「超越」弱化为「打平」。

## 5. 细扫结果（已全量完成）

- Qwen2.5-32B 24 组（rank{4,8,16}×lr{1e-4..5e-4}×e{1,2}）：最优单点 rank8/lr3e-4 = 70.24%（见 `ablation/RESULTS_sweep_en_dental_qwen25.md`）。
- Llama-70B 12 组（rank{4,8,16}×lr{1e-4..5e-4}×e1）：最优单点 = 默认 rank16/lr1e-4 = 69.05%（见 `ablation/RESULTS_sweep_en_dental_llama70b.md`）。

## 6. 方法论发现（供论文）

- val（26 题）太小，与 test 几乎不相关 → 无法用 val 做模型选择，细扫只能「在 test 上挑」，单点最优虚高。
- run-to-run 方差 ~1–2pp（即便 `--deterministic`），84 题上「±1 题」无统计意义；必须 3+ seed + 独立复跑。

## 7. 复现

```bash
cd /home/student/arthas/dentaldistill && source setup.env
python3 data/prepare_en_dental.py                              # 数据（R1 严格）
python3 data/check_dental_subset.py data/en_dental/test.jsonl  # 应 [PASS]
bash experiments/en_dental/scripts/run_train_qwen25_best_3seed.sh  # Qwen 最优 3-seed
bash ablation/run_sweep_en_dental_llama70b.sh                  # Llama 细扫
```

## 8. 关键文件

- 结果：`experiments/en_dental/RESULTS_llama_3seed.md`、`ablation/RESULTS_sweep_en_dental_qwen25.md`、`ablation/RESULTS_sweep_en_dental_llama70b.md`
- 夜间坐实过程：`OVERNIGHT_REPORT_2026-09-03.md`
- 数据论证：`reports/en_dental_strict_decision.md`、`reports/en_dental_audit.md`
