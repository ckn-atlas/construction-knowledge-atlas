# Construction Knowledge Atlas — 작업 노트

> 새 세션에서 이 파일을 먼저 읽으면 프로젝트 전체 상태를 바로 파악할 수 있습니다.
> 최종 업데이트: 2026-06-07

## 프로젝트 개요
전 세계 건설기술 연구를 시각화하는 인터랙티브 웹 플랫폼.
- **라이브 사이트:** https://construction-knowledge-atlas.pages.dev
- **GitHub:** https://github.com/ckn-atlas/construction-knowledge-atlas
- **로컬 경로:** `D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas`
- **현황:** 261,534편 논문 · 222개 저널(JCR FA+IM 카테고리) · EN/KO 이중언어

---

## 계정 정보
| 서비스 | 계정/ID |
|---|---|
| Gmail | cknatlas48@gmail.com |
| GitHub | github.com/ckn-atlas |
| Cloudflare Pages | cknatlas48@gmail.com (push 시 자동 배포) |
| Google Analytics | G-HWFQQXWF66 |
| Google AdSense | ca-pub-5331661212294614 |
| Unsplash API | s4ZnXZruiQfi-8HQp_7DtcoKU7-qevTvhMuktNV0K-s |
| OpenAlex mailto | ckn.atlas@gmail.com (polite pool) |

⚠️ 비밀번호는 채팅/스크립트에 절대 입력 금지.

---

## 용어 (사용자 정의)
- **페이지** = 상단 네비게이션 항목 (1페이지 Latest, 2페이지 Impact, …)
- **탭** = 각 페이지 안에서 들어가 확인하는 기능 (예: 3페이지의 Hierarchy/Knowledge Graph/KG Summary)

### 7개 페이지
| # | 페이지 | 데이터 파일 | 비고 |
|---|--------|------------|------|
| 1 | Latest (최신 연구) | latest.json | 테마별 최신 고FWCI 논문 11개 + Unsplash 이미지 |
| 2 | Impact Papers (주요 논문) | papers.json | 임팩트 점수 = 인용+FWCI+최신성+OA |
| 3 | Tech Ontology (기술 온톨로지) | graph.json | 풀스크린, 탭: Hierarchy/Knowledge Graph/KG Summary |
| 4 | Country Analysis (국가별) | country.json | **2x2 그리드**: 지도/온톨로지/PaperRank/연도비교 |
| 5 | Institution Network (기관) | network.json | 탭: Force 2D/3D/Map |
| 6 | Tech Evolution (기술 진화) | evolution.json, graph.json | 탭: Emergence Tree/Rank Trend/Year View |
| 7 | Journals (저널) | journals.json + journal_meta.json | 222개, IF/Quartile/Rank/h-index |

---

## 파일 구성
### 프론트엔드
- `index.html` — 메인(탭 레이아웃, 단일 파일, D3.js v7 + 3d-force-graph)
- `index2.html` — 스크롤 레이아웃 (make_scroll.py로 index.html에서 자동 생성)
- `journal.html` — 저널별 프로필 페이지 (?issn=... 파라미터)

### 데이터 파이프라인 (Python)
- `collect.py` — OpenAlex 논문 수집 (메인). `collect.py update`=증분, `rebuild`=파생파일만 재생성
- `generate_latest.py` — 1페이지 Latest 생성 (OpenAlex + Unsplash). **배치 ISSN 쿼리 + 429 재시도 + 빈결과 보호**
- `jcr_categories.py` — JCR FA+IM 카테고리 222개 저널 목록 + JIF/JCI/Quartile/Rank 수집 (경북대 IP 필요)
- `journal_meta_gen.py` — OpenAlex sources API로 전체 저널 메타(h-index/OA/topics 등) 생성 + JCR 병합
- `jcr_auto.py` — JCR 단일저널 공식 IF/Quartile (Playwright + 내부 API, 경북대 IP)
- `jcr_parse.py` — JCR MHTML 오프라인 파서 (폴백)
- `build_taxonomy.py` — Ollama(mistral:7b)로 taxonomy.json 생성
- `make_scroll.py` — index.html → index2.html 변환
- `capture_shots.py` — 배포 사이트 7페이지 스크린샷 → docs/ (Playwright)
- `patch_*.py` — 일회성 패치 스크립트 (이력용, 재실행 불필요)

