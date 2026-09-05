# 中文全科（cn_general）汇报

> 场景：中文全科（通用医学）选择题，学生超越教师蒸馏实验。教师 = DeepSeek-V4-flash（API），学生 = Qwen2.5-14B。

---

## 1. 数据

| 集合 | 条数 | 来源 |
|---|---|---|
| train | 4608 | CMExam 全科重分割（直接拷贝 mentalDistill 15 划分）|
| val | 991 | CMExam |
| test | 991 | CMExam |

## 2. 训练参数

- Choice-Head 蒸馏，α=0；LoRA rank16/alpha32；lr 1e-4；batch 1×8；1 epoch；3 seed（11/42/8）。

## 3. 结果

教师 DeepSeek-V4-flash 零样本 = **87.18%**（test 991）。

| seed | val acc | test acc |
|---|---|---|
| 11 | 90.11% | 89.51% |
| 42 | 89.00% | 88.80% |
| 8  | 88.40% | 88.60% |
| **均值** | **89.17%** | **88.97%** |

## 4. 结论

1. **中文全科是「学生超越教师」稳定成立的场景之一**：
   - 本次 test 均值 **88.97%**，比教师 DeepSeek-V4-flash 87.18% 高 **+1.79pp**（3 seed 全部高于教师）。
   - 与历史 mentalDistill 15 口径一致（学生 88.67% vs 教师 87.18%，+1.49pp）。
2. 与牙科场景（中/英牙科均打平）形成对比：**全科大样本（991 test）下学生稳定超越弱教师**。

## 5. 四场景总览（对照）

| 场景 | 教师 | 学生 | 结论 |
|---|---|---|---|
| **中文全科(991)** | DeepSeek 87.18% | Qwen2.5-14B **88.97%** | **超越 +1.79 ✅** |
| 中文牙科(84 干净) | DeepSeek 86.90% | Qwen2.5-32B 86.90% | 打平 |
| 英文全科(4110) | Qwen3-32B 80.22% | Qwen2.5-32B 82.09% / Llama 81.39% | 超越 ✅ |
| 英文牙科(84 严格) | Qwen3-32B 66.67% | Qwen2.5-32B 66.27% / Llama 67.06% | 打平 |

> 核心：干净口径下，「学生超越教师」在**全科（中/英）**成立，在**牙科（中/英）**弱化为「打平」。

## 6. 复现

```bash
cd /home/student/arthas/dentaldistill && source setup.env
python3 data/prepare_cn_general.py
bash experiments/cn_general/scripts/run_train.sh
```

## 7. 关键文件

- 结果：`experiments/cn_general/RESULTS.md`、`experiments/cn_general/README.md`
- 训练产物：`experiments/cn_general/runs/14B_a00_s{11,42,8}/`
