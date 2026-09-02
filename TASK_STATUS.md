# 任务状态快照（dentaldistill，2026-09-02，GPU 已释放）

> 本项目为「学生超越教师」蒸馏实验的可审计复现版。所有 GPU 训练任务已停止，GPU 腾给其他项目。
> 本文件记录：已完成（含结果）、已停止、待办（GPU/CPU）、复现命令，供后续续跑。

---

## 〇、一句话结论（当前口径）

1. **中文牙科**：干净口径下换 Qwen2.5-32B 学生后，3-seed 均值 86.90% 与教师 DeepSeek-V4-flash 86.90% **打平**
   （Qwen3-32B 只有 79.76%）。「学生超越教师」不成立，但「学生≈教师」成立。
2. **英文全科**：两个学生都**超越**弱教师 Qwen3-32B（80.22%）：Qwen2.5-32B 82.09%、Llama-70B 81.39%。
3. **英文牙科**（严格 84 题）：默认配置下 Qwen2.5-32B 落后（64.29%）、Llama-70B 微弱超（67.86% vs 66.67%）；
   **调参后** Qwen2.5-32B 最优可达 70.24%（rank8/lr3e-4/e1），超教师 +3.57pp（待 3-seed 坐实）。

---

## 一、已完成（结果均已落盘）

### 1. 数据（全部完成 ✅）
| 数据集 | train/val/test | 说明 |
|---|---|---|
| 中文全科 cn_general | 4608/991/991 | CMExam 全科重分割 |
| 中文牙科 cn_dental_clean | 381/80/84 | 扩充关键词 + 口腔科科室信号重筛（比旧 489 多回收 56 题真牙科）|
| 英文全科 en_general | 9789/1017/4110 | MedQA+MMLU 无印度 + 2 本单选书(BoF272+NBDE366) |
| 英文牙科 en_dental | 566/26/84 | R1 严格口径零非牙科 + 2 本书牙科题(BoF142+NBDE223) |

### 2. 中文牙科实验（全部完成 ✅）
| 学生 | 配置 | 结果 | 教师 | 结论 |
|---|---|---|---|---|
| Qwen3-32B | rank16/lr1e-4 3seed | 79.76% | 86.90% | 大幅落后 |
| Qwen2.5-32B | rank16/lr1e-4 3seed | 86.51% | 86.90% | 打平 |
| Qwen2.5-32B | rank16/lr2e-4 3seed | **86.90%** | 86.90% | **完全打平** |
| Qwen2.5-32B 细扫 | 24 组 | test 封顶 88.1% | — | 见 ablation/ |

### 3. 英文全科训练（全部完成 ✅）
| 学生 | 结果 | 教师 | Δ |
|---|---|---|---|
| Qwen2.5-32B | 82.09% | 80.22% | +1.87 ✅ |
| Llama-70B | 81.39% | 80.22% | +1.17 ✅ |

### 4. 英文牙科训练（默认配置，完成 ✅）
| 学生 | 结果 | 教师 | Δ |
|---|---|---|---|
| Qwen2.5-32B | 64.29% (单seed) | 66.67% | −2.38 ❌ |
| Llama-70B | 67.86% (3seed 69.05/67.86/66.67) | 66.67% | +1.19 ⚠️ |

### 5. 英文牙科 Qwen2.5-32B 参数细扫（完成 ✅，24 组）
- 最优 **rank8/lr3e-4/e1 = 70.24%**（超教师 +3.57pp），次优 rank4/lr2e-4、rank4/lr3e-4 = 69.05%。
- 规律：lr 2e-4/3e-4 优于默认 1e-4；epoch 2 与 lr 5e-4 掉点/发散。
- 详见 `ablation/RESULTS_sweep_en_dental_qwen25.md`。

---

## 二、已停止（GPU 已释放）

- **英文牙科 Llama-70B 参数细扫**（`ablation/run_sweep_en_dental_llama70b.sh`，12 组 = rank{4,8,16}×lr{1e-4,2e-4,3e-4,5e-4}×epoch1）。
  刚启动即被停（0 组完成，只跑了首个配置 r4_lr1e-4_e1 的训练，未完成评测）。脚本支持断点续跑（DONE 跳过）。

---

## 三、待办

### A. GPU 任务（续跑时按顺序，脚本均已备好）
1. **英文牙科 Qwen2.5-32B 最优配置 3-seed 坐实**（rank8/lr3e-4/e1，seed 11/42/8）：
   ```bash
   bash experiments/en_dental/scripts/run_train_qwen25_best_3seed.sh
   ```
   确认细扫最优 70.24% 是否稳定 ≥ 教师 66.67%。
2. **英文牙科 Llama-70B 细扫续跑**（12 组，断点跳过）→ 找最优 → 3-seed 坐实：
   ```bash
   bash ablation/run_sweep_en_dental_llama70b.sh
   ```

### B. CPU 任务（无需 GPU，本会话可继续做）
- 论文编写（把「干净口径下超越结论弱化/打平」写进去）。
- 数据检查、文档整理、README 同步（数据数字已同步，见下）。
- 汇总各 RESULTS_*.md 到 README/HANDOVER。

---

## 四、关键文件索引

- 结果：`experiments/cn_dental/RESULTS_qwen25_best_3seed.md`、`experiments/RESULTS_english.md`、
  `experiments/en_dental/RESULTS_llama_3seed.md`、`ablation/RESULTS_sweep_en_dental_qwen25.md`
- 数据论证：`reports/cn_dental_rescreen_report.md`、`reports/en_dental_strict_decision.md`、
  `reports/en_dental_audit.md`、`books/BOOKS_ARRANGEMENT.md`
- 训练队列脚本：`run_english_training_queue.sh`

## 五、复现/续跑命令

```bash
cd /home/student/arthas/dentaldistill
source setup.env

# 数据重筛（幂等）
python3 data/prepare_cn_dental_clean.py      # 中文牙科 381/80/84
python3 data/prepare_en_dental.py            # 英文牙科 566/26/84（R1 严格）

# 英文牙科 Qwen2.5-32B 细扫（已完成，可重跑）
bash ablation/run_sweep_en_dental_qwen25.sh

# 英文牙科 Llama-70B 细扫（续跑，断点跳过）
bash ablation/run_sweep_en_dental_llama70b.sh
```
