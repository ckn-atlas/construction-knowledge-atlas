# Construction Knowledge Atlas (프로토타입)

전 세계 건설기술 지식지도 — "논문을 읽는 사이트"가 아니라 **"논문의 기술을 보는 사이트"**.

## 실행

### 1) 데모만 보기 (샘플 데이터)
`index.html` 더블클릭. (인터넷 연결 필요 — D3.js CDN)

### 2) 실데이터로 보기 (권장)
`data/*.json`은 `fetch()`로 읽으므로 `file://`로 직접 열면 CORS로 차단됩니다. 로컬 서버 필요:
```
cd E:\PycharmProjects\ConstructionKnowledgeAtlas
python -m http.server 8765
```
브라우저에서 http://localhost:8765/index.html 접속. 헤더에 "실데이터 · N편 · 수집시각"이 뜨면 성공.

### 3) 데이터 갱신
```
python collect.py     # OpenAlex에서 최근 12개월 재수집 → data/*.json 갱신
```
폴백: 데이터 로드 실패 시 자동으로 내장 샘플로 표시됩니다.

## 구현된 화면 (기획서 → 프로토타입 매핑)

| 기획서 항목 | 프로토타입 구현 | 상태 |
|---|---|---|
| 2-(1) 기술 온톨로지 그래프 | D3 force graph. 노드 크기=논문수, 색=증가율, 선 굵기=공동출현. 노드 클릭→상세 | ✅ 작동 |
| 시간 슬라이더 (2024→2026) | 좌하단 슬라이더로 연도별 그래프 변화 | ✅ 작동 |
| 2-(2) 최근 1개월 트렌드 | 우측 사이드바 표 | ✅ |
| 2-(3) 급성장 기술 | 우측 사이드바 pill | ✅ |
| 3. 국가별 분석 | 막대 + 클릭 시 주요기관·기술 상세 | ✅ (지도는 추후) |
| 4. 기관 네트워크 | D3 공동저자 네트워크 그래프 | ✅ |
| 5. 영향력 논문 (Impact Score) | 카드 + 점수 산식 표시 | ✅ |
| 6. 논문 기술 영상화 | "1분 영상 보기" 버튼 (데모 placeholder) | ⏳ 데모만 |
| 7. 기술 진화 추적 | BIM 계보 타임라인 | ✅ |

> 데이터는 전부 기획서 수치를 옮긴 **샘플(하드코딩)**입니다. 실제 데이터 연동은 아래 참고.

## NTIS 프로젝트와의 연결 (다음 단계)

기존 `NTIS_SmartConstruction_Monitor`의 크롤링/NLP 출력이 이 그래프의 입력이 됩니다.

```
NTIS 크롤러 (논문: 제목·초록·키워드·저자·소속·국가·저널·연도·인용)
        │  NLP: 키워드 추출 + 기술 분류(온톨로지 매핑)
        ▼
graph.json  { nodes:[{id, papers, growth, group}], links:[{source,target,co}] }
country.json / orgs.json / papers.json
        ▼
index.html (fetch로 로드 — 현재는 인라인 상수 NODES/LINKS/... 를 교체)
```

핵심 변환 로직:
- **노드 논문수** = 키워드별 논문 count
- **증가율** = (최근 1개월 count − 직전 1개월 count) / 직전 count
- **링크 공동출현(co)** = 두 키워드가 같은 논문에 동시 등장한 횟수
- **Impact Score** = 정규화(인용) + 정규화(조회) + 정규화(다운로드) + 성장률 + Altmetric

## TODO (우선순위)
1. `data/*.json` 외부화 후 `fetch()`로 로드 (지금은 `<script>` 내 상수)
2. 국가별 분석을 실제 세계지도(d3-geo / TopoJSON)로
3. NTIS 크롤러 → graph.json 변환 스크립트 작성
4. 논문 기술 영상 자동 생성 (LLM 요약 → 슬라이드/TTS) — 4단계 기능
