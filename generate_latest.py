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

def _load_issns():
    import json, os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jcr_categories.json")
    if os.path.isfile(p):
        try:
            return list(json.load(open(p, encoding="utf-8")).keys())
        except Exception:
            pass
    return ["0926-5805","1474-0346","0950-0618","2352-7102",
            "2075-5309","2297-3362","1226-7988","1874-4753","0733-9364"]

JOURNAL_ISSNS = _load_issns()
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
    line = f"[{ts}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii","replace").decode("ascii"), flush=True)

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

MAILTO = "ckn.atlas@gmail.com"  # OpenAlex polite pool

def _get(url, params, timeout=30, retries=4):
    import time as _t
    params = dict(params); params["mailto"] = MAILTO
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                _t.sleep(5 * (attempt+1)); continue
            return r
        except Exception:
            _t.sleep(2)
    return None

def fetch_papers(cutoff, batch=40):
    """ISSN 목록이 길면 URL 길이 초과 → 배치로 나눠 조회 후 병합"""
    select = ("id,title,publication_date,fwci,cited_by_count,doi,concepts,"
              "abstract_inverted_index,open_access,primary_location")
    all_results = []
    seen = set()
    for k in range(0, len(JOURNAL_ISSNS), batch):
        chunk = JOURNAL_ISSNS[k:k+batch]
        params = {
            "filter": f"primary_location.source.issn:{'|'.join(chunk)},from_publication_date:{cutoff},has_abstract:true",
            "sort": "fwci:desc",
            "per-page": 100,
            "select": select,
        }
        try:
            r = _get("https://api.openalex.org/works", params)
            if not r or r.status_code != 200:
                continue
            for w in r.json().get("results", []):
                wid = w.get("id")
                if wid and wid in seen:
                    continue
                if wid:
                    seen.add(wid)
                all_results.append(w)
        except Exception:
            continue
        time.sleep(0.2)
    # 전체 FWCI 내림차순 정렬
    all_results.sort(key=lambda w: (w.get("fwci") or 0), reverse=True)
    return all_results

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

    # 기존 latest.json에서 DOI 기반 ck_take / grok_image 캐시 로드
    cached_ai = {}  # doi → {"ck_take": str, "grok_image": str}
    if os.path.exists(OUTPUT_PATH):
        try:
            old = json.load(open(OUTPUT_PATH, encoding="utf-8"))
            for p in old.get("papers", []):
                doi = p.get("doi", "")
                if doi and (p.get("ck_take") or p.get("grok_image")):
                    cached_ai[doi] = {
                        "ck_take":    p.get("ck_take", ""),
                        "grok_image": p.get("grok_image", ""),
                    }
        except Exception:
            pass
    log(f"AI 캐시 로드: {len(cached_ai)}개 DOI")

    # 033_AICollabWorkflow 경로
    COLLAB_DIR   = os.path.join(BASE_DIR, "..", "033_AICollabWorkflow")
    CODEX_INBOX  = os.path.join(COLLAB_DIR, "inbox", "codex")
    CODEX_OUTBOX = os.path.join(COLLAB_DIR, "outbox", "codex")
    GROK_INBOX   = os.path.join(COLLAB_DIR, "inbox", "grok")

    def _next_task_id():
        """outbox/codex의 RESULT-NNN.md 최대 번호 + 1"""
        max_n = 0
        for d in [CODEX_OUTBOX, CODEX_INBOX, GROK_INBOX]:
            if not os.path.isdir(d): continue
            for fn in os.listdir(d):
                import re as _re
                m = _re.search(r"(\d{3,})", fn)
                if m: max_n = max(max_n, int(m.group(1)))
        return max_n + 1

    def _write_codex_task(task_id, title, abstract, journal):
        os.makedirs(CODEX_INBOX, exist_ok=True)
        path = os.path.join(CODEX_INBOX, f"TASK-{task_id:03d}.md")
        content = f"""# TASK-{task_id:03d}: CKAtlas Paper Summary

## Instructions
Read the paper abstract below and write ONE sentence (max 25 words) as a casual, insightful comment from a construction research expert's perspective. Write in English only.

Output format (exactly):
SUMMARY: <your one sentence here>

## Paper
Title: {title}
Journal: {journal}
Abstract:
{abstract[:800]}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _write_grok_task(task_id, title, group_label, keywords):
        os.makedirs(GROK_INBOX, exist_ok=True)
        path = os.path.join(GROK_INBOX, f"TASK-{task_id:03d}.md")
        kw_str = ", ".join(keywords[:4]) if keywords else group_label
        content = f"""# TASK-{task_id:03d}: CKAtlas Background Image

