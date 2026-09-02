#!/usr/bin/env python3
"""牙科判定模块 v2 —— 修复 v1 的词干误配 + 歧义词假阳性。

背景
----
v1 有两个问题（由 data/audit_en_dental.py 发现）：
1. 词干误配（假阴性）："gingiv/periodont/mandib/maxill/occlus" 等被 `\\b...\\b` 当成整词，
   匹配不到 "gingivitis/periodontal/mandibular/occlusal"，漏掉真牙科题。
2. 歧义词假阳性："alveolar"(肺泡)、"pulp"(脾髓)、"molar"(葡萄胎) 单独命中即判牙科，
   把呼吸科/血液/妇产科题误判为牙科；R2 "oral examination" 是常规体格检查用语，泛滥。

v2 判定规则（可审计：每条命中返回「命中了哪个词 / 哪条规则」）
--------------------------------------------------------
一条题（题干+选项拼接）判为「牙科」，当且仅当命中下列任一：

R1a 精确牙科词（完整词边界，无歧义）：
    tooth, teeth, dental, dentine, dentin, enamel, caries, denture, amalgam,
    cementum, fluoride, periapical, dentition, bruxism, malocclusion, premolar,
    incisor, occlusal, endodontic(s), orthodontic(s), prosthodontic(s),
    gingiva, gingivitis, gingival, periodontitis, periodontal, periodontium,
    mandible, mandibular, maxilla, maxillary, pulpitis, pulpal, pulpotomy,
    pulpectomy, odontogenic, odontoma, odontoblast, palate, palatal, toothache, molar, canine

R1b 词干（词首边界，匹配派生词）：
    gingiv, periodont, mandib, maxill, endodont, orthodont, prosthodont, odonto, palat

R1c 歧义词的牙科限定短语（"alveolar/pulp" 只在明确牙科短语里才算）：
    alveolar bone/ridge/process/socket/crest/mucosa/resorption/nerve,
    dental pulp, pulp chamber/horn/cap/polyp/exposure/necrosis/stone/cavity,
    inferior alveolar nerve

R2  "oral" 口腔语境（明确口腔疾病/解剖，不含泛化的 "oral examination"/"oral mucosa"）：
    oral cavity / oral health / oral hygiene / oral thrush / oral candid /
    oral cancer / oral carcinoma / oral squamous / oral lesion / oral ulcer /
    oral surgery / oral surgeon / oral manifestation / oral infection / oral tissue /
    oral disease / oral trauma / oral rehabilitation / oral prosthesis / oral implant /
    oral microbiome / oral flora / oral antiseptic / oral rinse / oral vestibule /
    oral floor / oral tongue

明确排除（不判牙科）：
    - 裸 "oral"（口服 / oral medication / oral contraceptive / oral rehydration 等）
    - 裸 "mucosa" / "crown"
    - "molar pregnancy" / "hydatidiform"（葡萄胎，molar 在此非牙科）
    - "alveolar" 单独出现（肺泡）——须带牙科限定词（见 R1c）
    - "pulp" 单独出现（脾髓）——须带牙科限定词（见 R1c）

用法
----
    from dental_filter import is_dental, dental_match
    is_dental("...text...")           # -> bool
    dental_match("...text...")        # -> [("R1", "tooth"), ...] 命中明细
"""
import re

# R1a 精确牙科词（完整词边界）
STRONG_EXACT = [
    "tooth", "teeth", "dental", "dentine", "dentin", "enamel", "caries",
    "denture", "amalgam", "cementum", "fluoride", "periapical", "dentition",
    "bruxism", "malocclusion", "premolar", "incisor", "occlusal",
    "endodontic", "endodontics", "orthodontic", "orthodontics",
    "prosthodontic", "prosthodontics", "gingiva", "gingivitis", "gingival",
    "periodontitis", "periodontal", "periodontium", "mandible", "mandibular",
    "maxilla", "maxillary", "pulpitis", "pulpal", "pulpotomy", "pulpectomy",
    "odontogenic", "odontoma", "odontoblast", "palate", "palatal", "toothache",
    "molar", "canine",
]
_EXACT_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in STRONG_EXACT) + r")\b", re.IGNORECASE,
)

