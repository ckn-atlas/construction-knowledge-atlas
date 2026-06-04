#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_latest.py — OpenAlex에서 직접 조회, has_abstract=true 논문만
사용법:
  python generate_latest.py              # 최근 30일
  python generate_latest.py --week      # 최근 7일
  python generate_latest.py --day       # 오늘
"""
import json, os, sys, time, requests
from datetime import datetime, timedelta

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH  = os.path.join(BASE_DIR, "data", "latest.json")
UNSPLASH_KEY = "s4ZnXZruiQfi-8HQp_7DtcoKU7-qevTvhMuktNV0K-s"

JOURNAL_ISSNS = [
    # 기존 9개
    "0926-5805","1474-0346","0950-0618","2352-7102",
    "2075-5309","2297-3362","1226-7988","1874-4753","0733-9364",
    # 신규 9개
    "0733-9445","2214-5095","0969-9988","0887-3801",
    "1392-3730","1090-0241","0889-325X","1674-7755","1093-9687",
]
GROUP_MAP = {
    # AI / ML
    "computer science":"AI","artificial intelligence":"AI","machine learning":"AI",
    "deep learning":"AI","neural network":"AI","natural language processing":"AI",
    "large language model":"AI","reinforcement learning":"AI","data mining":"AI",
    # Vision
    "computer vision":"Vision","image processing":"Vision","pattern recognition":"Vision",
    "object detection":"Vision","point cloud":"Vision","3d reconstruction":"Vision",
    "photogrammetry":"Vision","lidar":"Vision","slam":"Vision",
    # Material
    "materials science":"Material","composite material":"Material","polymer":"Material",
    "concrete":"Material","steel":"Material","cement":"Material",
    "construction material":"Material","fiber reinforced":"Material",
    # Structural
    "civil engineering":"Structural","structural engineering":"Structural","mechanics":"Structural",
    "structural health monitoring":"Structural","finite element":"Structural",
    "bridge":"Structural","seismic":"Structural","load":"Structural",
    # Eco / Energy
    "environmental science":"Eco","sustainability":"Eco","green building":"Eco",
    "energy efficiency":"Eco","life cycle assessment":"Eco","carbon emission":"Eco",
    "indoor environment":"Eco","thermal comfort":"Eco",
    # Management
    "construction management":"Mgmt","safety":"Mgmt","project management":"Mgmt",
    "risk management":"Mgmt","scheduling":"Mgmt","cost estimation":"Mgmt",
    "lean construction":"Mgmt","supply chain":"Mgmt",
    # BIM
    "building information modeling":"BIM","bim":"BIM","ifc":"BIM",
    "facility management":"BIM","smart building":"BIM",
    # Geo
    "geotechnical engineering":"Geo","geology":"Geo","soil":"Geo",
    "foundation":"Geo","tunnel":"Geo","underground":"Geo","excavation":"Geo",
    "slope":"Geo","pile":"Geo",
    # Robotics
    "robotics":"Robot","automation":"Robot","autonomous":"Robot",
    "unmanned aerial vehicle":"Robot","drone":"Robot","uav":"Robot",
    "construction robot":"Robot","exoskeleton":"Robot",
    # Digital Twin
    "digital twin":"DT","cyber-physical":"DT","simulation":"DT",
    "virtual reality":"DT","augmented reality":"DT","mixed reality":"DT",
    # Sensing / IoT
    "sensor":"Sensing","remote sensing":"Sensing","iot":"Sensing",
    "internet of things":"Sensing","wireless sensor":"Sensing",
    "monitoring":"Sensing","accelerometer":"Sensing","strain gauge":"Sensing",
}
GROUP_KO = {
    "AI":"AI/ML","Vision":"Vision","Material":"Material","Structural":"Structural",
    "Eco":"Eco/Energy","Mgmt":"Management","BIM":"BIM/Info","Geo":"Geo",
    "Robot":"Robotics","DT":"Digital Twin","Sensing":"Sensing"
}

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def reconstruct_abstract(inv):
    if not inv: return None
    pos = sorted([(p,w) for w,locs in inv.items() for p in locs])
    return " ".join(w for _,w in pos)

def get_group(concepts):
    for c in sorted(concepts or [], key=lambda x: -x.get("score",0)):
        if c.get("score",0) < 0.25: break
        g = GROUP_MAP.get(c.get("display_name","").lower())
        if g: return g
    return None

# 테마별 Unsplash 검색어 (히트율 높은 구체적 키워드)
GROUP_IMG_QUERY = {
    "AI":         "artificial intelligence technology",
    "Vision":     "computer vision camera surveillance",
    "Material":   "construction materials concrete",
    "Structural": "bridge structural engineering",
    "Eco":        "green building sustainable energy",
    "Mgmt":       "construction site workers",
    "BIM":        "building architecture blueprint",
    "Geo":        "underground tunnel excavation",
    "Robot":      "construction robot automation",
    "DT":         "digital twin smart city",
    "Sensing":    "sensor monitoring technology",
}

def extract_query(concepts, group=None):
    # 그룹별 기본 검색어 우선
    if group and group in GROUP_IMG_QUERY:
        return GROUP_IMG_QUERY[group]
    kws = [c["display_name"] for c in
           sorted([c for c in (concepts or []) if c.get("score",0)>=0.4],
                  key=lambda c: c.get("level",0), reverse=True)[:3]]
    return " ".join(kws) if kws else "construction technology"

def fetch_unsplash(query):
    try:
        r = requests.get("https://api.unsplash.com/search/photos",
            params={"query":query,"per_page":1,"orientation":"landscape"},
            headers={"Authorization":f"Client-ID {UNSPLASH_KEY}"}, timeout=10)
        photos = r.json().get("results",[])
        if not photos: return None
        p = photos[0]
        try: requests.get(p["links"]["download_location"],
                headers={"Authorization":f"Client-ID {UNSPLASH_KEY}"}, timeout=5)
        except: pass
        return {
            "url": p["urls"]["regular"],
            "thumb": p["urls"]["thumb"],
            "alt": p.get("alt_description",""),
            "photographer": p["user"]["name"],
            "photographer_url": p["user"]["links"]["html"],
            "unsplash_url": p["links"]["html"],
        }
    except: return None

ALL_GROUPS = list(GROUP_KO.keys())  # 11개 테마

def fetch_papers(cutoff):
    params = {
        "filter": f"primary_location.source.issn:{'|'.join(JOURNAL_ISSNS)},from_publication_date:{cutoff},has_abstract:true",
        "sort": "fwci:desc",
        "per-page": 200,
        "select": "id,title,publication_date,fwci,cited_by_count,doi,concepts,abstract_inverted_index,open_access,primary_location",
    }
    r = requests.get("https://api.openalex.org/works", params=params, timeout=30)
    return r.json().get("results", [])

def build_theme_top(papers):
    theme_top = {}
    for w in papers:
        g = get_group(w.get("concepts"))
        if not g: continue
        fwci = w.get("fwci") or 0
        prev = theme_top.get(g)
        if not prev or fwci > (prev.get("fwci") or 0):
            theme_top[g] = w
    return theme_top

def main():
    args = sys.argv[1:]
    if "--day" in args:
        days = 1
    elif "--week" in args:
        days = 7
    else:
        days = 30

    cutoff = str((datetime.now()-timedelta(days=days)).date())
    log(f"Querying OpenAlex from {cutoff} ({days}d, has_abstract=true)...")
    papers = fetch_papers(cutoff)
    log(f"Found: {len(papers)} papers (primary period)")
    theme_top = build_theme_top(papers)

    # 누락 테마 → 90일 fallback
    missing = [g for g in ALL_GROUPS if g not in theme_top]
    if missing:
        log(f"Missing themes: {missing} → fallback 90d")
        cutoff90 = str((datetime.now()-timedelta(days=90)).date())
        papers90 = fetch_papers(cutoff90)
        log(f"Found: {len(papers90)} papers (90d fallback)")
        fallback_top = build_theme_top(papers90)
        for g in missing:
            if g in fallback_top:
                theme_top[g] = fallback_top[g]
                log(f"  [{g}] filled via fallback")

    # 여전히 누락 → 365일 fallback
    still_missing = [g for g in ALL_GROUPS if g not in theme_top]
    if still_missing:
        log(f"Still missing: {still_missing} → fallback 365d")
        cutoff365 = str((datetime.now()-timedelta(days=365)).date())
        papers365 = fetch_papers(cutoff365)
        fallback365 = build_theme_top(papers365)
        for g in still_missing:
            if g in fallback365:
                theme_top[g] = fallback365[g]
                log(f"  [{g}] filled via 365d fallback")

    results = []
    for group, w in sorted(theme_top.items()):
        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
        if not abstract: continue
        query = extract_query(w.get("concepts"), group)
        image = fetch_unsplash(query)
        time.sleep(0.5)
        loc = w.get("primary_location") or {}
        journal = (loc.get("source") or {}).get("display_name","")
        results.append({
            "group": group,
            "group_label": GROUP_KO.get(group, group),
            "title": w.get("title",""),
            "journal": journal,
            "date": w.get("publication_date",""),
            "fwci": w.get("fwci"),
            "citations": w.get("cited_by_count",0),
            "oa": bool((w.get("open_access") or {}).get("is_oa")),
            "doi": w.get("doi",""),
            "keywords": [c["display_name"] for c in (w.get("concepts") or []) if c.get("score",0)>=0.3][:5],
            "abstract": abstract,
            "image": image,
        })
        log(f"  [{group}] FWCI={w.get('fwci')} | {w.get('title','')[:50]}")

    output = {
        "generated_at": datetime.now().isoformat(),
        "date_from": cutoff,
        "total": len(results),
        "papers": results,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log(f"Saved: {OUTPUT_PATH} ({len(results)} papers)")

if __name__ == "__main__":
    main()