## Instructions
Generate a high-quality photorealistic background image for a construction research paper card.
Theme: {group_label}
Keywords: {kw_str}
Style: professional, wide landscape (1200x675), no text overlay, scientific/engineering atmosphere.

Save the image as: data/social/grok_images/{group_label.lower().replace(' ','_')}_{task_id:03d}.jpg

## Paper context
{title}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _read_codex_result(task_id):
        path = os.path.join(CODEX_OUTBOX, f"RESULT-{task_id:03d}.md")
        if not os.path.exists(path): return ""
        for line in open(path, encoding="utf-8"):
            if line.startswith("SUMMARY:"):
                return line.replace("SUMMARY:", "").strip()
        return ""

    results = []
    task_counter = _next_task_id()
    grok_img_dir = os.path.join(BASE_DIR, "data", "social", "grok_images")
    os.makedirs(grok_img_dir, exist_ok=True)

    for group, w in sorted(theme_top.items()):
        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
        if not abstract: continue
        query = extract_query(w.get("concepts"), group)
        image = fetch_unsplash(query)
        time.sleep(0.5)
        loc = w.get("primary_location") or {}
        journal = (loc.get("source") or {}).get("display_name","")
        doi = w.get("doi", "")
        keywords = [c["display_name"] for c in (w.get("concepts") or []) if c.get("score",0)>=0.3][:5]
        group_label = GROUP_KO.get(group, group)

        # AI 캐시 확인 (DOI 기준)
        cached = cached_ai.get(doi, {})
        ck_take   = cached.get("ck_take", "")
        grok_image = cached.get("grok_image", "")

        # 캐시 없으면 → Codex 태스크 생성
        if not ck_take and os.path.isdir(COLLAB_DIR):
            _write_codex_task(task_counter, w.get("title",""), abstract, journal)
            log(f"  [{group}] Codex 태스크 생성: TASK-{task_counter:03d}.md")
            # 즉시 결과 확인 (이미 처리된 경우)
            ck_take = _read_codex_result(task_counter)
            if ck_take:
                log(f"  [{group}] Codex 결과 즉시 로드")

        # Grok 이미지 캐시 없으면 → Grok 태스크 생성
        if not grok_image and os.path.isdir(COLLAB_DIR):
            _write_grok_task(task_counter, w.get("title",""), group_label, keywords)
            # 기존 grok_images 폴더에서 해당 그룹 이미지 확인
            expected = os.path.join(grok_img_dir, f"{group_label.lower().replace(' ','_')}_{task_counter:03d}.jpg")
            if os.path.exists(expected):
                grok_image = f"data/social/grok_images/{group_label.lower().replace(' ','_')}_{task_counter:03d}.jpg"

        task_counter += 1

        results.append({
            "group": group,
            "group_label": group_label,
            "title": w.get("title",""),
            "journal": journal,
            "date": w.get("publication_date",""),
            "fwci": w.get("fwci"),
            "citations": w.get("cited_by_count",0),
            "oa": bool((w.get("open_access") or {}).get("is_oa")),
            "doi": doi,
            "keywords": keywords,
            "abstract": abstract,
            "image": image,
            "ck_take": ck_take,
            "grok_image": grok_image,
        })
        log(f"  [{group}] FWCI={w.get('fwci')} | {w.get('title','')[:50]}")

    # 결과가 비었으면(rate limit 등) 기존 파일 보존 — 빈 데이터로 덮어쓰지 않음
    if not results:
        log("WARNING: 결과 0개 — 기존 latest.json 유지 (덮어쓰기 안 함)")
        return

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