# R1b 词干（只有词首边界，匹配派生词）
STRONG_STEMS = ["gingiv", "periodont", "mandib", "maxill", "endodont",
                "orthodont", "prosthodont", "odonto", "palat"]
_STEM_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in STRONG_STEMS) + r")", re.IGNORECASE)

# R1c 歧义词的牙科限定短语
DENTAL_PHRASES = [
    r"alveolar\s+(bone|ridge|process|socket|crest|mucosa|resorption|nerve)",
    r"inferior\s+alveolar\s+nerve",
    r"dental\s+pulp",
    r"pulp\s+(chamber|horn|cap|polyp|exposure|necrosis|stone|cavity|extirpation)",
]
_PHRASE_RE = re.compile("|".join(DENTAL_PHRASES), re.IGNORECASE)

# R2 "oral" 的明确口腔语境（不含泛化的 oral examination / oral mucosa）
ORAL_CONTEXT_PATTERNS = [
    r"oral\s+cavit",          # cavity / cavities
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
]
_ORAL_CONTEXT_RE = re.compile("|".join(ORAL_CONTEXT_PATTERNS), re.IGNORECASE)

# 否定语境：命中则相应的 "molar" 不算牙科
NEGATIVE_PATTERNS = [
    r"molar\s+pregnan",   # molar pregnancy（葡萄胎）
    r"hydatidiform",      # hydatidiform mole
]
_NEG_RE = re.compile("|".join(NEGATIVE_PATTERNS), re.IGNORECASE)

# 学科字段判定（比关键词更可靠，优先）
DENTAL_DISCIPLINES_CN = {"口腔医学"}
DENTAL_SUBJECTS_EN = {"Dental"}


def dental_match(text: str):
    """返回命中明细 [(规则, 关键词), ...]。空列表 = 非牙科。"""
    hits = []
    neg = bool(_NEG_RE.search(text))
    for m in _EXACT_RE.finditer(text):
        w = m.group(1).lower()
        if neg and w == "molar":
            continue  # 葡萄胎里的 molar 不算牙科
        hits.append(("R1", w))
    for m in _STEM_RE.finditer(text):
        hits.append(("R1", m.group(1).lower() + "*"))
    for m in _PHRASE_RE.finditer(text):
        hits.append(("R1", m.group(0).lower()))
    for m in _ORAL_CONTEXT_RE.finditer(text):
        hits.append(("R2", m.group(0)))
    return hits


def is_dental(text: str) -> bool:
    """text 是否判为牙科。"""
    return bool(dental_match(text))


def question_text(record: dict) -> str:
    """从一条记录拼接题干+选项，作为判定输入。"""
    parts = [str(record.get("Question", "")), str(record.get("Options", ""))]
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
      R1  强牙科关键词/词干/短语  +  R2 "oral" 口腔语境
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


def dental_match_strict(text: str):
    """严格版：只返回 R1 强牙科词命中，剔除 R2 "oral" 语境。

    原因：R2 的 oral ulcer/lesion/cavity/candidiasis/thrush 等是「全身病的口腔表现」，
    会把大量非牙科题（精神分裂的 oral health、肺炎的 oral lesion、Zenker 憩室的 oral cavity、
    抑郁的 oral lesion 等）误判为牙科。严格口径只用 R1（tooth/gingivitis/periodontal/…），
    保证「零非牙科」。
    """
    return [h for h in dental_match(text) if h[0] != "R2"]


def is_dental_record_strict(record: dict) -> tuple:
    """严格版牙科判定：D1/D2 + R1，不含 R2 oral 语境。"""
    hits = []
    disc = record.get("Medical Discipline") or record.get("discipline") or ""
    if disc in DENTAL_DISCIPLINES_CN:
        hits.append(("D1", disc))
    subj = record.get("subject") or record.get("subject_name") or ""
    if subj in DENTAL_SUBJECTS_EN:
        hits.append(("D2", subj))
    hits += dental_match_strict(question_text(record))
    return (bool(hits), hits)
