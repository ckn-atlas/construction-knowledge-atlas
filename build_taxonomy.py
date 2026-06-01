# -*- coding: utf-8 -*-
"""
build_taxonomy.py
─────────────────
Ollama 로컬 LLM을 사용해 OpenAlex 원시 키워드를 자동 분류한다.

생성물: taxonomy.json
  {
    "raw_keyword": {
      "canon":    "표준 노드명 (영문)",
      "group":    "AI | Vision | Sensing | BIM | DT | Robot | Material | Structural | Geo | Eco | Mgmt",
      "parent":   "상위 노드명 또는 null",
      "label_ko": "한글 축약 라벨"
    }, ...
  }

사용법:
  python build_taxonomy.py                    # _raw.json 기반 전체 분류
  python build_taxonomy.py --model qwen2.5:7b # 모델 지정
  python build_taxonomy.py --batch 10         # 배치 크기 조정 (기본 15)
  python build_taxonomy.py --dry-run          # API 호출 없이 추출된 키워드만 확인
"""

import json
import os
import re
import sys
import time
import argparse
from collections import Counter

# ── 설정 ──────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RAW_PATH    = os.path.join(BASE_DIR, "data", "_raw.json")
TAXO_PATH   = os.path.join(BASE_DIR, "taxonomy.json")
OLLAMA_URL  = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "mistral:7b"
BATCH_SIZE  = 15   # 로컬 모델은 작은 배치가 안정적

GROUPS = ["AI", "Vision", "Sensing", "BIM", "DT", "Robot",
          "Material", "Structural", "Geo", "Eco", "Mgmt"]

# ── 3단계 위계: 테마 → 중분류 → 세부기술 ────────────────────────────────
# 각 테마별 중분류(Level 2) 카테고리 — LLM이 parent를 이 중에서 선택하도록 유도
MID_CATEGORIES = {
    "AI":         ["Machine Learning", "Deep Learning", "NLP", "Generative AI",
                   "Explainable AI", "Anomaly Detection"],
    "Vision":     ["Computer Vision", "Image Processing", "Object Detection",
                   "3D Vision", "Video Analysis"],
    "Sensing":    ["IoT & Sensors", "Point Cloud Processing", "Remote Sensing",
                   "Structural Health Monitoring", "SLAM & Localization"],
    "BIM":        ["BIM", "Digital Documentation", "Knowledge Management",
                   "Interoperability"],
    "DT":         ["Digital Twin", "Simulation", "Cyber-Physical Systems"],
    "Robot":      ["Robotics", "Autonomous Systems", "Additive Manufacturing",
                   "Drone & UAV"],
    "Material":   ["Cementitious Materials", "Composite Materials",
                   "Asphalt & Pavement", "Material Testing", "Sustainable Materials"],
    "Structural": ["Structural Analysis", "Seismic Engineering",
                   "Fatigue & Fracture", "Structural Dynamics"],
    "Geo":        ["Geotechnical Engineering", "Tunneling & Underground",
                   "Foundation Engineering", "Slope & Soil"],
    "Eco":        ["Sustainability", "Building Energy", "Carbon & Emissions",
                   "Green Building"],
    "Mgmt":       ["Project Management", "Construction Safety", "Cost & Scheduling",
                   "Supply Chain", "Risk Management"],
}

# ── Few-shot 예시 포함 프롬프트 ────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a construction technology research expert. "
    "Classify construction/engineering keywords into a 3-level hierarchy: "
    "Level1(group/theme) → Level2(mid-category) → Level3(this keyword=canon). "
    "Always respond with a valid JSON array only. No explanation, no markdown."
)

FEW_SHOT = [
    # Level 3 세부기술 → Level 2 중분류
    {"raw": "convolutional neural network",
     "canon": "CNN", "group": "AI",
     "mid_cat": "Deep Learning", "parent": "Deep Learning",
     "level": 3, "label_ko": "합성곱신경망"},
    {"raw": "deep learning",
     "canon": "Deep Learning", "group": "AI",
     "mid_cat": "Machine Learning", "parent": "Machine Learning",
     "level": 2, "label_ko": "딥러닝"},
    {"raw": "carbon fiber reinforced polymer",
     "canon": "CFRP", "group": "Material",
     "mid_cat": "Composite Materials", "parent": "Composite Materials",
     "level": 3, "label_ko": "탄소섬유복합재"},
    {"raw": "geopolymer",
     "canon": "Geopolymer", "group": "Material",
     "mid_cat": "Cementitious Materials", "parent": "Cementitious Materials",
     "level": 3, "label_ko": "지오폴리머"},
    {"raw": "slope failure",
     "canon": "Slope Stability", "group": "Geo",
     "mid_cat": "Slope & Soil", "parent": "Slope & Soil",
     "level": 3, "label_ko": "사면안정"},
    {"raw": "building energy simulation",
     "canon": "Building Energy Simulation", "group": "Eco",
     "mid_cat": "Building Energy", "parent": "Building Energy",
     "level": 3, "label_ko": "건물에너지시뮬레이션"},
]

