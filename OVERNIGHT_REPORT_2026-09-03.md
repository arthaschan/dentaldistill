# 夜间执行报告 — dentaldistill（2026-09-03 早上交付）

> 承接 `TASK_STATUS.md` / `HANDOVER.md` 交接内容，本报告记录本次会话「接着执行任务」的完整过程与结果。
> 一句话结论见文末 §6，详细过程逐节说明。

---

## 1. 承接的任务（交接内容回顾）

上次交接留下的**两项 GPU 待办**（其余数据/实验均已完成落盘）：

| # | 任务 | 脚本 | 目标 |
|---|---|---|---|
| A | 英文牙科 Qwen2.5-32B 最优配置 **3-seed 坐实**（rank8/lr3e-4/e1） | `experiments/en_dental/scripts/run_train_qwen25_best_3seed.sh` | 确认细扫单 seed 70.24% 是否稳定 ≥ 教师 66.67% |
| B | 英文牙科 **Llama-70B 细扫续跑**（12 组）→ 找最优 → 3-seed 坐实 | `ablation/run_sweep_en_dental_llama70b.sh` | 找 Llama 最优配置并坐实 |

交接还说明：上次 GPU 已释放，本次续跑需在 GPU 空闲时进行。

---

## 2. 环境与数据核验（本次会话实测）

### 2.1 GPU
- `nvidia-smi`：**NVIDIA H100 NVL，95GB**，会话开始时空闲（0% 利用率、14 MiB 已用）。
- 结论：GPU 已重新空闲，可以直接续跑两项 GPU 待办。

### 2.2 模型与工具链
- Python：`/home/student/anaconda3/bin/python3`（3.12.7）✅
- 模型路径（`setup.env`）：Qwen2.5-32B-Instruct、Llama-3.3-70B-Instruct、Qwen3-32B 均在位 ✅
- 磁盘：可用 280G，足以容纳全部 adapter/checkpoint ✅

### 2.3 数据条数（与交接口径一致）
| 数据集 | train/val/test | 合计 |
|---|---|---|
| cn_general | 4608/991/991 | 6590 |
| cn_dental_clean | 381/80/84 | 545 |
| en_general | 9789/1017/4110 | 14916 |
| en_dental | 566/26/84 | 676 |

> 注：交接 HANDOVER §4 审计口令写的是 `data/cn_dental/test.jsonl`（旧未清洗 125 题），
> 实际规范数据在 `data/cn_dental_clean/`（84 题）。本次审计已按干净集口径执行。

### 2.4 数据审计（全部 PASS，退出码 0）
- `data/check_no_nondental.py` → `[PASS] 中文牙科 545 题 + 英文牙科 676 题，全部为牙科，无非牙科数据`（rc=0）
- `data/check_dental_subset.py data/cn_dental_clean/test.jsonl` → `[PASS]` 84/84 牙科（rc=0）
- `data/check_dental_subset.py data/en_dental/test.jsonl` → `[PASS]` 84/84 牙科（rc=0）

---

## 3. 执行过程

### 3.1 补完上次被打断的 Llama-70B 细扫首配置
上次 `run_sweep_en_dental_llama70b.sh` 刚跑完 `r4_lr1e-4_e1` 的训练即被停（无 DONE、无评测、无结果行）。
本次补完其评测并回填结果：

| rank | lr | epoch | val_acc | test_acc |
|---|---|---|---|---|
| 4 | 1e-4 | 1 | 88.46 | 63.1 |

> 该配置 test 63.1% **低于**教师 66.67%，与 Qwen2.5 细扫「lr1e-4 偏弱」的规律一致。

### 3.2 无人值守队列（后台执行，已完成 ✅）
新增 `run_overnight_queue.sh`（根目录），按顺序串行执行：

- **Phase A**：Qwen2.5-32B rank8/lr3e-4/e1 3-seed（seed 11/42/8）
- **Phase B**：Llama-70B 细扫（rank{4,8,16}×lr{1e-4,2e-4,3e-4,5e-4}×e1，断点跳过，r4_lr1e-4_e1 已跳过）
- **Phase C**：按 Phase B 结果自动取 test_acc 最优配置 → Llama-70B 3-seed 坐实
  （新增 `experiments/en_dental/scripts/run_train_llama_best_3seed.sh`，参数化 `<rank> <lr>`）

队列日志：`overnight_queue.log`（根目录）。启动时间 2026-09-02 23:11。

### 3.3 队列执行结果（详见 §4 / §5）

---

## 4. Phase A 结果：Qwen2.5-32B 最优配置 3-seed（已完成 ✅）

> 配置：rank8 / lr3e-4 / 1 epoch / α=0 / lora_alpha=16，seed(11/42/8)。
> 教师 Qwen3-32B 零样本基线 = **66.67%**（56/84，test 84）。

