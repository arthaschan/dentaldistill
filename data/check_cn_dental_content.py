#!/usr/bin/env python3
"""中文牙科子集内容级检测 —— 不只靠「学科字段」，而是逐题检查题目内容是否真牙科。

背景
----
`data/cn_dental/` 是按 `Medical Discipline == "口腔医学"` 从 CMExam 全科拆出来的。
但 CMExam 的「口腔医学」学科字段并非纯口腔题目（口腔医师资格考试也考基础医学、
药理学、儿科学等通科内容）。因此仅靠学科字段会漏掉「被打上口腔医学标签、但内容
是通科医学」的题。

本脚本对每题拼接 题干+选项+解析，用「中文强牙科关键词 + 英文学科字段/关键词」判定，
把「内容里没有任何牙科信号」的题显式列出，供人工逐题复核。

判定（内容级，任一命中即视为牙科信号）：
  C1  中文强牙科关键词（龋/牙髓/牙周/颌/牙龈/釉质/根管/口腔/义齿/正畸/咬合/氟牙/腭/…）
  C2  英文学科字段 subject=="Dental"
  C3  英文 R1 强牙科关键词 / R2 oral 口腔语境（复用 dental_filter）

注意：口腔医师资格考试的「药理学/儿科学/内科」通科题通常没有任何牙科关键词，
会被本脚本显式列出——这正是我们要找的「非牙科污染」。

用法
----
    python3 data/check_cn_dental_content.py [outdir=data/cn_dental] [--report 报告.md]

退出码：0=全部命中牙科信号；1=存在无牙科信号的题（需人工复核）。
"""
import json
import os
import sys
import re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dental_filter import is_dental_record, dental_match, question_text  # noqa: E402

