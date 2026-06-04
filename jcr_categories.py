#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jcr_categories.py - JCR 카테고리별 전체 저널 목록 수집

대상 카테고리:
  - CONSTRUCTION & BUILDING TECHNOLOGY  (~95개)
  - ENGINEERING, CIVIL                  (~184개)

수집 데이터 (저널별):
  JIF, JIF Rank, JIF Quartile, JIF Percentile
  JCI, JCI Rank, JCI Quartile, JCI Percentile
  5yr JIF, Total Citations, ISSN, Publisher

조건: 경북대 네트워크에서 실행

사용법:
  python jcr_categories.py
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json, time, requests
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR   = Path(__file__).parent
OUT_PATH   = BASE_DIR / "data" / "jcr_categories.json"
META_PATH  = BASE_DIR / "data" / "journal_meta.json"

TARGET_CATEGORIES = {
    "CONSTRUCTION & BUILDING TECHNOLOGY",
    "ENGINEERING, CIVIL",
}
TARGET_CATEGORY_IDS = ["FA", "IM"]  # FA=Construction, IM=Engineering Civil

SEARCH_URL = "https://jcr.clarivate.com/api/jcr3/bwjournal/v1/search-result"


def get_session():
    print("세션 획득 중...")
    sid, cookies = None, {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        ctx  = browser.new_context()
        page = ctx.new_page()
        def on_req(req):
            nonlocal sid
            if "x-1p-inc-sid" in req.headers:
                sid = req.headers["x-1p-inc-sid"]
        page.on("request", on_req)
        page.goto("https://jcr.clarivate.com/jcr/browse-journals?editions=SCIE&splitEditions=false&year=2024",
                  timeout=20000)
        time.sleep(6)
        for c in ctx.cookies():
            if c.get("value"):
                cookies[c["name"]] = c["value"]
        browser.close()
    if not sid:
        raise RuntimeError("세션 ID 획득 실패 - 경북대 네트워크에서 실행하세요")
    print(f"세션 획득 완료\n")
    return sid, cookies


def fetch_all_journals(sid, cookies):
    h = {
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept":       "application/json",
        "x-1p-inc-sid": sid,
        "Referer":      "https://jcr.clarivate.com/",
    }

    page_size = 250
    start     = 1
    results   = []

    while True:
        payload = {
            "journalFilterParameters": {
                "query": "", "journals": [],
                "categories": TARGET_CATEGORY_IDS,  # FA + IM
                "publishers": [], "countryRegions": [],
                "citationIndexes": ["SCIE", "SSCI", "AHCI", "ESCI"],
                "jcrYear": 2024, "categorySchema": "WOS",
                "openAccess": "N", "jifQuartiles": [],
                "jifRanges": [], "jifNA": False,
                "jifPercentileRanges": [], "jciRanges": [],
                "oaRanges": [], "issnJ20s": []
            },
            "retrievalParameters": {
                "start":     start,
                "count":     page_size,
                "sortBy":    "jif2019",
                "sortOrder": "DESC"
            }
        }

        r = requests.post(SEARCH_URL, json=payload, headers=h, cookies=cookies, timeout=30)
        d = r.json()

        batch = d.get("data", [])
        total = d.get("totalCount", 0)

        results.extend(batch)
        print(f"  {start}~{start+len(batch)-1} / {total}  누적: {len(results)}개")

        start += page_size
        if start > total or not batch:
            break
        time.sleep(0.3)

    return results


def build_output(journals):
    """저널 목록 → 구조화된 딕셔너리"""
    out = {}
    for j in journals:
        issn = j.get("issn", "").strip()
        if not issn:
            continue

        cats_q = j.get("categoryQuartiles", [])

        # 카테고리별 지표 추출
        cat_data = {}
        for cq in cats_q:
            cat = cq.get("category", "")
            if cat in TARGET_CATEGORIES:
                cat_data[cat] = {
                    "jif_rank":      cq.get("jifRank"),
                    "jif_quartile":  cq.get("quartile") or cq.get("jciQuartile"),
                    "jif_percentile":cq.get("jifPercentile"),
                    "jci_rank":      cq.get("jciRank"),
                    "jci_quartile":  cq.get("jciQuartile"),
                    "jci_percentile":cq.get("jciPercentile"),
                    "ais_rank":      cq.get("aisRank"),
                    "ais_quartile":  cq.get("aisQuartile"),
                    "5yr_jif_quartile": cq.get("fiveYearJifQuartile"),
                }

        out[issn] = {
            "issn":         issn,
            "eissn":        j.get("eissn", "").strip(),
            "name":         j.get("journalName", ""),
            "abbr":         j.get("abbrJournal", ""),
            "publisher":    j.get("publisher", ""),
            "categories":   j.get("category", []),
            "jcr_year":     j.get("jcrYear"),
            # 전체 지표
            "jif":          _f(j.get("jif2019")),
            "jif_5yr":      _f(j.get("jif5Years")),
            "jif_no_self":  _f(j.get("jifWithoutSelfCites")),
            "jif_percentile": _f(j.get("jifPercentile")),
            "jif_rank":     j.get("jifRank"),
            "jif_quartile": j.get("quartile"),
            "jci":          _f(j.get("jci")),
            "jci_percentile": _f(j.get("jciPercentile")),
            "jci_rank":     j.get("jciRank"),
            "jci_quartile": j.get("jciQuartile"),
            "total_cites":  _i(j.get("totalCites")),
            "citable_items": _i(j.get("citableItems")),
            "oa_pct":       _f(j.get("percentageOAGold")),
            # 카테고리별 세부 순위
            "category_ranks": cat_data,
        }
        # None 제거
        out[issn] = {k: v for k, v in out[issn].items() if v is not None}

    return out


def _f(v):
    try: return float(v) if v and str(v) not in ("N/A","") else None
    except: return None

def _i(v):
    try: return int(str(v).replace(",","")) if v else None
    except: return None


def update_journal_meta(out):
    """journal_meta.json에 JCR 데이터 병합"""
    if not META_PATH.exists():
        return
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    updated = 0
    for issn, jcr in out.items():
        if issn in meta:
            # JCR 공식 필드 업데이트
            for field in ["jif","jif_5yr","jif_no_self","jif_percentile","jif_rank","jif_quartile",
                          "jci","jci_percentile","jci_rank","jci_quartile","total_cites","oa_pct","category_ranks"]:
                if jcr.get(field) is not None:
                    meta[issn][field] = jcr[field]
            meta[issn]["jcr_year"] = 2024
            meta[issn] = {k: v for k, v in meta[issn].items() if v is not None}
            updated += 1
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"journal_meta.json 업데이트: {updated}개")


def main():
    sid, cookies = get_session()
    print("전체 저널 수집 중 (카테고리 필터링)...")
    journals = fetch_all_journals(sid, cookies)
    print(f"\n대상 저널 합계: {len(journals)}개")

    # 카테고리별 집계
    from collections import Counter
    cat_count = Counter()
    for j in journals:
        for c in j.get("category", []):
            if c in TARGET_CATEGORIES:
                cat_count[c] += 1
    for cat, cnt in cat_count.items():
        print(f"  {cat}: {cnt}개")

    print("\n데이터 구조화 중...")
    out = build_output(journals)

    # jcr_categories.json 저장
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {OUT_PATH}  ({len(out)}개 저널)")

    # journal_meta.json 병합
    update_journal_meta(out)

    # 상위 10개 미리보기
    print("\n[JIF 상위 10개]")
    top10 = sorted(out.values(), key=lambda x: x.get("jif", 0) or 0, reverse=True)[:10]
    for j in top10:
        print(f"  {j.get('jif'):5}  {j.get('jif_quartile','?')}  {j.get('abbr','')[:25]:<25}  {','.join(j.get('categories',[]))}")


if __name__ == "__main__":
    main()
