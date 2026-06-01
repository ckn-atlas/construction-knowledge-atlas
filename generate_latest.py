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
    "0926-5805","1474-0346","0950-0618","2352-7102",
    "2075-5309","2297-3362","1226-7988","1874-4753","0733-9364",
]
GROUP_MAP = {
    "computer science":"AI","artificial intelligence":"AI","machine learning":"AI","deep learning":"AI",
    "computer vision":"Vision","image processing":"Vision","pattern recognition":"Vision",
    "materials science":"Material","composite material":"Material","polymer":"Material",
    "civil engineering":"Structural","structural engineering":"Structural","mechanics":"Structural",
    "environmental science":"Eco","sustainability":"Eco","green building":"Eco",
    "construction management":"Mgmt","safety":"Mgmt",
    "building information modeling":"BIM",
    "geotechnical engineering":"Geo","geology":"Geo",
    "robotics":"Robot","automation":"Robot",
    "digital twin":"DT",
    "sensor":"Sensing","remote sensing":"Sensing",
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

def extract_query(concepts):
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

def main():
    args = sys.argv[1:]
    if "--day" in args:
        cutoff = str(datetime.now().date())
    elif "--week" in args:
        cutoff = str((datetime.now()-timedelta(days=7)).date())
    else:
        cutoff = str((datetime.now()-timedelta(days=30)).date())

    log(f"Querying OpenAlex from {cutoff} (has_abstract=true)...")
    params = {
        "filter": f"primary_location.source.issn:{'|'.join(JOURNAL_ISSNS)},from_publication_date:{cutoff},has_abstract:true",
        "sort": "fwci:desc",
        "per-page": 100,
        "select": "id,title,publication_date,fwci,cited_by_count,doi,concepts,abstract_inverted_index,open_access,primary_location",
    }
    r = requests.get("https://api.openalex.org/works", params=params, timeout=30)
    papers = r.json().get("results", [])
    log(f"Found: {len(papers)} papers")

    theme_top = {}
    for w in papers:
        g = get_group(w.get("concepts"))
        if not g: continue
        fwci = w.get("fwci") or 0
        prev = theme_top.get(g)
        if not prev or fwci > (prev.get("fwci") or 0):
            theme_top[g] = w

    results = []
    for group, w in sorted(theme_top.items()):
        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
        if not abstract: continue
        query = extract_query(w.get("concepts"))
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