# ---- 中文强牙科关键词（内容级）----
# 只收录「医学语境下几乎必然牙科」的词，避免误报：
#   - 不含裸「口」（口服/口腔给药）、「面」「舌」「唇」（中医舌诊/唇色）等歧义词
#   - 不含「种植」「修复」「冠」（种植转移/基因修复/冠心病）等，除非带牙科限定词
CN_STRONG = [
    # 牙体/牙髓/牙周
    "龋", "牙髓", "牙周", "牙体", "牙槽", "牙龈", "龈", "牙本质", "牙骨质", "釉质",
    "窝沟", "根管", "牙菌斑", "牙石", "牙垢", "牙髓炎", "牙周炎", "牙周病",
    "窝洞", "根尖", "根尖周", "牙髓病", "菌斑", "牙周袋", "龈下", "附着龈", "游离龈",
    "刮治", "含漱", "洗必泰", "塞治剂",
    # 牙/齿/颌（结构）
    "牙齿", "智齿", "乳牙", "恒牙", "磨牙", "切牙", "门牙", "尖牙", "前磨牙", "双尖牙",
    "阻生牙", "阻生齿", "多生牙", "牙", "齿", "颌", "颌骨", "颌面", "颌下", "颞下颌",
    "牙列", "牙颌", "反颌", "覆颌", "深覆", "开颌", "错颌",
    # 口腔及黏膜
    "口腔", "口腔黏膜", "口腔溃疡", "口腔卫生", "口腔保健", "腭", "腭裂", "唇腭裂",
    "颊黏膜", "舌系带", "口底", "阿弗他", "白斑", "毛状白斑",
    # 口腔黏膜病
    "口炎", "疱疹性口炎", "念珠菌性口炎", "口角炎", "扁平苔藓", "盘状红斑狼疮",
    # 舌（口腔解剖/黏膜，注意避开裸"舌"以排除中医舌诊）
    "舌下神经", "舌神经", "舌咽神经", "舌炎", "地图舌", "沟纹舌", "裂纹舌",
    "萎缩性舌炎", "剥脱性舌炎", "舌乳头", "轮廓乳头", "菌状乳头", "丝状乳头", "叶状乳头",
    "味蕾", "舌肌", "颏舌肌", "舌骨舌肌", "舌垂直肌", "舌横肌", "舌上纵肌", "舌下纵肌",
    "腭舌肌", "舌背", "舌腹",
    # 口腔颌面肿瘤（明确口腔部位）
    "舌癌", "颊癌", "唇癌", "腭癌", "牙龈癌", "口底癌",
    # 功能/治疗/修复
    "咬合", "义齿", "假牙", "正畸", "拔牙", "牙关", "洁牙", "补牙", "镶牙",
    "种植牙", "牙种植", "种植体",
    "银汞", "固定桥", "粘接桥", "桩冠", "烤瓷", "全冠", "嵌体", "贴面",
    "卡环", "隙卡沟", "冠桩", "印模", "取模", "藻酸盐", "硅橡胶", "聚醚橡胶",
    "琼脂", "局部义齿", "全口义齿", "牙列缺损",
    # 牙体牙髓治疗
    "活髓切断术", "盖髓剂", "塑化", "酚醛树脂", "髓室", "根髓", "冠髓",
    # 氟（仅限牙科语境）
    "氟牙", "氟斑", "氟化", "涂氟", "含氟", "氟骨症",
    # 唾液腺 / 神经（口腔颌面外科范围）
    "唾液腺", "涎腺", "涎石", "流涎", "面神经", "三叉神经",
    "腮腺", "下颌下腺", "舌下腺", "涎瘘", "分泌管", "闰管", "黏液囊肿", "黏液腺",
    "沃辛瘤", "腺淋巴瘤", "腺泡细胞癌", "多形性腺瘤", "混合瘤", "基底细胞腺瘤",
    "肌上皮瘤", "嗜酸性腺瘤",
    # 颌面外科：囊肿/畸形/肿瘤/感染
    "鳃裂", "鳃弓", "鳃瘘", "鳃沟", "鼻唇沟", "唇面沟", "颏唇沟", "鼻小柱",
    "鼻唇囊肿", "鼻牙槽囊肿", "鼻腭管囊肿", "甲状舌管囊肿", "皮脂腺囊肿", "皮样囊肿",
    "表皮样囊肿", "血管瘤", "脉管畸形",
    "唇痈", "危险三角", "海绵窦", "颌骨骨髓炎", "化脓性骨髓炎", "放射性骨坏死", "切开引流",
    # 颞下颌关节 / 咀嚼肌
    "翼外肌", "翼内肌", "关节盘", "髁突", "关节结节", "开口度", "弹响", "肌筋膜痛", "下关穴",
    # 胚胎/牙胚发育
    "牙胚", "原发性上皮带", "球状突", "中鼻突", "侧鼻突", "额鼻突", "成釉器", "牙板",
    "牙囊", "牙乳头",
    # 口腔黏膜组织病理
    "角化层", "棘细胞层", "粒层", "生发层",
]

_CN_STRONG_RE = re.compile("|".join(sorted(CN_STRONG, key=len, reverse=True)))


def cn_hits(text: str):
    """返回命中明细 [(规则, 词), ...]。空 = 无牙科信号。"""
    return [("C1", m.group(0)) for m in _CN_STRONG_RE.finditer(text)]


def content_signal(record: dict):
    """仅内容级信号（不含学科字段）：返回 [(规则, 词), ...]。空 = 内容里没有牙科信号。"""
    text = question_text(record)
    hits = []
    hits += cn_hits(text)
    # 英文关键词（MedQA/MMLU 混入中文集的情况）
    hits += dental_match(text)
    return hits


def discipline_signal(record: dict):
    """学科字段信号：返回 [(规则, 值), ...]。"""
    hits = []
    disc = record.get("Medical Discipline") or record.get("discipline") or ""
    if disc == "口腔医学":
        hits.append(("D1", disc))
    subj = record.get("subject") or record.get("subject_name") or ""
    if subj == "Dental":
        hits.append(("D2", subj))
    return hits


# 口腔相关临床科室（比「口腔医学」学科字段更细，经人工复核可靠）
CN_DENTAL_DEPTS = {"口腔科"}


def dept_signal(record: dict):
    """临床科室信号：Clinical Department 属于口腔相关科室时返回命中。"""
    dept = str(record.get("Clinical Department") or "").strip()
    if dept in CN_DENTAL_DEPTS:
        return [("D3", dept)]
    return []


