#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jcr_auto.py - JCR API 직접 수집 (경북대 IP + 세션 토큰)

방식:
  1. Playwright로 JCR 페이지 1회 접속 → 세션 ID + 쿠키 획득
  2. 이후 requests로 내부 API 직접 호출 (빠르고 안정적)

조건: 경북대 네트워크에서 실행

사용법:
  python jcr_auto.py          # 17개 전체
  python jcr_auto.py --test   # 1개만 테스트
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json, time, requests
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR  = Path(__file__).parent
META_PATH = BASE_DIR / "data" / "journal_meta.json"
BASE_API  = "https://jcr.clarivate.com/api/jcr3/journalprofile/v1"

JOURNALS = [
    ("AUTOMAT CONSTR",        "0926-5805", "Automation in Construction"),
    ("ADV ENG INFORM",        "1474-0346", "Advanced Engineering Informatics"),
    ("CONSTR BUILD MATER",    "0950-0618", "Construction and Building Materials"),
    ("J BUILD ENG",           "2352-7102", "Journal of Building Engineering"),
    ("BUILDINGS-BASEL",       "2075-5309", "Buildings"),
    ("FRONT BUILT ENVIRON",   "2297-3362", "Frontiers in Built Environment"),
    ("KSCE J CIV ENG",        "1226-7988", "KSCE Journal of Civil Engineering"),
    ("J INF TECHNOL CONSTR",  "1874-4753", "J. of Information Technology in Construction"),
    ("J CONSTR ENG M",        "0733-9364", "J. of Construction Engineering and Mgmt"),
    ("J STRUCT ENG",          "0733-9445", "Journal of Structural Engineering"),
    ("CASE STUD CONSTR MAT",  "2214-5095", "Case Studies in Construction Materials"),
    ("ENG CONSTR ARCHIT MA",  "0969-9988", "Engineering Construction & Architectural Mgmt"),
    ("J COMPUT CIVIL ENG",    "0887-3801", "Journal of Computing in Civil Engineering"),
    ("J CIV ENG MANAG",       "1392-3730", "Journal of Civil Engineering and Management"),
    ("J GEOTECH GEOENVIRON",  "1090-0241", "J. of Geotechnical and Geoenvironmental Eng"),
    ("ACI MATER J",           "0889-325X", "ACI Materials Journal"),
    ("J ROCK MECH GEOTECH",   "1674-7755", "J. of Rock Mechanics and Geotechnical Eng"),
    ("COMPUT-AIDED CIV INF",  "1093-9687", "Computer-Aided Civil & Infrastructure Eng"),
]


def get_session():
    """Playwright로 JCR 1회 접속해 세션 ID + 쿠키 획득"""
    print("세션 획득 중...")
    session_data = {"sid": None, "cookies": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=False)
        ctx  = browser.new_context()
        page = ctx.new_page()

        def on_request(req):
            if "jcr3/journalprofile" in req.url and "x-1p-inc-sid" in req.headers:
                session_data["sid"] = req.headers["x-1p-inc-sid"]

        page.on("request", on_request)
        page.goto(
            "https://jcr.clarivate.com/jcr-jp/journal-profile?journal=AUTOMAT%20CONSTR&year=2024",
            timeout=20000
        )
        time.sleep(8)

        for c in ctx.cookies():
            if c.get("value"):
                session_data["cookies"][c["name"]] = c["value"]

        browser.close()

    if not session_data["sid"]:
        raise RuntimeError("세션 ID 획득 실패 - 경북대 네트워크에서 실행하세요")

    print(f"세션 획득 완료 (쿠키 {len(session_data['cookies'])}개)\n")
    return session_data


def api_post(endpoint, payload, headers, cookies):
    r = requests.post(f"{BASE_API}/{endpoint}", json=payload,
                      headers=headers, cookies=cookies, timeout=15)
    return r.json() if r.status_code == 200 else None


