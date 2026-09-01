# HANDOVER — 交接/审计文档（供其他 AI 或人类审计本实验）

> 目的：让一个不参与本项目的 AI（或人）能在只读本仓库的情况下，核对"数据来源、数据条数、实验参数、牙科判定、实验结论"是否自洽、可复现。

---

## 0. 一句话结论

本仓库把 4 个"学生超越教师"的蒸馏实验（中文全科 / 中文牙科 / 英文全科 / 英文牙科）从 `mentalDistill` 重建成干净、可审计的版本。核心机制结论：**学生能否超越教师，等价于"教师零样本领先幅度 headroom < 蒸馏增益 gain"**。

---

## 1. 实验与关键数字（审计起点）

| 场景 | 老师 | 学生 | train/val/test | 历史结果（mentalDistill 口径） |
|---|---|---|---|---|
| 中文全科 | DeepSeek-V4-flash | Qwen2.5-14B | 4608/991/991 | 学生 88.67% vs 老师 87.18%（+1.49） |
| 中文牙科 | DeepSeek-V4-flash | Qwen3-32B | 580/125/125 | 学生 82.40%±0.80 vs 老师 79.20%（+3.20，3-seed 全超） |
| 英文全科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | 9151/1017/4110 | 82.19% / 82.09% vs 80.22%（+1.97/+1.87） |
| 英文牙科 | Qwen3-32B | Qwen2.5-32B / Llama-3.3-70B | 待书籍并入 | **旧结果作废**（见 §5 oral 误判） |

> 注意：英文牙科的旧结果（75.65%/80.64% vs 72.46%）是在被 "oral" 污染的 501 题测试集上算的，本仓库**作废并重做**。

---

## 2. 训练参数（四场景统一）

- Choice-Head 蒸馏，α=0（纯标准答案监督，不用教师软标签）
- LoRA rank 16 / alpha 32；学习率 1e-4；batch 1 × 梯度累积 8；1 epoch
- 唯一差异：Llama-3.3-70B 用 QLoRA 4bit（显存）；中文牙科用 3 seed（11/42/8），英文用 seed 42

**在哪核对**：每个 `experiments/<场景>/scripts/run_train.sh` 的命令行参数（`--rank 16 --lora_alpha 32 --learning_rate 1e-4 --batch_size 1 --gradient_accumulation_steps 8 --num_epochs 1 --alpha 0.0`）。训练入口 `shared/train_choice_head_distill.py` 只解析+套用这些参数（其 argparse 默认值与实际不同，勿以默认值为准）。

---

## 3. 数据来源与条数（审计方法）

见 `data/README.md` 第 2 节。审计口令：

```bash
wc -l data/<场景>/train.jsonl data/<场景>/val.jsonl data/<场景>/test.jsonl
```

中文数据来自 CMExam（学科字段「口腔医学」），英文来自 MedQA/MMLU（无印度 MedMCQA）。3 本教材（Best of Fives / NBDE / MCQs for Dentistry）见 `books/`。

---

## 4. 牙科判定与检查工具（本仓库核心）

**判定规则**（`data/dental_filter.py` 顶部 docstring）：
- D1 中文学科 `Medical Discipline == "口腔医学"`；
- D2 英文学科 `subject == "Dental"`（MedMCQA）；
- R1 强牙科关键词（tooth/dental/caries/enamel/pulp/periodont/…）；
- R2 "oral" 仅限口腔语境（oral cavity / oral mucosa / oral health / oral cancer / …）；
- **裸 "oral"（口服）与裸 "mucosa"/"crown" 不算牙科**。

**审计工具**：

```bash
python3 data/check_dental_subset.py data/cn_dental/test.jsonl     # 应 [PASS]
python3 data/check_dental_subset.py data/en_dental/test.jsonl     # 应 [PASS]
```

输出每题命中明细（命中了哪条规则/哪个词），非牙科题会显式列出并给理由。退出码 0=全牙科。

---

## 5. 关键背景：旧 "oral" 误判（必须了解）

旧 mentalDistill 英文牙科子集用 `\boral\b` 关键词，把"oral = 口服"的题误判成牙科。实测旧 501 题牙科测试集里 **311 道非牙科**（口服避孕药/oral morphine/decreased oral intake 等），只剩 190 道真牙科。本仓库用收紧判定重建，英文牙科（MedQA+MMLU）现为 train 219 / val 26 / test 85，并靠 3 本书扩充。

---

## 6. 复现与验证清单（AI 审计 checklist）

- [ ] `data/prepare_*.py` 可运行，输出条数与 `data/README.md` 一致
- [ ] `data/check_dental_subset.py` 对牙科三集均 [PASS]
- [ ] `experiments/<场景>/scripts/run_train.sh` 参数与 §2 一致
- [ ] 训练产物在 `experiments/<场景>/runs/`（gitignored），评测脚本可复现结果
- [ ] 消融（`ablation/`）验证 α=0 / rank16 / lr1e-4 是否最优

---

## 7. 待办（交接给下一轮）

- [ ] 移植 `shared/train_choice_head_distill.py` 到 `shared/`
- [ ] 各 `experiments/<场景>/` 的 run_train/run_eval 脚本 + README
- [ ] `books/` 提取 3 本教材并并入英文牙科数据
- [ ] `ablation/` 消融实验
- [ ] 在 GPU 环境重跑训练/评估，落地本仓库自己的数字
