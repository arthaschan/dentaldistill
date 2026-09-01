#!/usr/bin/env python3
"""牙科判定模块 —— 修复了 mentalDistill 旧正则里 `\\boral\\b` 的误判问题。

背景
----
旧正则把 "oral" 当作牙科关键词，但英文医学题里 "oral" 绝大多数是
"口服 / oral administration / oral medication / oral contraceptive"
等非牙科含义（例：洋地黄中毒题的选项 "oral activated charcoal"），
导致英文牙科子集被大量非牙科题污染。

判定规则（可审计：每条命中都返回"命中了哪个词 / 哪条规则"）
--------------------------------------------------------
一条题（题干 + 选项拼接后的文本）被判为"牙科"，当且仅当命中下列任一规则：

R1  强牙科关键词（单独命中即可）：
    tooth, teeth, dental, dentine, dentin, enamel, pulp, molar, premolar,
    incisor, canine, gingiv, periodont, mandib, maxill, caries, occlus,
    denture, endodont, orthodont, amalgam, prosthodont, cementum, odonto,
    root canal, fluoride, saliva, buccal, lingual, periapical, dentition,
    bruxism, malocclusion, alveolar, palat

R2  "oral" 出现在明确口腔语境：
    oral cavity / oral mucosa / oral health / oral hygiene / oral thrush /
    oral candid / oral cancer / oral carcinoma / oral squamous / oral lesion /
    oral ulcer / oral surgery / oral surgeon / oral examination /
    oral manifestation / oral infection / oral tissue / oral disease /
    oral trauma / oral rehabilitation / oral prosthesis / oral implant /
    oral microbiome / oral flora / oral antiseptic / oral rinse /
    oral vestibule / oral floor / oral tongue

明确排除（不判牙科）：
    - 裸 "oral"（口服 / oral medication / oral contraceptive / oral rehydration 等）
    - 裸 "mucosa" / "crown"（胃/肠黏膜、皇冠等；牙科语境下它们必然伴随 R1/R2 命中）

用法
----
    from dental_filter import is_dental, dental_match
    is_dental("...text...")           # -> bool
    dental_match("...text...")        # -> [("R1", "tooth"), ...] 命中明细
"""
import re

# R1 强牙科关键词（不含歧义的 oral / mucosa / crown）
STRONG_KEYWORDS = [
    "tooth", "teeth", "dental", "dentine", "dentin", "enamel", "pulp",
    "molar", "premolar", "incisor", "canine", "gingiv", "periodont",
    "mandib", "maxill", "caries", "occlus", "denture", "endodont",
    "orthodont", "amalgam", "prosthodont", "cementum", "odonto",
    "root canal", "fluoride", "saliva", "buccal", "lingual", "periapical",
    "dentition", "bruxism", "malocclusion", "alveolar", "palat",
]
_STRONG_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in STRONG_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# R2 "oral" 的明确口腔语境
ORAL_CONTEXT_PATTERNS = [
    r"oral\s+cavit",          # cavity / cavities
    r"oral\s+mucosa",
    r"oral\s+health",
    r"oral\s+hygiene",
    r"oral\s+thrush",
    r"oral\s+candid",         # candidiasis
    r"oral\s+cancer",
    r"oral\s+carcinoma",
    r"oral\s+squamous",
    r"oral\s+lesion",
    r"oral\s+ulcer",
    r"oral\s+surgery",
    r"oral\s+surgeon",
    r"oral\s+examin",         # examination
    r"oral\s+manifestation",
    r"oral\s+infection",
    r"oral\s+tissue",
    r"oral\s+disease",
    r"oral\s+trauma",
    r"oral\s+rehab",
    r"oral\s+prosthesis",
    r"oral\s+implant",
    r"oral\s+microbiome",
    r"oral\s+flora",
    r"oral\s+antiseptic",
    r"oral\s+rinse",
    r"oral\s+vestibule",
    r"oral\s+floor",
    r"oral\s+tongue",
    r"oral\s+cavity",
]
_ORAL_CONTEXT_RE = re.compile("|".join(ORAL_CONTEXT_PATTERNS), re.IGNORECASE)

# 学科字段判定（比关键词更可靠，优先）
# D1: CMExam 中文学科字段
DENTAL_DISCIPLINES_CN = {"口腔医学"}
# D2: MedMCQA 英文学科字段
DENTAL_SUBJECTS_EN = {"Dental"}


def dental_match(text: str):
    """返回命中明细 [(规则, 关键词), ...]。空列表 = 非牙科。"""
    hits = []
    for m in _STRONG_RE.finditer(text):
        hits.append(("R1", m.group(1).lower()))
    for m in _ORAL_CONTEXT_RE.finditer(text):
        hits.append(("R2", m.group(0)))
    return hits


def is_dental(text: str) -> bool:
    """text 是否判为牙科。"""
    return bool(dental_match(text))


def question_text(record: dict) -> str:
    """从一条记录拼接题干+选项，作为判定输入。"""
    parts = [str(record.get("Question", "")), str(record.get("Options", ""))]
    # 兼容不同字段名
    for k in ("stem", "question", "text"):
        if k in record:
            parts.insert(0, str(record[k]))
    for k in ("options", "choices"):
        v = record.get(k)
        if isinstance(v, dict):
            parts.append(" ".join(str(x) for x in v.values()))
        elif isinstance(v, str):
            parts.append(v)
    return " ".join(parts)


def is_dental_record(record: dict) -> tuple:
    """对一条记录判定，返回 (是否牙科, 命中明细)。

    判定优先级（任一命中即牙科）：
      D1  中文学科字段 Medical Discipline == "口腔医学"
      D2  英文学科字段 subject == "Dental"（MedMCQA）
      R1  强牙科关键词 / R2 "oral" 口腔语境（英文关键词，MedQA/MMLU/书籍）
    """
    hits = []
    disc = record.get("Medical Discipline") or record.get("discipline") or ""
    if disc in DENTAL_DISCIPLINES_CN:
        hits.append(("D1", disc))
    subj = record.get("subject") or record.get("subject_name") or ""
    if subj in DENTAL_SUBJECTS_EN:
        hits.append(("D2", subj))
    hits += dental_match(question_text(record))
    return (bool(hits), hits)