### 자동화
- `daily_update.ps1` — 일일 자동 갱신 (collect update → generate_latest → make_scroll → git push)
- Windows Task Scheduler "CKN Atlas Daily Update" — **매일 오전 10:00** 실행

### 데이터 (data/)
- `_raw.json` — OpenAlex 원본 (~2.5GB, **.gitignore**, 로컬만)
- 파생: graph/country/network/papers/journals/evolution/trend/meta.json
- `jcr_categories.json` — JCR 222개 저널 지표
- `journal_meta.json` — 저널 메타 168개 (OpenAlex + JCR 병합)
- `latest.json` — 1페이지 데이터
- `taxonomy.json` — 키워드 분류 (OpenAlex 계층 + 수동 override)

---

## 데이터 소스
| 소스 | 데이터 |
|------|--------|
| OpenAlex API | 261,534편, 인용, concept, 기관 geo |
| JCR (Clarivate) | 공식 IF/JCI/Quartile/Rank — **경북대 IP 접근** (jcr.clarivate.com) |
| Unsplash | 테마별 이미지 |

### JCR 수집 방법 (중요)
- 경북대(KNU) 캠퍼스 IP/VPN에서 jcr.clarivate.com 무료 접근 가능
- Playwright로 페이지 1회 접속 → 세션 ID(`x-1p-inc-sid`) + 쿠키 획득
- 이후 내부 API 직접 호출: `https://jcr.clarivate.com/api/jcr3/bwjournal/v1/search-result`
- 카테고리 ID: FA=Construction&Building Tech(95개), IM=Engineering Civil(184개), Multiple=둘다(44개) → 고유 222개

---

## OpenAlex Rate Limit (중요)
- 무료 일일 예산 $1 = 10,000 크레딧, **자정 UTC(=KST 오전 9시) 리셋**
- 222개 저널 대량 수집하면 소진됨 → 429 에러
- **그래서 daily_update를 오전 10시로 변경** (리셋 후)
- generate_latest.py는 빈 결과면 기존 latest.json 보존 (덮어쓰기 안 함)

---

## 최근 주요 작업 (2026-06 기준)
1. **저널 확장 18→222개** (JCR FA+IM 전체 카테고리)
2. **JCR 공식 지표 통합** (IF/Quartile/Rank/JCI) — 경북대 IP API
3. **journal_meta_gen.py** — 222개 저널 OpenAlex 메타 일괄 생성
4. **4페이지 2x2 그리드** 재구성 (지도/온톨로지/순위/연도비교)
5. **cName 무한재귀 버그 수정** (CTRY_KO 폴백) — 막대/툴팁 깨짐 원인이었음
6. **27개국 NUM 매핑 추가** — 지도 색·호버 정확도
7. **init() try-catch 격리** — 한 함수 실패가 전체 페이지 안 깨지게
8. **탭 격리** (.view overflow:hidden + 탭별 cleanup) — 페이지 간 오염 방지
9. **README + 7페이지 스크린샷** (docs/)
10. **rate limit 대응** — 실행시간 10시 변경 + 빈결과 보호
11. **X(@cknatlas48) 자동 게시 파이프라인** (2026-06-09)

---

## X 소셜 자동 게시 파이프라인

### 계정
- X: **@cknatlas48** (cknatlas48@gmail.com)
- X Developer App: `20638454251199928320cknatlas48` (Pay Per Use, Free tier — 쓰기 API 불가)

### 파이프라인 구성
```
daily_update.ps1
  └─ Step 3-1: generate_social_card.py  → 카드 이미지 + 트윗 텍스트 생성
  └─ Step 3-2: post_x_browser.py        → Playwright 브라우저로 X.com 직접 게시
```

