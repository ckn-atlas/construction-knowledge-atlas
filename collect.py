# -*- coding: utf-8 -*-
"""
Construction Knowledge Atlas - 데이터 수집기
OpenAlex API(무료, 키 불필요)로 주요 건설 저널의 논문을 수집해
프로토타입(index.html)이 읽는 JSON 파일들로 변환한다.

생성물 (data/ 폴더):
  - graph.json      : 기술 온톨로지 그래프 (nodes=키워드, links=공동출현)
  - country.json    : 국가별 논문수/인용수/주요기관/주요기술 (+ISO 코드)
  - network.json    : 기관 공동저자 네트워크 (+기관 국가코드)
  - papers.json     : 영향력 논문 (Impact = 인용 + FWCI + 최근성 + OA)
  - trend.json      : 최근 기술 트렌드 + 증가율
  - evolution.json  : 연도별 핵심 기술 조합 (상위 기술쌍/키워드)
  - meta.json       : 수집 메타정보
  - _raw.json       : 원자료 캐시 (rebuild 용)

사용법:
  python collect.py            # 전체 수집 후 JSON 생성
  python collect.py rebuild    # 재수집 없이 _raw.json 으로 JSON 만 재생성(빠름)
"""
import requests
import json
import os
import sys
import time
from collections import defaultdict, Counter
from datetime import datetime

# Windows 콘솔 한글 깨짐 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ----------------------------------------------------------------------
# 설정
# ----------------------------------------------------------------------
# polite pool용. 본인 메일로 교체 권장.
# 주의: "your-email@example.com" 같은 placeholder 는 OpenAlex 가 403 으로 차단한다. 비우면 mailto 미전송.
MAILTO = ""
BASE = "https://api.openalex.org/works"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 2020-01-01 부터 수집 → 5개년 트렌드 확보, 2024·2025 완결연도로 증가율 계산
SINCE = "2020-01-01"
PREV_YEAR = 2024        # 증가율 기준 이전 완결연도
LAST_YEAR = 2025        # 증가율 기준 최신 완결연도
PER_PAGE = 200          # OpenAlex 최대 200
MAX_PAGES = 999         # 무제한 — 저널 전체 수집

# JCR CONSTRUCTION & BUILDING TECHNOLOGY (FA) + ENGINEERING, CIVIL (IM) 카테고리 전체
# jcr_categories.json 에서 동적 로딩 (jcr_categories.py 로 갱신)
def _load_journals():
    _path = os.path.join(OUT_DIR, "jcr_categories.json")
    if os.path.isfile(_path):
        try:
            _d = json.load(open(_path, encoding="utf-8"))
            return [{"name": j.get("name", issn), "issn": issn}
                    for issn, j in _d.items() if issn]
        except Exception:
            pass
    # fallback: 기존 18개 저널
    return [
        {"name": "Automation in Construction",                    "issn": "0926-5805"},
        {"name": "Advanced Engineering Informatics",              "issn": "1474-0346"},
        {"name": "Construction and Building Materials",           "issn": "0950-0618"},
        {"name": "Journal of Building Engineering",               "issn": "2352-7102"},
        {"name": "Buildings",                                     "issn": "2075-5309"},
        {"name": "Frontiers in Built Environment",                "issn": "2297-3362"},
        {"name": "KSCE Journal of Civil Engineering",             "issn": "1226-7988"},
        {"name": "J. of Information Technology in Construction",  "issn": "1874-4753"},
        {"name": "J. of Construction Engineering and Mgmt",       "issn": "0733-9364"},
        {"name": "Journal of Structural Engineering",             "issn": "0733-9445"},
        {"name": "Case Studies in Construction Materials",        "issn": "2214-5095"},
        {"name": "Engineering Construction & Architectural Mgmt", "issn": "0969-9988"},
        {"name": "Journal of Computing in Civil Engineering",     "issn": "0887-3801"},
        {"name": "Journal of Civil Engineering and Management",   "issn": "1392-3730"},
        {"name": "J. of Geotechnical and Geoenvironmental Eng",   "issn": "1090-0241"},
        {"name": "ACI Materials Journal",                         "issn": "0889-325X"},
        {"name": "J. of Rock Mechanics and Geotechnical Eng",     "issn": "1674-7755"},
        {"name": "Computer-Aided Civil & Infrastructure Eng",     "issn": "1093-9687"},
    ]

JOURNALS = _load_journals()

