#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jcr_parse.py — JCR MHTML 파일 파싱 → journal_meta.json 업데이트

사용법:
  1. Chrome에서 JCR 저널 페이지 열기 (로그인 상태)
  2. Ctrl+S → "웹페이지, 단일 파일 (*.mhtml)" 로 저장
     저장 위치: data/jcr_pages/  (파일명은 아무거나 OK)
  3. 18개 저널 반복 후 이 스크립트 실행:
     python jcr_parse.py

추출 항목:
  - JIF (Journal Impact Factor, 공식)
  - JIF without self-citations
  - Total Citations
  - Quartile (Q1/Q2/Q3/Q4)
  - JCR Category / Rank
  - Cited Half-Life
  - OA % (citable items)
"""

import os, re, json, email, quopri, sys
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR    = Path(__file__).parent
MHTML_DIR   = BASE_DIR / "data" / "jcr_pages"
META_PATH   = BASE_DIR / "data" / "journal_meta.json"

# JCR 약어 → ISSN 매핑 (collect.py JOURNALS 기준)
JCR_ABBR_TO_ISSN = {
    "AUTOMAT CONSTR":       "0926-5805",
    "ADV ENG INFORM":       "1474-0346",
    "CONSTR BUILD MATER":   "0950-0618",
    "J BUILD ENG":          "2352-7102",
    "BUILDINGS-BASEL":      "2075-5309",
    "FRONT BUILT ENV":      "2297-3362",
    "KSCE J CIV ENG":       "1226-7988",
    "J INF TECHNOL CONSTR": "1874-4753",
    "J CONSTR ENG M":       "0733-9364",
    "J STRUCT ENG":         "0733-9445",
    "CASE STUD CONSTR MAT": "2214-5095",
    "ENG CONSTR ARCHIT MAN":"0969-9988",
    "J COMPUT CIVIL ENG":   "0887-3801",
    "J CIV ENG MANAG":      "1392-3730",
    "J GEOTECH GEOENVIRON": "1090-0241",
    "ACI MATER J":          "0889-325X",
    "J ROCK MECH GEOTECH":  "1674-7755",
    "COMPUT AIDED CIV INF": "1093-9687",
}

def read_mhtml(path: Path) -> str:
    """MHTML 파일에서 HTML 본문 추출"""
    raw = path.read_bytes()
    msg = email.message_from_bytes(raw)

    for part in msg.walk():
        ct = part.get_content_type()
        if ct not in ("text/html", "application/xhtml+xml"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            payload = part.get_payload()
            if isinstance(payload, str):
                enc = part.get("Content-Transfer-Encoding", "")
                if enc.lower() == "quoted-printable":
                    payload = quopri.decodestring(payload.encode()).decode("utf-8", errors="replace")
                else:
                    payload = payload
        else:
            charset = part.get_content_charset() or "utf-8"
            payload = payload.decode(charset, errors="replace")
        return payload
    return raw.decode("utf-8", errors="replace")


def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def extract_number(text: str) -> float | None:
    """문자열에서 숫자 추출 (쉼표 포함)"""
    m = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    return float(m.group().replace(',', '')) if m else None


def parse_jcr_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    full_text = soup.get_text(separator="\n")
    lines = [clean(l) for l in full_text.splitlines() if clean(l)]

    # ── 저널명 & JCR Abbreviation ──
    # <h1> 또는 큰 제목
    for tag in soup.find_all(["h1", "h2"]):
        t = clean(tag.get_text())
        if len(t) > 5 and not t.startswith("Journal"):
            data["jcr_name"] = t
            break

    # 약어 (meta 또는 텍스트)
    abbr_m = re.search(r'JCR ABBREVIATION\s*\n([A-Z ]+)', full_text)
    if abbr_m:
        data["jcr_abbr"] = abbr_m.group(1).strip()

    # ISSN / eISSN
    issn_m = re.search(r'ISSN\s*\n?([\d\-X]+)', full_text)
    if issn_m:
        data["jcr_issn"] = issn_m.group(1).strip()
    eissn_m = re.search(r'[Ee]ISSN\s*\n?([\d\-X]+)', full_text)
    if eissn_m:
        data["jcr_eissn"] = eissn_m.group(1).strip()

    # ── JIF (Journal Impact Factor) ──
    # "2024 JOURNAL IMPACT FACTOR\n11.5" 형식
    jif_m = re.search(
        r'(?:20\d\d\s+)?JOURNAL IMPACT FACTOR\s*\n?\s*([\d]+\.[\d]+)',
        full_text, re.IGNORECASE
    )
    if jif_m:
        data["jif"] = float(jif_m.group(1))

    # JIF without self citations
    jif_no_self_m = re.search(
        r'(?:JOURNAL IMPACT FACTOR WITHOUT SELF[- ]CITATIONS?|JIF WITHOUT SELF)\s*\n?\s*([\d]+\.[\d]+)',
        full_text, re.IGNORECASE
    )
    if jif_no_self_m:
        data["jif_no_self"] = float(jif_no_self_m.group(1))

    # ── Total Citations ──
    cite_m = re.search(
        r'TOTAL CITATIONS?\s*\n?\s*([\d,]+)',
        full_text, re.IGNORECASE
    )
    if cite_m:
        data["total_citations_jcr"] = int(cite_m.group(1).replace(',', ''))

    # ── Quartile ──
    q_m = re.search(r'\b(Q[1-4])\b', full_text)
    if q_m:
        data["quartile"] = q_m.group(1)

    # ── Category Rank (e.g. "5/171 CONSTRUCTION & BUILDING TECHNOLOGY") ──
    rank_m = re.search(
        r'(\d+)\s*/\s*(\d+)\s+([\w &/\-]+(?:ENGINEERING|TECHNOLOGY|SCIENCE|CONSTRUCTION)[^\n]*)',
        full_text, re.IGNORECASE
    )
    if rank_m:
        data["jcr_rank"]     = int(rank_m.group(1))
        data["jcr_rank_of"]  = int(rank_m.group(2))
        data["jcr_category"] = clean(rank_m.group(3))

    # ── Cited Half-Life ──
    hl_m = re.search(r'CITED HALF.LIFE\s*\n?\s*([\d]+\.?[\d]*)', full_text, re.IGNORECASE)
    if hl_m:
        data["cited_half_life"] = float(hl_m.group(1))

    # ── OA % ──
    oa_m = re.search(r'(\d+\.?\d*)\s*%\s*(?:OF CITABLE OA|OPEN ACCESS)', full_text, re.IGNORECASE)
    if oa_m:
        data["oa_pct_jcr"] = float(oa_m.group(1))

    # ── Eigenfactor / Article Influence ──
    ef_m = re.search(r'EIGENFACTOR[^\n]*\n\s*([\d]+\.[\d]+)', full_text, re.IGNORECASE)
    if ef_m:
        data["eigenfactor"] = float(ef_m.group(1))

    ai_m = re.search(r'ARTICLE INFLUENCE[^\n]*\n\s*([\d]+\.[\d]+)', full_text, re.IGNORECASE)
    if ai_m:
        data["article_influence"] = float(ai_m.group(1))

    return data


def detect_issn_from_html(html: str) -> str | None:
    """HTML에서 ISSN을 추출해서 journal_meta.json 키 찾기"""
    m = re.search(r'\b(\d{4}-\d{3}[\dX])\b', html)
    return m.group(1) if m else None


def main():
    MHTML_DIR.mkdir(parents=True, exist_ok=True)

    # journal_meta.json 로드
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    else:
        print("ERROR: journal_meta.json not found"); return

    mhtml_files = list(MHTML_DIR.glob("*.mhtml")) + list(MHTML_DIR.glob("*.mht"))
    if not mhtml_files:
        print(f"MHTML 파일 없음. {MHTML_DIR} 에 저장해주세요.")
        print_save_guide()
        return

    print(f"MHTML 파일 {len(mhtml_files)}개 발견\n")
    updated = 0

    for fpath in sorted(mhtml_files):
        print(f"파싱: {fpath.name}")
        try:
            html = read_mhtml(fpath)
            jcr_data = parse_jcr_html(html)

            if not jcr_data:
                print(f"  → 데이터 추출 실패 (JS 미렌더링?)\n")
                continue

            # ISSN으로 매핑
            issn = detect_issn_from_html(html)
            if not issn or issn not in meta:
                # JCR 약어로 매핑 시도
                abbr = jcr_data.get("jcr_abbr", "")
                issn = JCR_ABBR_TO_ISSN.get(abbr.strip())

            if not issn or issn not in meta:
                print(f"  → 매핑 실패 (ISSN={issn})\n")
                continue

            # journal_meta.json 업데이트
            meta[issn]["jif"]              = jcr_data.get("jif")
            meta[issn]["jif_no_self"]      = jcr_data.get("jif_no_self")
            meta[issn]["total_cites_jcr"]  = jcr_data.get("total_citations_jcr")
            meta[issn]["quartile"]         = jcr_data.get("quartile")
            meta[issn]["jcr_rank"]         = jcr_data.get("jcr_rank")
            meta[issn]["jcr_rank_of"]      = jcr_data.get("jcr_rank_of")
            meta[issn]["jcr_category"]     = jcr_data.get("jcr_category")
            meta[issn]["cited_half_life"]  = jcr_data.get("cited_half_life")
            meta[issn]["oa_pct_jcr"]       = jcr_data.get("oa_pct_jcr")
            meta[issn]["jif_year"]         = 2024

            # None 값 제거
            meta[issn] = {k: v for k, v in meta[issn].items() if v is not None}

            name = meta[issn].get("name", issn)
            print(f"  ✅ {name}")
            for k in ["jif","quartile","jcr_rank","jcr_rank_of","total_cites_jcr","oa_pct_jcr"]:
                if k in meta[issn]:
                    print(f"     {k}: {meta[issn][k]}")
            print()
            updated += 1

        except Exception as e:
            print(f"  ERROR: {e}\n")

    if updated:
        META_PATH.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"✅ journal_meta.json 업데이트 완료 ({updated}개 저널)")
    else:
        print("업데이트된 저널 없음")


def print_save_guide():
    print("""