### 핵심 파일
| 파일 | 역할 |
|------|------|
| `generate_social_card.py` | FWCI 최고 논문 선택 → Grok 이미지 + Codex 요약 → 1200×675 카드 PNG |
| `_force_card.py` | 강제 카드 재생성 (changed.flag 무시, 테스트용) |
| `post_x_browser.py` | Playwright로 X.com 브라우저 자동화 게시 |
| `data/social/card.png` | 생성된 카드 이미지 |
| `data/social/caption.txt` | 트윗 본문 텍스트 |
| `data/social/changed.flag` | 1=신규변경/0=변경없음 |
| `data/social/pw_profile/` | Playwright 전용 Chrome 프로필 (로그인 세션 유지) |

### 트윗 포맷
```
{emoji} New paper published in {theme} research!

💬 CKAtlas' Take : {AI 요약 1문장}

🔗 https://construction-knowledge-atlas.pages.dev
#{테마태그} #CivilEngineering #Research #{저널명태그} #CKAtlas
```

### AI 협업 프로토콜 (033_AICollabWorkflow 연동)
- **이미지**: Grok → 논문 주제 맞춤 이미지 생성 → `data/social/_grok_bg.jpg`
- **요약**: Codex(GPT) → abstract → 대화체 영어 1문장 → `outbox/codex/RESULT-NNN.md`
- TASK 파일: `inbox/codex/TASK-NNN.md`, `inbox/grok/TASK-NNN.md`
- 결과 파싱: `SUMMARY: ` 접두어로 시작하는 줄 추출

### X API 관련 주의사항
- X API 무료 티어는 쓰기(트윗 게시) **불가** (2023년 2월부터)
- Basic 플랜 $100/월부터 API 게시 가능
- **현재 방식: Playwright 브라우저 자동화** (API 없이 직접 게시)
- `pw_profile/` — Playwright 전용 Chrome 프로필, 최초 1회 수동 로그인 후 세션 유지
- `post_x_browser.py --force` — 강제 게시 (테스트용)

### 수동 실행
```powershell
python _force_card.py          # 카드 강제 재생성
python post_x_browser.py --force   # X 강제 게시
python post_x_browser.py --dry    # 게시 내용 미리보기만
```

---

## 알려진 이슈 / 주의점
- 미수집 7개 저널: OpenAlex에 2020년 이후 논문 0편 (Advanced Steel Construction 등) → 수집 불가, 정상
- `index.html` 수정 후 반드시 `python make_scroll.py` 실행해서 index2.html 동기화
- 레이아웃 수정 시: `.view{overflow:hidden}`라 스크롤 필요한 페이지는 `#view-XXX.active{overflow-y:auto}` 추가 필요
- height:calc(100%-Npx) 패턴 주의 — flex 레이아웃에서 깨질 수 있음

---

## 자주 쓰는 명령
```powershell
cd D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas

python collect.py update          # 증분 수집
python collect.py rebuild         # 파생파일만 재생성
python generate_latest.py         # 1페이지 갱신
python jcr_categories.py          # JCR 222개 갱신 (경북대 IP, 연1회)
python journal_meta_gen.py        # 저널 메타 갱신 (연1회)
python make_scroll.py             # index2.html 동기화
python capture_shots.py           # 스크린샷 재캡처

# 작업 시퀀스: index.html 수정 → make_scroll.py → git add → commit → push (자동배포)
```

---

## 미래 작업 후보 (보류 중)
- 커스텀 도메인 `ckatlas.dev` (도메인 구매 + Cloudflare 연결 + AdSense 재심사 필요)
- 로컬/배포 파일 폴더 분리 (data_local/ vs data/) — 사용자가 "나중에" 보류
- 저널 메타 연 1회 자동 갱신을 daily_update.ps1에 추가 (현재 월1회 jcr_categories만)