# 기술 키워드 정규화 사전: OpenAlex concept/keyword -> 사이트 표준 노드명 (소문자 포함 매칭)
# 세분화된 키워드 정규화 사전.
# canon_keyword() 는 (1)정확매칭 후 (2)dict 순서대로 부분문자열 매칭하므로
# 반드시 "더 구체적인(긴) 표현"을 위에, "포괄적인(짧은) 표현"을 아래에 둔다.
CANON = {
    # ---- AI / ML 세부 ----
    "large language model": "LLM", "foundation model": "LLM", "generative adversarial": "GAN",
    "generative": "Generative AI", "transformer": "Transformer",
    "convolutional neural network": "CNN", "graph neural network": "Graph Neural Net",
    "deep reinforcement learning": "Reinforcement Learning", "reinforcement learning": "Reinforcement Learning",
    "transfer learning": "Transfer Learning", "deep learning": "Deep Learning",
    "artificial neural network": "Neural Network", "deep neural network": "Deep Learning",
    "neural network": "Neural Network", "machine learning": "Machine Learning",
    "explainable": "Explainable AI", "anomaly detection": "Anomaly Detection",
    "natural language": "NLP", "agentic": "Agentic AI", "llm": "LLM",
    "artificial intelligence": "AI (general)",
    # ---- 비전 / 인식 세부 ----
    "crack detection": "Crack Detection", "crack": "Crack Detection",
    "defect detection": "Defect Detection", "object detection": "Object Detection",
    "semantic segmentation": "Segmentation", "image segmentation": "Segmentation",
    "image classification": "Image Classification", "pose estimation": "Pose Estimation",
    "pattern recognition": "Pattern Recognition", "computer vision": "Computer Vision",
    "image processing": "Image Processing",
    # ---- 측량 / 센싱 세부 ----
    "simultaneous localization and mapping": "Visual SLAM", "visual slam": "Visual SLAM",
    "slam": "Visual SLAM", "point cloud": "Point Cloud", "lidar": "LiDAR",
    "ground penetrating radar": "GPR", "laser scanning": "Laser Scanning",
    "terrestrial laser": "Laser Scanning", "photogrammetry": "Photogrammetry",
    "digital image correlation": "DIC", "structural health monitoring": "SHM",
    "structural health": "SHM", "wearable": "Wearable Sensing",
    "internet of things": "IoT", "iot": "IoT", "wireless sensor": "Sensor Network",
    "sensor": "Sensors",
    # ---- BIM / 정보관리 세부 ----
    "scan-to-bim": "Scan-to-BIM", "scan to bim": "Scan-to-BIM",
    "industry foundation classes": "IFC", "ifc": "IFC", "openbim": "OpenBIM",
    "4d bim": "4D BIM", "5d bim": "5D BIM",
    "building information modeling": "BIM", "building information model": "BIM", "bim": "BIM",
    "knowledge graph": "Knowledge Graph", "ontology": "Ontology",
    "semantic web": "Semantic Web", "knowledge management": "Knowledge Mgmt",
    # ---- 디지털트윈 / 로봇 / 자동화 세부 ----
    "digital twin": "Digital Twin", "cyber-physical": "Cyber-Physical Sys",
    "path planning": "Path Planning", "motion planning": "Path Planning",
    "unmanned aerial": "Drone/UAV", "uav": "Drone/UAV", "drone": "Drone/UAV",
    "3d concrete printing": "3D Concrete Printing",
    "additive manufacturing": "3D Printing", "3d printing": "3D Printing",
    "autonomous": "Autonomous Equipment", "robotic": "Robotics", "robot": "Robotics",
    "robotics": "Robotics", "drone": "Drone/UAV", "uav": "Drone/UAV",
    "unmanned aerial": "Drone/UAV", "autonomous robot": "Robotics",
    "automation": "Construction Automation",
    # ---- 재료 세부 ----
    "geopolymer concrete": "Geopolymer", "geopolymer": "Geopolymer", "alkali-activated": "Geopolymer",
    "ultra-high performance": "UHPC", "uhpc": "UHPC",
    "high-performance concrete": "HPC", "fiber-reinforced": "Fiber-Reinforced",
    "fibre-reinforced": "Fiber-Reinforced", "recycled aggregate": "Recycled Aggregate",
    "self-healing": "Self-Healing Concrete", "compressive strength": "Compressive Strength",
    "flexural strength": "Flexural Strength", "tensile strength": "Tensile Strength",
    "durability": "Durability", "corrosion": "Corrosion",
    "supplementary cementitious": "SCM", "fly ash": "Fly Ash",
    "microstructure": "Microstructure", "reinforced concrete": "Reinforced Concrete",
    "portland cement": "Cementitious", "mortar": "Mortar", "concrete": "Concrete",
    "cement": "Cementitious", "asphalt": "Asphalt", "composite material": "Composite",
    # ---- 구조 / 지반 세부 ----
    "finite element": "FEM", "seismic": "Seismic", "earthquake": "Seismic",
    "fatigue": "Fatigue", "fracture": "Fracture", "tunnelling": "Tunneling",
    "tunnel": "Tunneling", "geotechnical": "Geotechnical", "foundation": "Foundation Eng",
    "slope stability": "Slope Stability", "soil": "Soil Mechanics",
    # ---- 지속가능 / 에너지 세부 ----
    "life cycle assessment": "LCA", "embodied carbon": "Embodied Carbon",
    "carbon emission": "Carbon Emission", "carbon footprint": "Carbon Emission",
    "greenhouse gas": "Carbon Emission", "energy efficiency": "Energy Efficiency",
    "energy consumption": "Building Energy", "thermal comfort": "Thermal Comfort",
    "green building": "Green Building", "sustainability": "Sustainability",
    "sustainable": "Sustainability", "energy": "Building Energy",
    # ---- 관리 / 안전 세부 ----
    "construction safety": "Construction Safety", "hazard": "Hazard Detection",
    "fall": "Fall Prevention", "cost estimation": "Cost Estimation",
    "scheduling": "Scheduling", "productivity": "Productivity",
    "risk management": "Risk Mgmt", "risk assessment": "Risk Mgmt",
    "lean construction": "Lean Construction", "supply chain": "Supply Chain",
    "facility management": "Facility Mgmt", "safety": "Construction Safety",
    "prefabrica": "Prefabrication", "modular": "Modular Construction",
}