=== MHTML 저장 방법 ===
1. Chrome에서 JCR 로그인
2. 아래 URL 중 하나 열기
3. Ctrl+S → 파일 형식: "웹페이지, 단일 파일 (*.mhtml)"
4. 저장 위치: data/jcr_pages/

=== JCR 저널 URL 목록 ===
""")
    journals = [
        ("AUTOMAT CONSTR",        "Automation in Construction"),
        ("ADV ENG INFORM",        "Advanced Engineering Informatics"),
        ("CONSTR BUILD MATER",    "Construction and Building Materials"),
        ("J BUILD ENG",           "Journal of Building Engineering"),
        ("BUILDINGS-BASEL",       "Buildings"),
        ("KSCE J CIV ENG",        "KSCE Journal of Civil Engineering"),
        ("J INF TECHNOL CONSTR",  "J. of Information Technology in Construction"),
        ("J CONSTR ENG M",        "J. of Construction Engineering and Mgmt"),
        ("J STRUCT ENG",          "Journal of Structural Engineering"),
        ("CASE STUD CONSTR MAT",  "Case Studies in Construction Materials"),
        ("ENG CONSTR ARCHIT MAN", "Engineering Construction & Architectural Mgmt"),
        ("J COMPUT CIVIL ENG",    "Journal of Computing in Civil Engineering"),
        ("J CIV ENG MANAG",       "Journal of Civil Engineering and Management"),
        ("J GEOTECH GEOENVIRON",  "J. of Geotechnical and Geoenvironmental Eng"),
        ("ACI MATER J",           "ACI Materials Journal"),
        ("J ROCK MECH GEOTECH",   "J. of Rock Mechanics and Geotechnical Eng"),
        ("COMPUT AIDED CIV INF",  "Computer-Aided Civil & Infrastructure Eng"),
    ]
    for abbr, name in journals:
        url = f"https://jcr.clarivate.com/jcr-jp/journal-profile?journal={abbr.replace(' ','%20')}&year=2024"
        print(f"  {name}")
        print(f"  {url}\n")


if __name__ == "__main__":
    if "--guide" in sys.argv:
        print_save_guide()
    else:
        main()
