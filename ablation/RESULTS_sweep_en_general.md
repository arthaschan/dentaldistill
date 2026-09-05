# 英文全科（en_general）参数细扫结果

> 网格：rank{8,16} × lr{1e-4,2e-4,3e-4} × epoch{1} = 6 组/学生，α=0，seed=42（单 seed）。
> 数据：data/en_general/（train 9789 / val 1017 / test 4110，MedQA+MMLU 无印度 + 2 本单选书）。
> 教师 Qwen3-32B 零样本基线 = 80.22%（test 4110）。
> 复现：bash ablation/run_sweep_en_general_qwen25.sh 与 run_sweep_en_general_llama70b.sh
> 结果表：ablation/results_en_general_qwen25.tsv、results_en_general_llama70b.tsv

---

## 1. Qwen2.5-32B（默认 rank16/lr1e-4 = 82.09%）

| rank | lr | test_acc | vs 默认 |
|---|---|---|---|
| 16 | 1e-4 | **82.41** | —（=默认，最优）|
| 8  | 1e-4 | 82.29 | −0.12 |
| 8  | 2e-4 | 82.29 | −0.12 |
| 16 | 2e-4 | 81.70 | −0.71 |
| 8  | 3e-4 | 81.12 | −1.29 |
| 16 | 3e-4 | 79.59 | −2.82 |

**结论：默认配置即最优，调参无收益；lr3e-4 掉点。6 组全部稳定。**

## 2. Llama-70B（默认 rank16/lr1e-4 = 81.39%）

| rank | lr | test_acc | 状态 |
|---|---|---|---|
| 8  | 1e-4 | **82.75** | ✅ 最优 |
| 8  | 2e-4 | 80.83 | ✅ |
| 8  | 3e-4 | 77.83 | ✅ |
| 16 | 1e-4 | 81.61 | ✅（首跑 NaN 崩，重跑正常）|
| 16 | 2e-4 | 24.43 | ❌ 发散（≈随机）|
| 16 | 3e-4 | 0.0  | ❌ 发散（彻底崩坏）|

**结论：rank8 更稳且 rank8/lr1e-4 最优（82.75%）；rank16（默认）在 lr2e-4/lr3e-4 下训练发散。**

## 3. 关键发现

1. **Llama-70B QLoRA 在 9789 条大集上 rank16 数值不稳定**：
   - rank16/lr2e-4 → test 24.43%（≈随机）；rank16/lr3e-4 → test 0.0%（崩坏）；
   - rank16/lr1e-4 首跑也 loss→NaN 崩过一次（重跑 81.61%）。
   - **rank8 三组全部稳定**，是更安全的选择。
2. **Qwen2.5-32B 与 Llama-70B 的 lr 敏感度相反**：Qwen 对 lr 不敏感（1e-4/2e-4 都在 82%+），
   Llama 高 lr 直接发散（rank16 下 2e-4/3e-4 崩坏）。
3. 两个学生最优配置均稳定超弱教师 80.22%（Qwen +2.19、Llama +2.53）。

## 4. ⚠️ 单 seed 与 selection-on-test

- 本细扫为单 seed（seed42）+ 在 test 4110 上选优。4110 题的标准误约 ±0.6pp，
  故 rank8 vs rank16 的 ~1.3pp 差距仍需 **3-seed 坐实**。
- 已启动：`experiments/en_general/scripts/run_train_llama_best_3seed.sh 8 1e-4`（seed 11/42/8）。