# ──────────────────────────────────────────────────────────────────────
# GROUP_OF / PARENT: OpenAlex 계층이 PRIMARY 소스.
# 여기 값은 최소한의 시드(seed) / 명시적 override만 유지.
# build_outputs() 에서 concept_meta(OpenAlex ancestors)로 자동 갱신.
# taxonomy.json이 최종 override.
# ──────────────────────────────────────────────────────────────────────
GROUP_OF = {
    # OpenAlex lv0~1 개념에서 자동 파생 불가한 것들만 명시
    "AI (general)": "AI", "LLM": "AI", "NLP": "AI",
    "BIM": "BIM", "Digital Twin": "DT", "Cyber-Physical Sys": "DT",
    "IoT": "Sensing", "SHM": "Sensing",
    "Robotics": "Robot", "Construction Automation": "Robot",
    "Sustainability": "Eco", "Building Energy": "Eco",
    "Construction Safety": "Mgmt",
}

# OpenAlex lv0~1 이름 → 우리 그룹명 매핑 (build_outputs에서 사용)
OA_TO_GROUP = {
    "computer science": "AI", "artificial intelligence": "AI",
    "machine learning": "AI", "data mining": "AI",
    "materials science": "Material", "chemistry": "Material",
    "composite material": "Material", "polymer": "Material",
    "civil engineering": "Structural", "structural engineering": "Structural",
    "mechanical engineering": "Structural",
    "environmental science": "Eco", "ecology": "Eco",
    "construction management": "Mgmt", "engineering management": "Mgmt",
    "business": "Mgmt", "operations research": "Mgmt",
    "geography": "Geo", "geology": "Geo", "geotechnical engineering": "Geo",
    "robotics": "Robot", "automation": "Robot",
    "computer vision": "Vision", "image processing": "Vision",
    "remote sensing": "Sensing", "sensor": "Sensing",
    "building information modeling": "BIM", "information system": "BIM",
    "digital twin": "DT",
    "environmental engineering": "Eco", "sustainable development": "Eco",
    "physics": "Structural", "mechanics": "Structural",
    "mathematics": "AI",
}

PARENT = {}  # OpenAlex ancestor에서 자동 설정 (build_outputs 내에서 채워짐)


def resolve_parent(node, present):
    """node 의 부모를, top_nodes(present) 안에 실제로 존재하는 가장 가까운 조상으로 해석.
    없으면 None (=중앙 가상 루트에 붙음)."""
    p = PARENT.get(node)
    while p is not None and p not in present:
        p = PARENT.get(p)
    return p if (p in present) else None

CC_NAME = {"US": "미국", "CN": "중국", "GB": "영국", "DE": "독일", "KR": "한국",
           "JP": "일본", "IT": "이탈리아", "AU": "호주", "CA": "캐나다", "ES": "스페인",
           "FR": "프랑스", "NL": "네덜란드", "IN": "인도", "SG": "싱가포르", "HK": "홍콩",
           "CH": "스위스", "SE": "스웨덴", "BE": "벨기에", "AT": "오스트리아", "PL": "폴란드",
           "TR": "튀르키예", "IR": "이란", "SA": "사우디", "EG": "이집트", "ZA": "남아공",
           "MY": "말레이시아", "BR": "브라질", "RU": "러시아", "TW": "대만", "MO": "마카오",
           "NG": "나이지리아", "PT": "포르투갈", "GR": "그리스", "NZ": "뉴질랜드",
           "PK": "파키스탄", "BD": "방글라데시", "TH": "태국", "VN": "베트남",
           "NO": "노르웨이", "FI": "핀란드"}


# ----------------------------------------------------------------------
# taxonomy.json 로드 (있으면 CANON/GROUP_OF/PARENT를 자동 보완)
# ----------------------------------------------------------------------
_TAXO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taxonomy.json")