| seed | val_acc | test_acc |
|---|---|---|
| 11 | 50.00% | 65.48% (55/84) |
| 42 | 53.85% | 69.05% (58/84) |
| 8  | 53.85% | 64.29% (54/84) |
| **均值** | — | **66.27% (55.67/84)** |

**结论：细扫的「70.24% 超教师 +3.57pp」不可复现。**

- 细扫单 seed(42) = 70.24%，但 3-seed 重跑同配置（seed 42 也重跑）得 69.05%，均值 **66.27% ≈ 教师 66.67%（−0.40pp，打平）**。
- 同配置、同 seed、同 `--deterministic`，重跑仍从 70.24% 漂到 69.05%：说明存在 GPU 非确定性的 run-to-run 方差。
- 更根本的问题：细扫是**在 test 集上选最优**（见 §5 注），70.24% 属「对测试集选择」+ 小样本噪声，本就虚高。
- **英文牙科 Qwen2.5-32B：无论默认配置还是最优配置，3-seed 都不稳定超越教师，最多打平（66.27% ≈ 66.67%）。**

> 注意：val（26 题）与 test（84 题）几乎不相关（如 rank8/lr3e-4/e1 val=53.85 却 test=70.24），
> val 太小无法用于模型选择——这也是细扫只能「在 test 上挑」的根因。

---

## 5. Phase B / C 结果：Llama-70B 细扫 + 3-seed

### 5.1 Phase B 细扫（12 组，已完成 ✅）

> 网格：rank{4,8,16} × lr{1e-4,2e-4,3e-4,5e-4} × epoch1，α=0，seed=42，QLoRA 4bit。
> 教师 Qwen3-32B 零样本 = 66.67%（56/84）。

| rank | lr | val_acc | test_acc | vs 教师 |
|---|---|---|---|---|
| 16 | 1e-4 | 92.31 | **69.05** | **+2.38 ✅** |
| 4 | 2e-4 | 88.46 | 67.86 | +1.19 ✅ |
| 8 | 2e-4 | 92.31 | 67.86 | +1.19 ✅ |
| 8 | 3e-4 | 92.31 | 65.48 | −1.19 |
| 8 | 1e-4 | 88.46 | 64.29 | −2.38 |
| 4 | 3e-4 | 92.31 | 64.29 | −2.38 |
| 4 | 1e-4 | 88.46 | 63.10 | −3.57 |
| 4 | 5e-4 | 69.23 | 63.10 | −3.57 |
| 16 | 2e-4 | 84.62 | 63.10 | −3.57 |
| 16 | 3e-4 | 80.77 | 58.33 | −8.33 |
| 16 | 5e-4 | 73.08 | 55.95 | −10.71 |
| 8 | 5e-4 | 88.46 | 55.95 | −10.71 |

**关键观察：**

1. 细扫在 test 上选的「最优」是 **r16/lr1e-4 = 69.05%**，而这一组恰是**默认配置**。
2. 默认配置的 3-seed 之前已跑过（`Llama70B_a00_s{11,42,8}`）：69.05 / 67.86 / 66.67 → **均值 67.86%**。
   本次细扫同一 seed=42 得 69.05%，与早前 3-seed 的 seed42=67.86% 相差 ~1.2pp → 再次印证 run-to-run 方差。
3. Llama 的 lr 规律与 Qwen2.5 相反：**lr 越大越差**（lr5e-4 掉到 55.95/55.95），lr1e-4/2e-4 最好。
4. 所有 12 组 test 在 55.95–69.05 之间，84 题 ±~5pp 噪声内，**单点「最优」不可靠**。

### 5.2 Phase C 结果：Llama-70B 最优（r16/lr1e-4）3-seed（已完成 ✅）

> 细扫在 test 上选的「最优」= r16/lr1e-4 = 默认配置。跑了一轮全新 3-seed（seed 11/42/8）。

| seed | val_acc | test_acc |
|---|---|---|
| 11 | 92.31% | 67.86% (57/84) |
| 42 | 88.46% | 64.29% (54/84) |
| 8  | 88.46% | 66.67% (56/84) |
| **均值** | — | **66.27% (55.67/84)** |

**与早前默认 3-seed（`Llama70B_a00_s{11,42,8}`）对照：**

| 轮次 | seed 11 | seed 42 | seed 8 | 均值 |
|---|---|---|---|---|
| 第 1 轮（早前 a00） | 69.05% | 67.86% | 66.67% | 67.86% |
| 第 2 轮（本次 r16） | 67.86% | 64.29% | 66.67% | 66.27% |
| **两轮合并 6 seed** | — | — | — | **67.06%（338/504）** |