def dental_signal(record: dict):
    """综合牙科信号 = 内容关键词(C1/C3) + 临床科室(D3)。

    用于「干净子集」筛选：内容里确有牙科词，或临床科室明确是口腔科
    （覆盖「口腔科但用了关键词表未覆盖专业术语」的边界题）。
    """
    return content_signal(record) + dept_signal(record)


def load_jsonl(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "cn_dental")
    report_path = None
    if "--report" in sys.argv:
        report_path = sys.argv[sys.argv.index("--report") + 1]

    print("=" * 70)
    print("中文牙科子集内容级检测（学科字段 + 内容关键词）")
    print("=" * 70)

    all_flags = []
    for name in ["train", "val", "test"]:
        path = os.path.join(outdir, f"{name}.jsonl")
        if not os.path.exists(path):
            continue
        rows = load_jsonl(path)
        content_silent, content_hit = [], []
        disc_counter = Counter()
        for r in rows:
            sig = content_signal(r)
            disc_counter[r.get("Medical Discipline", "?")] += 1
            if sig:
                content_hit.append(r)
            else:
                content_silent.append(r)
        print(f"\n[{name}] 共 {len(rows)} 题")
        print(f"  内容含牙科关键词 : {len(content_hit)}")
        print(f"  内容无牙科关键词 : {len(content_silent)}（仅靠学科字段=口腔医学，疑似非牙科通科题）")
        print(f"  Medical Discipline 分布: {dict(disc_counter)}")
        all_flags.append((name, content_silent))

    # 汇总报告
    total_flags = sum(len(n) for _, n in all_flags)
    print("\n" + "=" * 70)
    if total_flags == 0:
        print("[PASS] 三集全部题目的内容均含牙科关键词。")
    else:
        print(f"[REVIEW] 共 {total_flags} 题内容无牙科关键词（疑似非牙科通科题），需人工复核：")
        print("=" * 70)
        for name, nodental in all_flags:
            for r in nodental:
                uid = r.get("uid", "?")
                disc = r.get("Medical Discipline", "")
                dept = r.get("Clinical Department", "")
                grp = r.get("Disease Group", "")
                q = (r.get("Question") or "")[:90]
                print(f"  [{name}] uid={uid} 学科={disc} 科室={dept} 疾病组={grp}")
                print(f"      Q: {q}")

    # 写报告
    if report_path:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        lines = []
        lines.append("# 中文牙科子集内容级检测报告\n")
        lines.append("## 检测方法\n")
        lines.append("- 数据：`data/cn_dental/{train,val,test}.jsonl`（按 `Medical Discipline == 口腔医学` 拆分）。\n")
        lines.append("- 对每题拼接 题干+选项，做**内容级**检查（不看学科字段）：\n")
        lines.append("  1. C1 中文强牙科关键词（龋/牙髓/牙周/颌/牙龈/釉质/根管/口腔/义齿/正畸/咬合/氟牙/腭…，见 `check_cn_dental_content.py` 顶部 `CN_STRONG`）；\n")
        lines.append("  2. C3 英文 R1/R2 关键词（复用 `dental_filter.py`，防英文题混入）。\n")
        lines.append("- 内容级命中任一 → 判为「真牙科」；内容级零命中 → 列为「仅靠学科字段、疑似非牙科通科题」。\n")
        lines.append("- 结论依据：口腔医师资格考试试卷含大量基础医学/药理/儿科学通科题，学科字段「口腔医学」并不保证内容是牙科。\n\n")
        lines.append("## 结果\n\n")
        for name, rows in all_flags:
            lines.append(f"- `{name}`: 内容无牙科关键词 {len(rows)} 题（疑似非牙科）\n")
        lines.append("\n## 疑似非牙科题清单\n\n")
        for name, nodental in all_flags:
            for r in nodental:
                uid = r.get("uid", "?")
                disc = r.get("Medical Discipline", "")
                dept = r.get("Clinical Department", "")
                grp = r.get("Disease Group", "")
                q = r.get("Question", "")
                lines.append(f"- `{name}` uid={uid} | 学科={disc} | 科室={dept} | 疾病组={grp}\n")
                lines.append(f"  - Q: {q}\n")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        print(f"\n报告已写入: {report_path}")

    sys.exit(1 if total_flags else 0)


if __name__ == "__main__":
    main()
