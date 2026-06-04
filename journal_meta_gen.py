#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
journal_meta_gen.py — OpenAlex sources API로 전체 저널 메타데이터 생성

journals.json(수집 저널) + jcr_categories.json(JCR 데이터) 기준으로
OpenAlex /sources 에서 h-index, i10, OA, APC, topics, 연도별 등 수집
→ journal_meta.json 갱신 (JCR 필드 병합)
"""
import sys, io, json, os, time, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
JOURNALS  = os.path.join(BASE_DIR, "data", "journals.json")
JCR_CATS  = os.path.join(BASE_DIR, "data", "jcr_categories.json")
META_PATH = os.path.join(BASE_DIR, "data", "journal_meta.json")

# 출판사 도시 (알려진 것만)
PUB_CITY = {
    "Elsevier": "Amsterdam", "Elsevier BV": "Amsterdam",
    "Wiley": "Hoboken NJ", "Wiley-Blackwell": "Hoboken NJ",
    "MDPI": "Basel", "MDPI AG": "Basel",
    "Springer": "Berlin", "Springer Nature": "Berlin", "Springer Science+Business Media": "Berlin",
    "Frontiers": "Lausanne", "Frontiers Media": "Lausanne", "Frontiers Media SA": "Lausanne",
    "Taylor & Francis": "London", "Emerald": "Bingley", "Emerald Publishing": "Bingley",
    "ASCE": "Reston VA", "American Society of Civil Engineers": "Reston VA",
    "ACI": "Farmington Hills MI", "American Concrete Institute": "Farmington Hills MI",
    "Sage": "Thousand Oaks CA", "SAGE Publications": "Thousand Oaks CA",
    "IEEE": "Piscataway NJ", "Hindawi": "London", "Thomas Telford": "London",
    "ICE Publishing": "London", "De Gruyter": "Berlin", "ASTM": "West Conshohocken PA",
}

def log(m):
    print(m, flush=True)

def fetch_source(issn):
    """OpenAlex sources by ISSN"""
    try:
        r = requests.get(f"https://api.openalex.org/sources/issn:{issn}", timeout=20)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def parse_source(s, issn):
    if not s:
        return None
    summ = s.get("summary_stats", {}) or {}
    cby  = s.get("counts_by_year", []) or []
    apc  = s.get("apc_usd")
    apc_prices = s.get("apc_prices", []) or []
    host = s.get("host_organization_name", "") or ""
    topics = [t.get("display_name","") for t in (s.get("topics", []) or [])[:5] if t.get("display_name")]
    issn_l = s.get("issn_l", issn)
    issns  = s.get("issn", []) or [issn]

    m = {
        "issn_l": issn_l,
        "issn": issns,
        "name": s.get("display_name", ""),
        "publisher": host,
        "country": s.get("country_code", ""),
        "homepage": s.get("homepage_url", ""),
        "h_index": summ.get("h_index"),
        "i10_index": summ.get("i10_index"),
        "if2y": round(summ.get("2yr_mean_citedness", 0), 2) if summ.get("2yr_mean_citedness") else None,
        "works": s.get("works_count"),
        "cites": s.get("cited_by_count"),
        "is_oa": bool(s.get("is_oa")),
        "is_doaj": bool(s.get("is_in_doaj")),
        "is_core": bool(s.get("is_core")),
        "apc_usd": apc,
        "apc_prices": apc_prices,
        "topics": topics,
        "counts_by_year": cby,
        "pub_city": PUB_CITY.get(host, PUB_CITY.get(host.replace(" BV","").replace(" AG","").strip(), "")),
    }
    # first/last year
    years = [c["year"] for c in cby if c.get("year")]
    if years:
        m["last_year"] = max(years)
    # oa_works
    oa = next((c for c in cby), None)
    # 누적 oa는 sources에 없으므로 생략

    return {k: v for k, v in m.items() if v is not None and v != ""}

def main():
    journals = json.load(open(JOURNALS, encoding="utf-8"))
    jcr = json.load(open(JCR_CATS, encoding="utf-8")) if os.path.exists(JCR_CATS) else {}

    # 기존 meta 로드 (있으면 보존, 갱신)
    meta = json.load(open(META_PATH, encoding="utf-8")) if os.path.exists(META_PATH) else {}

    # 수집 저널 ISSN 목록
    issns = []
    for j in journals:
        issn = (j.get("issn") or "").strip()
        if issn:
            issns.append(issn)
    issns = list(dict.fromkeys(issns))  # 중복 제거
    log(f"대상 저널: {len(issns)}개\n")

    ok, fail = 0, 0
    for i, issn in enumerate(issns, 1):
        s = fetch_source(issn)
        parsed = parse_source(s, issn)
        if not parsed:
            log(f"  [{i}/{len(issns)}] {issn} — OpenAlex 미발견")
            fail += 1
            time.sleep(0.15)
            continue

        # ISSN-L 키로 저장 (jcr_categories와 맞춤)
        key = issn
        # 기존 항목과 병합
        entry = meta.get(key, {})
        entry.update(parsed)

        # JCR 데이터 병합
        jc = jcr.get(issn) or jcr.get(parsed.get("issn_l",""))
        if jc:
            for f in ["jif","jif_5yr","jif_no_self","jif_percentile","jif_rank","jif_quartile",
                      "jci","jci_percentile","jci_rank","jci_quartile","total_cites",
                      "categories","jcr_year","category_ranks"]:
                if jc.get(f) is not None:
                    entry[f] = jc[f]

        meta[key] = {k: v for k, v in entry.items() if v is not None}
        log(f"  [{i}/{len(issns)}] {parsed.get('name','')[:40]:<40} h={parsed.get('h_index')} works={parsed.get('works')}")
        ok += 1
        time.sleep(0.15)

    json.dump(meta, open(META_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log(f"\n[완료] {ok}개 성공, {fail}개 실패 → journal_meta.json ({len(meta)}개 항목)")

if __name__ == "__main__":
    main()