**结论：Llama-70B 的「+1.19pp 超越」同样不可复现。**

- 同一默认配置，两轮 3-seed 均值分别为 67.86% 与 66.27%，一个在教师之上、一个在教师之下。
- 合并 6 seed = 67.06%，与教师 66.67% 相差 **+0.40pp（≈1 题），纯噪声**。
- 即英文牙科上 **Llama-70B 也是「打平教师」，不是稳定超越**。

---

## 6. 结论（本次执行的最终结论）

### 6.1 英文牙科（本次完成的核心任务）——「学生超越教师」不成立

严格 84 题，教师 Qwen3-32B 零样本 = 66.67%（56/84）：

| 学生 | 配置 | 关键数字 | 均值 | vs 教师 |
|---|---|---|---|---|
| Qwen2.5-32B | 默认 rank16/lr1e-4 | 单 seed 64.29% | 64.29% | −2.38 ❌ |
| Qwen2.5-32B | 细扫最优 rank8/lr3e-4 | 65.48/69.05/64.29（3seed） | 66.27% | −0.40（打平） |
| Llama-70B | 默认 rank16/lr1e-4 | 67.86% / 66.27%（两轮各 3seed） | 67.06%（6seed） | +0.40（打平） |

- 细扫单点 **70.24%（+3.57）不可复现**：同配置 3-seed 均值 66.27%，与教师打平。
- Llama 的 **+1.19 也不可复现**：两轮 3-seed 均值分别为 67.86% / 66.27%，合并 67.06%，在教师 ±0.4pp 噪声内。
- **两个学生最终都「打平教师」，无稳定超越。**

### 6.2 全局叙事（四场景汇总，结合既有结果）

| 场景 | 教师 | 学生 | 结论 |
|---|---|---|---|
| 中文牙科(84 干净) | DeepSeek 86.90% | Qwen2.5-32B 86.90%（3seed） | 打平 |
| 英文全科(4110) | Qwen3-32B 80.22% | Qwen2.5-32B 82.09% / Llama-70B 81.39% | **双超越 ✅** |
| 英文牙科(84 严格) | Qwen3-32B 66.67% | Qwen2.5-32B 66.27% / Llama-70B 67.06% | **打平（本次坐实，撤销原「超越」）** |
| 中文全科 | DeepSeek 87.18% | Qwen2.5-14B 88.67%（历史） | 本仓库未重跑 |

> **核心一句话：在干净、严格口径下，「学生超越教师」只在英文全科（4110 题大样本 + 弱教师）成立；**
> **中/英牙科两个场景均为「学生≈教师（打平）」，历史口径下的「超越」被撤销。**

### 6.3 方法论结论（供论文/复现）

1. **val 集（26 题）太小**，与 test 几乎不相关 → 无法用 val 做模型选择，细扫只能「在 test 上挑」，
   单点「最优」是 selection-on-test，系统性虚高。
2. **run-to-run 方差 ~1–2pp**（即便开 `--deterministic`），84 题上「±1 题」没有统计意义。
3. 小样本下必须 **3+ seed + 独立复跑**才能下结论；本次正是靠「同配置独立复跑」戳破了
   Qwen 的 +3.57 与 Llama 的 +1.19。

---

## 7. 新增/修改文件

- `OVERNIGHT_REPORT_2026-09-03.md`（本报告）
- `run_overnight_queue.sh`（新增，夜间队列驱动）
- `experiments/en_dental/scripts/run_train_llama_best_3seed.sh`（新增，Llama 参数化 3-seed）
- `ablation/RESULTS_sweep_en_dental_llama70b.md`（新增，Llama 细扫结果汇总）
- `ablation/results_en_dental_llama70b.tsv`（12 组结果全量）
- `ablation/runs/en_dental_llama70b/r4_lr1e-4_e1/DONE`（补标记）
- 训练产物：`experiments/en_dental/runs/32B_a00_r8_lr3e4_s{11,42,8}`、
  `ablation/runs/en_dental_llama70b/*`、`experiments/en_dental/runs/Llama70B_r16_lr1e-4_s{11,42,8}`

## 8. 复现本次结果的命令

```bash
cd /home/student/arthas/dentaldistill
source setup.env

# Qwen2.5-32B 最优配置 3-seed（Phase A）
bash experiments/en_dental/scripts/run_train_qwen25_best_3seed.sh

# Llama-70B 细扫（Phase B，断点跳过）
bash ablation/run_sweep_en_dental_llama70b.sh

# Llama-70B 最优配置 3-seed（Phase C，参数化）
bash experiments/en_dental/scripts/run_train_llama_best_3seed.sh 16 1e-4
```

> 全流程（A→B→C 自动串联）：`bash run_overnight_queue.sh`，日志 `overnight_queue.log`。