def _load_taxonomy():
    """taxonomy.json을 읽어 CANON/GROUP_OF/PARENT에 병합하고
    중분류(mid_cat) 노드도 GROUP_OF에 등록한다."""
    if not os.path.exists(_TAXO_PATH):
        return
    try:
        with open(_TAXO_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(u"[taxonomy] 로드 실패: {0}".format(e))
        return

    added_canon = added_group = added_parent = 0
    for raw_kw, info in data.items():
        if raw_kw.startswith("_"):
            continue
        canon   = (info.get("canon")   or "").strip()
        group   = (info.get("group")   or "").strip()
        mid_cat = (info.get("mid_cat") or "").strip() or None
        parent  = (info.get("parent")  or "").strip() or None
        if not canon:
            continue

        # CANON
        if raw_kw not in CANON:
            CANON[raw_kw] = canon
            added_canon += 1

        # GROUP_OF — taxonomy.json이 hardcoded 값보다 우선
        if group:
            if canon not in GROUP_OF:
                added_group += 1
            GROUP_OF[canon] = group

        # GROUP_OF — 중분류 노드도 같은 그룹으로 등록
        if mid_cat and group:
            if mid_cat not in GROUP_OF:
                added_group += 1
            GROUP_OF[mid_cat] = group

        # PARENT — taxonomy.json이 우선
        if parent:
            if canon not in PARENT:
                added_parent += 1
            PARENT[canon] = parent

        # PARENT — 중분류 자체는 부모 없음 (테마 색으로만 구분)
        # (mid_cat을 PARENT에 넣지 않으면 온톨로지 트리에서 루트 직계로 배치됨)

    print(u"[taxonomy] CANON+{0}  GROUP_OF+{1}  PARENT+{2}".format(
        added_canon, added_group, added_parent))

_load_taxonomy()   # 모듈 로드 시 자동 실행


# ----------------------------------------------------------------------
# 유틸
# ----------------------------------------------------------------------
def log(msg):
    print(u"[{0}] {1}".format(datetime.now().strftime("%H:%M:%S"), msg))
    sys.stdout.flush()


def canon_keyword(text):
    """원시 키워드/개념명을 표준 노드명으로 정규화. 없으면 None."""
    if not text:
        return None
    t = text.strip().lower()
    if t in CANON:
        return CANON[t]
    for frag, canon in CANON.items():
        if frag in t:
            return canon
    return None


# ----------------------------------------------------------------------
# 수집
# ----------------------------------------------------------------------
def fetch_journal(journal, since=None):
    """한 저널의 SINCE 이후 논문 목록을 OpenAlex 에서 수집"""
    works = []
    cursor = "*"
    for _page in range(MAX_PAGES):
        params = {
            "filter": "primary_location.source.issn:{0},from_publication_date:{1}".format(
                journal["issn"], since or SINCE),
            "sort": "publication_date:desc",
            "per-page": PER_PAGE,
            "cursor": cursor,
            "select": ("id,title,publication_year,publication_date,cited_by_count,"
                       "fwci,open_access,authorships,concepts,keywords,doi,"
                       "primary_location,abstract_inverted_index"),
        }
        if MAILTO:
            params["mailto"] = MAILTO
        try:
            r = requests.get(BASE, params=params, timeout=30)
            r.raise_for_status()
        except Exception as e:
            log(u"  ! 요청 실패 ({0}): {1!r}".format(journal["name"], e))
            break
        data = r.json()
        batch = data.get("results", [])
        works.extend(batch)
        cursor = data.get("meta", {}).get("next_cursor")
        log(u"  {0} - {1}편 누적".format(journal["name"], len(works)))
        if not cursor or not batch:
            break
        time.sleep(0.3)   # polite
    return works


# ----------------------------------------------------------------------
# 변환
# ----------------------------------------------------------------------
def build_outputs(all_works):
    node_papers = Counter()            # 키워드별 논문수(전체 윈도)
    node_year = defaultdict(Counter)   # 키워드 -> 연도 -> 논문수
    node_month = defaultdict(Counter)  # 키워드 -> "YYYY-MM" -> 논문수
    pair_co = Counter()                # 키워드 공동출현(전체)
    pair_year = defaultdict(Counter)   # 연도 -> pair -> 공동출현
    pair_month = defaultdict(Counter)  # "YYYY-MM" -> pair -> 공동출현
    country_papers = Counter()
    country_cites = Counter()
    country_year = defaultdict(Counter)   # 국가 -> 연도 -> 논문수
    country_orgs = defaultdict(Counter)
    country_tech = defaultdict(Counter)
    org_pairs = Counter()              # 기관 공동저자
    org_pairs_year = defaultdict(Counter)  # year -> pairs
    org_pairs_half = defaultdict(Counter)  # "2024H1"/"2024H2" -> pairs
    org_weight = Counter()
    org_country = defaultdict(Counter)  # 기관 -> 국가코드 -> 빈도
    journal_papers = Counter()         # 저널별 논문수
    journal_cites = Counter()          # 저널별 인용수 합
    papers_scored = []

    # OpenAlex concept 계층 자동 수집
    # concept_meta[canonical_name] = {level, best_parent, group_hint, raw_name}
    concept_meta = {}   # canonical → {level, parent_raw, group_hint}

    def _register_concept_meta(c_obj):
        """OpenAlex concept 객체에서 계층 정보 추출·저장"""
        raw_name = c_obj.get("display_name", "").strip()
        ck = canon_keyword(raw_name)
        if not ck:
            return
        lv = c_obj.get("level", -1)
        ancestors = c_obj.get("ancestors") or []

        if ck not in concept_meta:
            concept_meta[ck] = {"level": lv, "parent_raw": None, "group_hint": None}
        else:
            # 더 구체적인 레벨 정보가 있으면 업데이트
            if lv > concept_meta[ck]["level"]:
                concept_meta[ck]["level"] = lv

        # 직계 부모: ancestors 중 자신보다 1~2레벨 위인 것 중 가장 가까운 것
        if ancestors and concept_meta[ck]["parent_raw"] is None:
            # ancestors는 최하위 → 최상위 순이거나 반대일 수 있으므로 level로 정렬
            sorted_anc = sorted(ancestors, key=lambda a: a.get("level", 0), reverse=True)
            for anc in sorted_anc:
                anc_lv = anc.get("level", 0)
                if anc_lv < lv:
                    concept_meta[ck]["parent_raw"] = anc.get("display_name", "")
                    break

        # 그룹 힌트: level 0~1 ancestor
        if concept_meta[ck]["group_hint"] is None:
            for anc in ancestors:
                if anc.get("level", 99) <= 1:
                    concept_meta[ck]["group_hint"] = anc.get("display_name", "")
                    break

    for w in all_works:
        # --- 키워드 추출 + 정규화 ---
        raw = []
        for c in (w.get("concepts") or []):
            if c.get("score", 0) >= 0.3:
                raw.append(c.get("display_name", ""))
                _register_concept_meta(c)  # ← 계층 정보 수집
        for k in (w.get("keywords") or []):
            raw.append(k.get("display_name", "") or k.get("keyword", ""))
        canon = []
        for x in raw:
            ck = canon_keyword(x)
            if ck and ck not in canon:
                canon.append(ck)

        year = w.get("publication_year") or 0
        pub_date = w.get("publication_date") or ""
        month_key = pub_date[:7] if len(pub_date) >= 7 else ""  # "2024-03"
        for ck in canon:
            node_papers[ck] += 1
            node_year[ck][year] += 1
            if month_key:
                node_month[ck][month_key] += 1
        for i in range(len(canon)):
            for j in range(i + 1, len(canon)):
                pair = tuple(sorted([canon[i], canon[j]]))
                pair_co[pair] += 1
                pair_year[year][pair] += 1
                if month_key:
                    pair_month[month_key][pair] += 1

        # --- 국가 / 기관 ---
        countries_here = set()
        orgs_here = []
        for a in (w.get("authorships") or []):
            for inst in (a.get("institutions") or []):
                name = inst.get("display_name")
                cc = inst.get("country_code")
                if name:
                    orgs_here.append(name)
                    if cc:
                        org_country[name][cc] += 1
                if cc:
                    countries_here.add(cc)
                    if name:
                        country_orgs[cc][name] += 1
                    for ck in canon:
                        country_tech[cc][ck] += 1
        for cc in countries_here:
            country_papers[cc] += 1
            country_cites[cc] += w.get("cited_by_count", 0)
            if year:
                country_year[cc][year] += 1
        orgs_here = list(dict.fromkeys(orgs_here))   # 중복 제거, 순서 유지
        for o in orgs_here:
            org_weight[o] += 1
        for i in range(len(orgs_here)):
            for j in range(i + 1, len(orgs_here)):
                org_pairs[tuple(sorted([orgs_here[i], orgs_here[j]]))] += 1
                if year:
                    pair_key = tuple(sorted([orgs_here[i], orgs_here[j]]))
                    org_pairs_year[year][pair_key] += 1
                    half = f"{year}H1" if (pub_date[5:7] <= '06') else f"{year}H2"
                    org_pairs_half[half][pair_key] += 1

        # --- Impact 원자료 ---
        loc = w.get("primary_location") or {}
        src = (loc.get("source") or {}).get("display_name", "")
        oa = (w.get("open_access") or {}).get("is_oa", False)
        if src:
            journal_papers[src] += 1
            journal_cites[src] += w.get("cited_by_count", 0)
        title = (w.get("title") or "").strip()
        # 제목이 저널명과 같거나 비어 있으면 저널 레코드 — 논문으로 취급 안 함
        if not title or (src and title.lower() == src.lower()):
            continue
        papers_scored.append({
            "t": title or "(제목 없음)",
            "j": src,
            "y": year,
            "date": pub_date[:7] if len(pub_date) >= 7 else str(year),
            "cit": w.get("cited_by_count", 0),
            "fwci": w.get("fwci"),          # field-weighted citation impact
            "oa": bool(oa),
            "doi": w.get("doi"),
            "tech": canon[:4],
        })

    # ----- graph.json (증가율 = 전년대비 LAST vs PREV, 부분연도 2026 제외) -----
    def growth(n):
        prev = node_year[n][PREV_YEAR]
        last = node_year[n][LAST_YEAR]
        if prev == 0:
            return 100 if last else 0
        return int(round((last - prev) / float(prev) * 100))

    # ── 세부기술 노드 선택 ──
    # 기본 상위 100개 + 각 taxonomy 그룹에서 최대 3개 보장 (소규모 그룹 누락 방지)
    _top100 = {n for n, _ in node_papers.most_common(100)}
    _group_top = {}   # grp -> [node, ...]
    for n, cnt in node_papers.most_common():
        grp = GROUP_OF.get(n)
        if grp and cnt > 0:
            if grp not in _group_top:
                _group_top[grp] = []
            if len(_group_top[grp]) < 3:
                _group_top[grp].append(n)
    for grp_nodes in _group_top.values():
        _top100.update(grp_nodes)
    top_nodes = [n for n, _ in node_papers.most_common() if n in _top100]
    nodeset   = set(top_nodes)

    # ── 중분류 노드 자동 추출 ──
    # 세부기술 노드의 parent(중분류)가 top_nodes에 없으면 가상 중분류 노드 생성
    mid_agg = {}   # mid_name → {papers, group}
    for n in top_nodes:
        p = PARENT.get(n)
        if p and p not in nodeset:
            grp = GROUP_OF.get(p, GROUP_OF.get(n, "AI"))
            if p not in mid_agg:
                mid_agg[p] = {"papers": 0, "group": grp}
            mid_agg[p]["papers"] += node_papers[n]

    # taxonomy.json의 mid_cat도 추가 (등장 빈도가 낮아 top_nodes에 없는 경우)
    if os.path.exists(_TAXO_PATH):
        try:
            with open(_TAXO_PATH, encoding="utf-8") as _tf:
                _taxo = json.load(_tf)
            for _info in _taxo.values():
                mc = (_info.get("mid_cat") or "").strip()
                grp = (_info.get("group")  or "AI").strip()
                if mc and mc not in nodeset and mc not in mid_agg:
                    mid_agg[mc] = {"papers": 0, "group": grp}
        except Exception:
            pass

    # 중분류 노드를 nodeset에 추가
    nodeset.update(mid_agg.keys())

    # ── OpenAlex concept_meta → GROUP_OF / PARENT 자동 결정 (MAIN SOURCE) ──
    # 1단계: OpenAlex ancestors 기반으로 GROUP_OF, PARENT 채우기
    # 2단계: taxonomy.json이 _load_taxonomy()에서 이미 적용됨 → 최종 override
    for ck, meta in concept_meta.items():
        # GROUP_OF: lv0~1 ancestor에서 우리 그룹명 결정
        hint = (meta.get("group_hint") or "").lower()
        if hint:
            for k, v in OA_TO_GROUP.items():
                if k in hint:
                    GROUP_OF[ck] = v
                    break

        # PARENT: OpenAlex ancestor chain에서 직계 부모 결정
        # (taxonomy.json에 명시된 것이 있으면 _load_taxonomy에서 이미 override됨)
        if meta.get("parent_raw"):
            parent_ck = canon_keyword(meta["parent_raw"])
            if parent_ck and parent_ck != ck:
                PARENT[ck] = parent_ck

    # taxonomy.json 재적용 (OpenAlex 파생값보다 taxonomy 우선)
    _load_taxonomy()

    # ── 노드 목록 구성 ──
    nodes = []
    for n in top_nodes:
        prev = node_year[n][PREV_YEAR]
        last = node_year[n][LAST_YEAR]
        meta = concept_meta.get(n, {})
        nodes.append({
            "id":          n,
            "group":       GROUP_OF.get(n, "AI"),
            "papers":      node_papers[n],
            "growth":      growth(n),
            "growth_cnt":  int(last - prev),
            "prev_papers": int(prev),
            "last_papers": int(last),
            "parent":      resolve_parent(n, nodeset),
            "level":       3,
            "oa_level":    meta.get("level", -1),  # OpenAlex 원본 계층 레벨
            "monthly":     dict(sorted(node_month[n].items())),
        })
    for p, info in mid_agg.items():
        nodes.append({
            "id":      p,
            "group":   info["group"],
            "papers":  info["papers"],
            "growth":  0,
            "parent":  None,   # 중분류는 루트 직계
            "level":   2,      # 중분류
            "monthly": {},
        })
    links = []
    for (a, b), co in pair_co.most_common():
        if a in nodeset and b in nodeset and co >= 2:
            monthly_co = {m: int(pair_month[m][(a, b)])
                          for m in sorted(pair_month)
                          if pair_month[m][(a, b)] > 0}
            links.append([a, b, co, monthly_co])
    graph = {"nodes": nodes, "links": links}

    # ----- country.json (상위 40개국 + ISO 코드) -----
    countries = []
    for cc, cnt in country_papers.most_common(40):
        countries.append({
            "c": CC_NAME.get(cc, cc),
            "code": cc,
            "papers": cnt,
            "cites": country_cites[cc],
            "orgs": [o for o, _ in country_orgs[cc].most_common(4)],
            "tech": [t for t, _ in country_tech[cc].most_common(3)],
            "keywords": [[t, n] for t, n in country_tech[cc].most_common(20)],
            "yearly": {str(y): n for y, n in sorted(country_year[cc].items())},
        })

    # ----- network.json (기관 공동저자) -----
    # 국가 다양성 확보: 논문수 1위 국가(중국)에 쏠리지 않도록 국가당 최대 N개 기관만 선정.
    def dom_country(o):
        c = org_country.get(o)
        return c.most_common(1)[0][0] if c else ""
    MAX_PER_COUNTRY = 15    # 국가당 최대 15개 (다양성 확보)
    NET_SIZE = 150
    per_cc = Counter()
    net_nodes = []
    for o, _ in org_weight.most_common():
        cc = dom_country(o)
        if per_cc[cc] >= MAX_PER_COUNTRY:
            continue
        per_cc[cc] += 1
        net_nodes.append(o)
        if len(net_nodes) >= NET_SIZE:
            break
    net_set = set(net_nodes)
    net_links = []
    for (a, b), co in org_pairs.most_common():
        if a in net_set and b in net_set and co >= 1:
            net_links.append([a, b, co])

    # 기관 좌표 수집 (OpenAlex institutions API, 캐시 활용)
    coords_cache_path = os.path.join(OUT_DIR, "_org_coords.json")
    try:
        coords_cache = json.load(open(coords_cache_path, encoding="utf-8"))
    except Exception:
        coords_cache = {}

    def fetch_org_coord(name):
        if name in coords_cache:
            return coords_cache[name]
        try:
            url = f"https://api.openalex.org/institutions?search={requests.utils.quote(name)}&per-page=1"
            r = requests.get(url, timeout=8, headers={"User-Agent":"mailto:research@example.com"})
            results = r.json().get("results", [])
            if results:
                geo = results[0].get("geo") or {}
                lat, lon = geo.get("latitude"), geo.get("longitude")
                if lat is not None and lon is not None:
                    coords_cache[name] = [float(lat), float(lon)]
                    return coords_cache[name]
        except Exception:
            pass
        coords_cache[name] = None
        return None

    org_coords = {}
    for o in net_nodes:
        coord = fetch_org_coord(o)
        if coord:
            org_coords[o] = coord

    # 캐시 저장
    try:
        json.dump(coords_cache, open(coords_cache_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 기간별 links 생성 함수
    def make_period_links(pairs_counter):
        return [[a, b, co] for (a, b), co in pairs_counter.most_common()
                if a in net_set and b in net_set and co >= 1][:200]

    # 연도별, 반기별 links
    links_by_year = {str(yr): make_period_links(org_pairs_year[yr])
                     for yr in sorted(org_pairs_year.keys())}
    links_by_half = {h: make_period_links(org_pairs_half[h])
                     for h in sorted(org_pairs_half.keys())}

    network = {
        "nodes": net_nodes,
        "links": net_links[:200],
        "weight": {o: org_weight[o] for o in net_nodes},
        "country": {o: dom_country(o) for o in net_nodes},
        "coords": org_coords,
        "links_by_year": links_by_year,
        "links_by_half": links_by_half,
    }

    # ----- papers.json (Impact = 인용 + FWCI + 최근성 + OA) -----
    max_cit = max([p["cit"] for p in papers_scored] or [1]) or 1
    max_fwci = max([p["fwci"] for p in papers_scored if p["fwci"]] or [1]) or 1
    this_year = LAST_YEAR + 1
    for p in papers_scored:
        cit_n = p["cit"] / float(max_cit)
        fwci_n = (p["fwci"] / float(max_fwci)) if p["fwci"] else 0
        recency = 1.0 if p["y"] >= this_year else (0.6 if p["y"] == LAST_YEAR else 0.2)
        score = 0.45 * cit_n + 0.30 * fwci_n + 0.15 * recency + 0.10 * (1 if p["oa"] else 0)
        p["score"] = int(round(score * 100))
    papers_scored.sort(key=lambda x: x["score"], reverse=True)

    # 기간별로 보장된 논문 포함 (전체 top20 + 최근3개월 top10 + 최근3년 top10 합집합)
    now = datetime.now()
    cut_3m = f"{now.year}-{(now.month - 3 - 1) % 12 + 1:02d}" if now.month > 3 \
             else f"{now.year - 1}-{now.month + 9:02d}"
    cut_3y = now.year - 2

    seen = set()
    papers = []
    for bucket in [
        papers_scored[:20],
        sorted([p for p in papers_scored if p.get("date","") >= cut_3m],
               key=lambda x: x["score"], reverse=True)[:10],
        sorted([p for p in papers_scored if p.get("y", 0) >= cut_3y],
               key=lambda x: x["score"], reverse=True)[:10],
    ]:
        for p in bucket:
            key = p.get("doi") or p["t"]
            if key not in seen:
                seen.add(key)
                papers.append(p)

    # ----- trend.json -----
    trend = sorted(
        [{"id": n["id"], "papers": n["papers"], "growth": n["growth"]} for n in nodes],
        key=lambda x: x["papers"], reverse=True)[:8]

    # ----- evolution.json (연도별 상위 3개 기술쌍 + 상위 키워드) -----
    evolution = []
    for yr in sorted(y for y in pair_year.keys() if y and y >= PREV_YEAR):
        top_kw = [{"id": k, "n": c} for k, c in
                  Counter({n: node_year[n][yr] for n in node_year}).most_common(4)]
        top_pairs = [{"a": pr[0], "b": pr[1], "co": co}
                     for pr, co in pair_year[yr].most_common(3)]
        evolution.append({"year": yr, "top_keywords": top_kw, "top_pairs": top_pairs})

    # ----- journals.json (수집된 저널별 논문수/인용수) -----
    # OpenAlex가 돌려준 실제 저널명(src) 기준 집계. 저널마다 표기가 갈릴 수 있어 그대로 노출.
    # ISSN 역매핑 (저널명 → ISSN)
    name_to_issn = {j["name"].lower(): j["issn"] for j in JOURNALS}
    journals = [{"name": name, "papers": cnt, "cites": journal_cites[name],
                 "issn": name_to_issn.get(name.lower(), "")}
                for name, cnt in journal_papers.most_common()]

    return {
        "graph.json": graph,
        "country.json": countries,
        "network.json": network,
        "papers.json": papers,
        "trend.json": trend,
        "evolution.json": evolution,
        "journals.json": journals,
    }


def save_outputs(outputs, total):
    outputs["meta.json"] = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_papers": total,
        "journals": [j["name"] for j in JOURNALS],
        "since": SINCE,
    }
    for fname, obj in outputs.items():
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        log(u"저장: {0}".format(fname))


def main():
    print("=" * 60)
    print("Construction Knowledge Atlas - 데이터 수집")
    print("=" * 60)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    raw_path = os.path.join(OUT_DIR, "_raw.json")

    # rebuild 모드: 재수집 없이 캐시로 JSON 만 재생성
    if "rebuild" in sys.argv and os.path.isfile(raw_path):
        log(u"rebuild 모드: _raw.json 에서 로드")
        all_works = json.load(open(raw_path, encoding="utf-8"))
        log(u"캐시 {0}편 로드".format(len(all_works)))
        save_outputs(build_outputs(all_works), len(all_works))
        log(u"rebuild 완료.")
        return 0

    # ── update 모드: 마지막 수집일 이후 신규 논문만 증분 추가 ──
    if "update" in sys.argv and os.path.isfile(raw_path):
        meta_path = os.path.join(OUT_DIR, "meta.json")
        last_date = None
        if os.path.isfile(meta_path):
            try:
                meta = json.load(open(meta_path, encoding="utf-8"))
                # generated_at 형식: "2026-06-01 18:55:35" → "2026-06-01"
                last_date = meta.get("generated_at", "")[:10]
            except Exception:
                pass
        if not last_date:
            log(u"update: meta.json에서 마지막 수집일을 읽을 수 없어 전체 수집으로 전환")
        else:
            log(u"update 모드: {0} 이후 신규 논문만 수집".format(last_date))
            existing = json.load(open(raw_path, encoding="utf-8"))
            existing_ids = {w.get("id") for w in existing if w.get("id")}
            new_works = []
            for j in JOURNALS:
                new_works.extend(fetch_journal(j, since=last_date))
            # 기존에 없는 것만 추가
            added = [w for w in new_works if w.get("id") not in existing_ids]
            log(u"신규 {0}편 추가 (기존 {1}편)".format(len(added), len(existing)))
            all_works = existing + added
            # 중복 제거
            seen2, deduped2 = set(), []
            for w in all_works:
                wid = w.get("id")
                if wid and wid in seen2: continue
                if wid: seen2.add(wid)
                deduped2.append(w)
            all_works = deduped2
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(all_works, f, ensure_ascii=False)
            save_outputs(build_outputs(all_works), len(all_works))
            log(u"update 완료. 총 {0}편".format(len(all_works)))
            return 0

    all_works = []
    for j in JOURNALS:
        log(u"수집: {0}".format(j["name"]))
        all_works.extend(fetch_journal(j))

    # 중복 제거(같은 work id)
    seen = set()
    deduped = []
    for w in all_works:
        wid = w.get("id")
        if wid and wid in seen:
            continue
        if wid:
            seen.add(wid)
        deduped.append(w)
    log(u"총 {0}편 수집 (중복 제거 후 {1}편)".format(len(all_works), len(deduped)))
    all_works = deduped

    if not all_works:
        log(u"수집된 논문이 없습니다. 네트워크/ISSN 확인 필요.")
        return 1

    # 원자료 캐시 (이후 `python collect.py rebuild` 로 즉시 재가공 가능)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False)
    log(u"원자료 캐시 저장: _raw.json")

    save_outputs(build_outputs(all_works), len(all_works))
    print("-" * 60)
    log(u"완료. index.html 새로고침(Ctrl+F5)하면 반영됩니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