def _mid_cat_hint() -> str:
    lines = ["Mid-category options per group (use these as parent values):"]
    for g, cats in MID_CATEGORIES.items():
        lines.append(f"  {g}: {' | '.join(cats)}")
    return "\n".join(lines)

GROUP_DESC = (
    "3-Level Hierarchy:\n"
    "  Level 1 (group)    = Theme: AI | Vision | Sensing | BIM | DT | Robot | "
    "Material | Structural | Geo | Eco | Mgmt\n"
    "  Level 2 (mid_cat)  = Mid-category within the theme (see list below)\n"
    "  Level 3 (canon)    = This specific keyword — assign parent = mid_cat\n"
    "  If the keyword itself IS a mid-category concept, set level=2 and parent=null.\n\n"
    + _mid_cat_hint() + "\n\n"
    "Group definitions:\n"
    "  AI       - machine learning, deep learning, neural nets, NLP, LLM\n"
    "  Vision   - computer vision, image processing, object/defect detection\n"
    "  Sensing  - IoT, sensors, LiDAR, point cloud, SHM, photogrammetry\n"
    "  BIM      - BIM, IFC, digital documentation, knowledge graph\n"
    "  DT       - digital twin, cyber-physical systems\n"
    "  Robot    - robotics, drones, UAV, autonomous equipment, 3D printing\n"
    "  Material - concrete, composites, steel, material properties/testing\n"
    "  Structural - structural analysis, FEM, seismic, fatigue, fracture\n"
    "  Geo      - geotechnical, tunneling, soil mechanics, foundation\n"
    "  Eco      - sustainability, carbon emission, energy efficiency, green building\n"
    "  Mgmt     - construction management, safety, scheduling, cost, risk\n"
)


def make_prompt(keywords: list[str]) -> str:
    examples = json.dumps(FEW_SHOT, ensure_ascii=False, indent=2)
    kw_list  = json.dumps(keywords, ensure_ascii=False)
    return (
        f"{GROUP_DESC}\n"
        f"Required fields per item: raw, canon, group, mid_cat, parent, level (2 or 3), label_ko\n\n"
        f"Examples:\n{examples}\n\n"
        f"Now classify these keywords. Return ONLY a JSON array:\n{kw_list}"
    )


# ── Ollama 호출 ────────────────────────────────────────────────────────
def call_ollama(prompt: str, model: str, timeout: int = 120) -> str:
    try:
        import urllib.request
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.1, "top_p": 0.9},
        }).encode()
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"]
    except Exception as e:
        print(f"  [Ollama 오류] {e}", flush=True)
        return ""


# ── JSON 파싱 (모델이 마크다운을 포함할 수 있어 robust하게 처리) ────────
def extract_json_array(text: str) -> list:
    # ```json ... ``` 블록 제거
    text = re.sub(r"```(?:json)?", "", text).strip()
    # [ ... ] 배열 추출
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        # 일부 항목이 깨진 경우 개별 객체 추출 시도
        items = []
        for obj_m in re.finditer(r"\{[^{}]+\}", m.group(), re.DOTALL):
            try:
                items.append(json.loads(obj_m.group()))
            except Exception:
                pass
        return items


# ── 원시 키워드 추출 ──────────────────────────────────────────────────
def extract_raw_keywords(raw_path: str, min_count: int = 3) -> list[str]:
    """_raw.json에서 등장 빈도 min_count 이상인 원시 키워드 추출"""
    print(f"_raw.json 로드 중...", flush=True)
    with open(raw_path, encoding="utf-8") as f:
        works = json.load(f)

    counter = Counter()
    for w in works:
        texts = []
        for c in (w.get("concepts") or []):
            if c.get("score", 0) >= 0.3:
                texts.append(c.get("display_name", "").lower().strip())
        for k in (w.get("keywords") or []):
            t = (k.get("display_name") or k.get("keyword") or "").lower().strip()
            if t:
                texts.append(t)
        for t in texts:
            if t:
                counter[t] += 1

    # 최소 등장 횟수 + 길이 필터
    keywords = [
        kw for kw, cnt in counter.most_common()
        if cnt >= min_count and 3 <= len(kw) <= 80
        and not kw.isdigit()
    ]
    print(f"  → 고유 원시 키워드 {len(counter)}개 중 "
          f"등장 {min_count}회 이상: {len(keywords)}개", flush=True)
    return keywords


