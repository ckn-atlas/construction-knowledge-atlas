# Construction Knowledge Atlas — 작업 노트

## 프로젝트 개요
전 세계 건설기술 지식지도 웹 플랫폼.
경로: `D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas`

## 파일 구성
- `index.html` — D3.js 단일 파일 프론트엔드
- `collect.py` — OpenAlex API 수집기 + taxonomy.json 자동 로드
- `build_taxonomy.py` — Ollama(mistral:7b)로 taxonomy.json 자동 생성
- `taxonomy.json` — LLM이 생성한 키워드 분류 사전 (CANON+GROUP_OF+PARENT 자동 보완)
- `data/*.json` — graph, country, network, papers, trend, evolution, journals, meta, _raw.json

## 실행 방법
```powershell
# 로컬 서버 시작
cd "D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas"
python -m http.server 8765

# 브라우저
http://localhost:8765/index.html?v=숫자   (Ctrl+Shift+R로 캐시 우회)

# 데이터 재수집 (전체)
python collect.py

# 캐시(_raw.json)로 빠른 재가공
python collect.py rebuild

# taxonomy 자동 분류 (Ollama mistral:7b 필요)
python build_taxonomy.py --min-count 30
```

## 현재 데이터 현황
- 총 13,540편 수집 (2024-01 ~ 2026-05)
- 저널 9개 / graph.json: Level2(중분류) 14개 + Level3(세부기술) 55개 = 총 69 노드
- 국가: 중국(3187) > 미국(558) > 홍콩(312) > 한국(286)
- taxonomy.json: 220개 키워드 분류 완료 (min-count 200 기준)

## 탭 구성 (7개)
1. **기술 온톨로지** — 방사형 위계 트리, 월별 슬라이더(상위N개 필터), 위계트리/지식그래프 토글
2. **국가별 분석** — choropleth 세계지도, 클릭→기관·기술
3. **기관 네트워크** — 공동저자 force graph
4. **영향력 논문** — Impact Score 카드
5. **기술 진화** — 연도별 핵심 기술쌍
6. **수집 저널** — 저널별 논문수/인용수
7. **지식 그래프** — Force-directed + 테마 메타 그래프 (테마 버튼 클릭 시)

## 3단계 위계 구조 (현재 적용됨)
```
Level 1 (테마)    — 색상으로 구분 (AI=파랑, Material=연두 등)
Level 2 (중분류)  — 반투명 + 점선 테두리 원 (taxonomy mid_cat에서 자동 생성)
Level 3 (세부기술)— 불투명 원 (top 55개 + taxonomy 기반)
```

## collect.py 핵심 구조
- `_load_taxonomy()`: 모듈 로드 시 taxonomy.json → CANON/GROUP_OF/PARENT 자동 보완
- `build_outputs()`: 세부기술 노드(55개) + 중분류 노드(mid_agg, 자동 생성) → graph.json
- 각 노드에 `level` 필드: 2=중분류, 3=세부기술
- 링크에 `monthly_co` 필드: 월별 공동출현 누적 → 슬라이더 연동

## build_taxonomy.py 구조
- Ollama REST API (`http://localhost:11434/api/chat`) 호출
- 배치 15개씩 처리, 배치마다 taxonomy.json 중간 저장
- 3단계 분류: group(테마) + mid_cat(중분류) + parent(직계 부모) + level(2/3)
- `--dry-run`: API 호출 없이 키워드 목록만 확인
- `--min-count N`: N회 이상 등장 키워드만 처리

## index.html 핵심 함수
- `buildGraph()`: 모드 분기 → `buildForceGraph(g)` 또는 트리
- `buildForceGraph(g)`: 현재 월 기준 topIds 필터 + 월별 링크 재계산
- `applyMonth()`: 슬라이더 이동 시 (force모드: 350ms 디바운스 후 buildGraph 재호출)
- `getTopIds(month)`: 상위N개 노드 ID 집합 반환
- `coUpTo(link, monthKey)`: 링크 누적 공동출현 계산
- `papersUpTo(node, monthKey)`: 노드 누적 논문수 계산
- `buildKGraph()`: 지식그래프 탭 — kgGroupSel 기준 force/테마메타 분기
- `setGraphMode(mode)`: 온톨로지 탭 내 '위계트리'/'지식그래프' 전환

## 중분류 노드 시각 표현
- 온톨로지 트리: `fill-opacity=0.55`, 점선 stroke
- 지식그래프: `fill-opacity=0.5`, 점선 stroke

## 미완료 / 다음 작업
1. **taxonomy 재분류**: 기존 taxonomy.json 삭제 후 3단계 프롬프트로 재분류
   ```powershell
   del taxonomy.json
   python build_taxonomy.py --min-count 30   # 약 30~60분
   python collect.py rebuild
   ```
2. **자동화 런처(run.py)**: 수집→서버→브라우저 한 번에 실행
3. **월별 슬라이더 검증**: 슬라이더 이동 시 노드+링크가 함께 변하는지 확인
4. **웹 배포**: GitHub + Cloudflare Pages (GitHub Actions cron으로 daily 수집)

## 주요 제약/주의사항
- `file://`로 열면 fetch CORS 차단 → 반드시 `python -m http.server 8765` 통해 접속
- 브라우저 캐시 강함 → `?v=숫자` 또는 Ctrl+Shift+R
- OpenAlex MAILTO="" 로 두면 일반 pool 사용 (느릴 수 있음)
- `_raw.json`(127MB)은 .gitignore 대상 — 배포 시 제외
- taxonomy.json의 parent가 nodeset에 없으면 `resolve_parent()`가 상위 조상 탐색