def fetch_journal(abbr, issn, name, headers, cookies):
    print(f"  [{issn}] {name}")
    payload_base = {"journal": abbr}
    payload_year = {"journal": abbr, "year": "2024"}

    result = {}

    # Quartile + Rank (rank-byjif: 최신 연도 첫번째 항목)
    d = api_post("rank-byjif", payload_base, headers, cookies)
    if d and d.get("data"):
        for cat in d["data"]:
            rank_list = cat.get("rankByJif", [])
            if rank_list:
                # 가장 최신 연도 (첫번째) 사용
                r = rank_list[0]
                rank_str = r.get("rank", "")
                parts = rank_str.split("/")
                if len(parts) == 2:
                    result["jcr_rank"]    = int(parts[0])
                    result["jcr_rank_of"] = int(parts[1])
                result["quartile"]       = r.get("quartile")
                result["jif_percentile"] = float(r.get("jifPercentile", 0) or 0)
                result["jcr_category"]   = cat.get("category")
                break

    # JIF 값 (jif-values 엔드포인트)
    d = api_post("jif-values", payload_year, headers, cookies)
    if d and d.get("data"):
        for item in d["data"]:
            if "withSelfCites" in item:
                v = item["withSelfCites"].get("impactCurrent", "0") or "0"
                try: result["jif"] = float(v) or None
                except: pass
            if "withoutSelfCites" in item:
                v = item["withoutSelfCites"].get("impactCurrent", "0") or "0"
                try: result["jif_no_self"] = float(v) or None
                except: pass

    # Total Citations
    d = api_post("total-cites", payload_year, headers, cookies)
    if d and d.get("data"):
        for item in d["data"]:
            if isinstance(item, dict) and item.get("year") == "2024":
                result["total_cites_jcr"] = int(item.get("value", 0) or 0)
                break

    # Cited Half-Life
    d = api_post("cited-halflife", payload_year, headers, cookies)
    if d and d.get("data"):
        for item in d["data"]:
            if isinstance(item, dict) and item.get("year") == "2024":
                result["cited_half_life"] = float(item.get("value", 0) or 0) or None
                break

    # OA %
    d = api_post("open-access", payload_year, headers, cookies)
    if d and d.get("data"):
        oa = d["data"]
        if isinstance(oa, dict):
            result["oa_pct_jcr"] = float(oa.get("oaPercentage", 0) or 0) or None

    result["jif_year"] = 2024

    if result.get("jif"):
        print(f"    OK  JIF={result.get('jif')}  "
              f"Q={result.get('quartile')}  "
              f"Rank={result.get('jcr_rank')}/{result.get('jcr_rank_of')}  "
              f"Citations={result.get('total_cites_jcr')}")
    else:
        print(f"    ! JIF 없음 (JCR 미등재 or 약어 오류)")

    return result if result.get("jif") else None


def main():
    args      = sys.argv[1:]
    test_mode = "--test" in args

    if not META_PATH.exists():
        print("ERROR: journal_meta.json not found")
        return

    meta    = json.loads(META_PATH.read_text(encoding="utf-8"))
    targets = JOURNALS[:1] if test_mode else JOURNALS

    # 세션 1회 획득
    sess = get_session()
    headers = {
        "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type":  "application/json",
        "Accept":        "application/json, text/plain, */*",
        "x-1p-inc-sid":  sess["sid"],
        "Referer":       "https://jcr.clarivate.com/",
    }

    print(f"[JCR API 수집] 대상: {len(targets)}개\n")
    updated = 0

    for abbr, issn, name in targets:
        d = fetch_journal(abbr, issn, name, headers, sess["cookies"])
        if d and issn in meta:
            meta[issn].update(d)
            meta[issn] = {k: v for k, v in meta[issn].items() if v is not None}
            updated += 1
        time.sleep(0.5)  # API 부하 방지

    META_PATH.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n[완료] {updated}/{len(targets)}개 journal_meta.json 업데이트")


if __name__ == "__main__":
    main()