# ── taxonomy 로드 / 저장 ───────────────────────────────────────────────
def load_taxonomy(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # _meta 키 제외
        return {k: v for k, v in data.items() if not k.startswith("_")}
    return {}


def save_taxonomy(taxo: dict, path: str, model: str) -> None:
    output = {
        "_meta": {
            "model": model,
            "total": len(taxo),
            "updated_at": time.strftime("%Y-%m-%d %H:%M"),
        }
    }
    output.update(dict(sorted(taxo.items())))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


# ── 분류 결과 검증 ────────────────────────────────────────────────────
def validate_item(item: dict) -> bool:
    return (
        isinstance(item, dict)
        and isinstance(item.get("canon"), str) and item["canon"].strip()
        and item.get("group") in GROUPS
    )


# ── 메인 ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Ollama 기반 건설기술 taxonomy 자동 생성")
    parser.add_argument("--model",   default=DEFAULT_MODEL, help="Ollama 모델명")
    parser.add_argument("--batch",   type=int, default=BATCH_SIZE, help="배치 크기 (기본 15)")
    parser.add_argument("--min-count", type=int, default=3, help="키워드 최소 등장 횟수")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 키워드만 확인")
    args = parser.parse_args()

    if not os.path.exists(RAW_PATH):
        print(f"오류: {RAW_PATH} 없음. 먼저 python collect.py 실행 필요.")
        sys.exit(1)

    # 1. 원시 키워드 추출
    all_keywords = extract_raw_keywords(RAW_PATH, args.min_count)

    # 2. 기존 taxonomy 로드 → 미분류 키워드만 처리
    taxonomy = load_taxonomy(TAXO_PATH)
    new_keywords = [kw for kw in all_keywords if kw not in taxonomy]
    print(f"\n기존 taxonomy: {len(taxonomy)}개 / "
          f"신규 분류 대상: {len(new_keywords)}개", flush=True)

    if args.dry_run:
        print("\n[dry-run] 상위 30개 신규 키워드:")
        for kw in new_keywords[:30]:
            print(f"  {kw}")
        return

    if not new_keywords:
        print("분류할 신규 키워드 없음. taxonomy.json이 최신 상태입니다.")
        return

    # 3. 배치 처리
    total     = len(new_keywords)
    success   = 0
    fail_kws  = []

    print(f"\n모델: {args.model}  배치: {args.batch}개  총: {total}개\n", flush=True)

    for i in range(0, total, args.batch):
        batch = new_keywords[i:i + args.batch]
        pct   = min(i + args.batch, total)
        print(f"[{pct:4d}/{total}] 배치 전송 중...", end=" ", flush=True)

        prompt   = make_prompt(batch)
        response = call_ollama(prompt, args.model)
        items    = extract_json_array(response)

        # 결과 병합
        batch_ok = 0
        for item in items:
            if not validate_item(item):
                continue
            raw_key = item.get("raw", "").lower().strip()
            if not raw_key:
                # raw 키가 없으면 배치의 순서대로 매핑 시도
                continue
            taxonomy[raw_key] = {
                "canon":    item["canon"].strip(),
                "group":    item["group"],
                "mid_cat":  (item.get("mid_cat") or "").strip() or None,
                "parent":   (item.get("parent") or "").strip() or None,
                "level":    item.get("level", 3),
                "label_ko": item.get("label_ko", item["canon"]).strip(),
            }
            batch_ok += 1
            success  += 1

        # raw 없는 항목 순서 매핑 (모델이 raw 필드를 빠뜨린 경우)
        if batch_ok < len(batch) and len(items) == len(batch):
            for idx, item in enumerate(items):
                if not validate_item(item):
                    continue
                raw_key = batch[idx]
                if raw_key not in taxonomy:
                    taxonomy[raw_key] = {
                        "canon":    item["canon"].strip(),
                        "group":    item["group"],
                        "mid_cat":  (item.get("mid_cat") or "").strip() or None,
                        "parent":   (item.get("parent") or "").strip() or None,
                        "level":    item.get("level", 3),
                        "label_ko": item.get("label_ko", item["canon"]).strip(),
                    }
                    success += 1

        failed = [kw for kw in batch if kw not in taxonomy]
        fail_kws.extend(failed)
        print(f"성공 {batch_ok}/{len(batch)}", flush=True)

        # 배치마다 중간 저장
        save_taxonomy(taxonomy, TAXO_PATH, args.model)
        time.sleep(0.3)

    # 4. 요약
    print(f"\n완료: {success}/{total}개 분류됨")
    print(f"taxonomy.json 저장: {TAXO_PATH}")
    if fail_kws:
        print(f"\n미분류 키워드 {len(fail_kws)}개 (상위 20개):")
        for kw in fail_kws[:20]:
            print(f"  {kw}")


if __name__ == "__main__":
    main()
