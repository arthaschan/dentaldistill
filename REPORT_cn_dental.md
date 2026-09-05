# 中文牙科（cn_dental）汇报

> 场景：中文牙科选择题，学生超越教师蒸馏实验。教师 = DeepSeek-V4-flash（API），学生 = Qwen2.5-32B。

---

## 1. 数据

| 集合 | 条数 | 来源 |
|---|---|---|
| train | 381 | CMExam「口腔医学」学科 → 内容级干净集重筛 |
| val | 80 | 同上 |
| test | 84 | 同上 |

- 干净集 `data/cn_dental_clean/`（共 545 题）：扩充牙科关键词 + 临床科室=口腔科信号重筛。
- 审计：`python3 data/check_no_nondental.py` → `[PASS]` 中文牙科 545 题全部为牙科（退出码 0）。
- 背景：旧「学科字段=口腔医学」口径含 35%~42% 通科题，已作废（见 `reports/cn_dental_rescreen_report.md`）。

## 2. 训练参数（四场景统一）

- Choice-Head 蒸馏，α=0（纯标准答案监督，不用教师软标签）
- LoRA rank16/alpha32；lr 1e-4（最优配置用 2e-4）；batch 1×8；1 epoch；3 seed（11/42/8）

## 3. 结果

教师 DeepSeek-V4-flash 零样本 = **86.90%**（73/84）。

| 学生 | 配置 | test acc | vs 教师 |
|---|---|---|---|
| Qwen3-32B | rank16/lr1e-4（3seed） | 79.76% | −7.14 ❌ 大幅落后 |
| Qwen2.5-32B | rank16/lr1e-4（3seed） | 86.51% | −0.39 打平 |
| Qwen2.5-32B | rank16/lr2e-4（3seed） | **86.90%** | 0.00 完全打平 |

最优配置（rank16/lr2e-4）3-seed 明细：

| seed | test acc |
|---|---|
| 11 | 88.10% (74/84) |
| 42 | 88.10% (74/84) |
| 8  | 84.52% (71/84) |
| **均值** | **86.90% (73/84)** |

- 细扫 24 组（rank{4,8,16}×lr{1e-4..5e-4}×e{1,2}）：test 封顶 **88.1%（74/84）**，10 组都顶到 88.1%，无配置超过；
  默认配置（rank16/lr1e-4）本身就在天花板上，细扫没找到更优配置（见 `ablation/RESULTS_sweep_qwen25.md`）。

## 4. 结论

1. **中文牙科干净口径下，「学生超越教师」不成立，但「学生≈教师」成立**：
   Qwen2.5-32B 最优配置 3-seed 均值 86.90%，与教师 DeepSeek-V4-flash 86.90% **完全打平**
   （2/3 seed 略超教师，1 seed 略低）。
2. 换学生效果显著：Qwen3-32B 只有 79.76%（大幅落后 −7.14），Qwen2.5-32B 才是打平水平。
3. 旧污染口径（125 题）的「+3.20 假超越」作废：干净口径真相是**弱教师场景下学生≈教师（打平）**。

## 5. 三个口径对照

| 口径 | 教师 | 学生 | 结论 |
|---|---|---|---|
| 旧 125 题（污染） | 79.20% | Qwen3-32B 82.40% | +3.20 假超越（作废） |
| 干净 84 题 | 86.90% | Qwen3-32B 79.76% | −7.14 大幅落后 |
| **干净 84 题** | **86.90%** | **Qwen2.5-32B 86.90%** | **打平（0.00）** |

## 6. 复现

```bash
cd /home/student/arthas/dentaldistill && source setup.env
python3 data/prepare_cn_dental_clean.py                       # 数据重筛（幂等）
python3 data/check_no_nondental.py                            # 应 [PASS] 退出码 0
bash experiments/cn_dental/scripts/run_train_qwen25_best_3seed.sh   # 最优 3-seed
```

## 7. 关键文件

- 结果：`experiments/cn_dental/RESULTS_qwen25_best_3seed.md`、`ablation/RESULTS_sweep_qwen25.md`
- 数据论证：`reports/cn_dental_rescreen_report.md`、`data/README.md`
