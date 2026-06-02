"""
apply_i18n.py — index.html에 한/영 i18n 적용
1. I18N 딕셔너리 + T() 헬퍼 삽입
2. 헤더에 KO|EN 토글 버튼 추가
3. 정적 HTML에 data-i18n 속성 추가
4. JS 동적 렌더링 함수에 T() 적용
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
c = open(SRC, encoding='utf-8').read()

# ─────────────────────────────────────────────────────────────────────────────
# 1. I18N 딕셔너리 + T() + setLang() JS 블록
# ─────────────────────────────────────────────────────────────────────────────
I18N_JS = r"""
/* ===================== i18n ===================== */
const I18N = {
  en: {
    /* nav */
    nav_latest:  '🔬 Latest',
    nav_impact:  'Impact Papers',
    nav_graph:   '🧬 Tech Ontology',
    nav_country: 'Country Analysis',
    nav_network: 'Institution Network',
    nav_evo:     'Tech Evolution',
    nav_journals:'Journals',
    /* data bar */
    live_data: (n,d) => `Live Data · ${n} papers · ${d} collected`,
    /* section titles */
    title_latest:  '🔬 Latest Research Highlights',
    sub_latest:    'Top-cited recent paper per theme · FWCI-ranked · Updated regularly',
    title_impact:  'Impact Paper Analysis',
    sub_impact:    'Impact Score = Citations + FWCI + Recency + Open Access',
    title_graph:   '🧬 Tech Ontology',
    sub_graph:     'Interactive visualization of construction technology concepts — explore hierarchy trees, force-directed networks, and theme summaries across 100+ tracked technologies.',
    title_country: 'Country Tech Influence',
    sub_country:   'Darker = more papers. Click map or rank to see key institutions & technologies. Click multiple countries to compare.',
    title_network: 'Institution Co-author Network',
    sub_network:   'Node=institution(color=country) · Link=co-papers. Drag & zoom to explore.',
    title_evo:     'Technology Emergence Tree',
    title_journals:'Journal Coverage',
    sub_journals:  'papers · citations (OpenAlex)',
    /* buttons */
    btn_last30:    'Last 30 Days',
    btn_last7:     'Last 7 Days',
    btn_refresh:   '↻ Refresh',
    btn_by_theme:  '📌 By Theme',
    btn_last3y:    'Last 3 Years',
    btn_last3m:    'Last 3 Months',
    btn_open_graph:'⧁ Open Interactive Graph →',
    btn_close:     '✕ Close',
    btn_alltime:   'All Time',
    btn_3y:        '3-Year',
    btn_1y:        '1-Year',
    btn_6m:        '6-Month',
    btn_force2d:   '🔗 Force 2D',
    btn_force3d:   '🔮 Force 3D',
    btn_map:       '🗺 Map',
    btn_tree:      'Hierarchy Tree',
    btn_force:     'Knowledge Graph',
    btn_summary:   'KG Summary',
    btn_emerge:    '🌿 Emergence Tree',
    btn_bump:      '📈 Rank Trend',
    btn_specific:  'Specific only',
    btn_all:       'All',
    /* graph hint */
    graph_hint:    'Radial hierarchy tree · Color=theme · Size=papers · Slider=monthly · Click node for details',
    /* sidebar */
    side_seltech:  'Selected Technology',
    side_seltech_hint: 'Click a node in the graph.',
    side_trends:   'Tech Trends (Papers)',
    side_rising:   '🚀 Fast-Growing Tech',
    side_legend:   'Legend',
    legend_fill:   'Fill = theme',
    legend_size:   'Node size ∝ papers\nLink width ∝ co-occurrence',
    /* country */
    ctry_rank:     'Paper Rank',
    ctry_compare:  'Annual Paper Comparison',
    ctry_clear:    'Clear Selection',
    ctry_ontology: 'Keyword Ontology',
    ctry_nodesize: 'Node size = papers',
    /* network */
    net_period:    'Period:',
    /* journals table */
    jt_num:   '#',
    jt_name:  'Journal',
    jt_papers:'Papers',
    jt_share: 'Paper Share',
    jt_cites: 'Citations',
    jt_if:    'IF (2yr)',
    jt_h:     'h-index',
    /* journal detail */
    jd_if:        'IF (2yr)',
    jd_h:         'h-index',
    jd_i10:       'i10-index',
    jd_cites_p:   'Cites/Paper',
    jd_total:     'Total Papers',
    jd_oa:        'OA Rate',
    jd_apc:       'APC (USD)',
    jd_founded:   'Founded',
    jd_country:   'Country',
    jd_city:      'Publisher City',
    jd_topics:    'Topics:',
    jd_chart:     'Papers published per year',
    jd_source:    'Source: OpenAlex · IF = 2yr mean citedness · JCR quartile/% requires Clarivate subscription',
    /* graph placeholder */
    gph_title:    '🧬 Tech Ontology',
    gph_sub:      'Interactive visualization of construction technology concepts — explore hierarchy trees, force-directed networks, and theme summaries across 100+ tracked technologies.',
    gph_btn:      '⧁ Open Interactive Graph →',
    gph_inside:   "What's inside",
    gph_desc:     '🌿 Hierarchy Tree — radial concept structure\n🔗 Knowledge Graph — force-directed network\n📊 KG Summary — theme-level overview\n📅 Month slider — track monthly trends',
    /* states */
    loading:      'Loading...',
    no_papers:    'No papers found.',
    no_theme:     'No theme data available.',
    no_match:     'No papers matched this theme',
    /* impact card */
    impact_top:   (n) => `— Top ${n} papers`,
    impact_score: 'Impact Score',
    impact_fwci:  'FWCI',
    impact_oa:    'OA',
    impact_full:  '→ Full Paper',
    /* evo */
    evo_node:     'Node size=papers · Color=growth(🟢up 🔴down ⬜stable) · Click to expand/collapse',
    evo_level:    'Level Filter:',
    evo_hint:     'Solid=specific · Dashed=broad · Hover for hierarchy',
    /* top slider */
    top_label:    'Top',
    top_items:    'items',
    period_label: 'Period',
  },
  ko: {
    /* nav */
    nav_latest:  '🔬 최신 연구',
    nav_impact:  '주요 논문',
    nav_graph:   '🧬 기술 온톨로지',
    nav_country: '국가별 분석',
    nav_network: '기관 네트워크',
    nav_evo:     '기술 진화',
    nav_journals:'저널',
    /* data bar */
    live_data: (n,d) => `실시간 데이터 · 논문 ${n}편 · ${d} 수집`,
    /* section titles */
    title_latest:  '🔬 최신 연구 하이라이트',
    sub_latest:    '테마별 최신 고인용 논문 · FWCI 순위 · 정기 업데이트',
    title_impact:  '주요 논문 분석',
    sub_impact:    '임팩트 점수 = 인용수 + FWCI + 최신성 + 오픈액세스',
    title_graph:   '🧬 기술 온톨로지',
    sub_graph:     '건설 기술 개념 인터랙티브 시각화 — 계층 트리, 네트워크 그래프, 테마 요약 등 100개 이상의 기술 추적',
    title_country: '국가별 기술 영향력',
    sub_country:   '색이 진할수록 논문 수가 많습니다. 지도 또는 순위를 클릭하면 주요 기관 및 기술을 확인할 수 있습니다.',
    title_network: '기관 공동저자 네트워크',
    sub_network:   '노드=기관(색상=국가) · 링크=공동논문 수. 드래그·줌으로 탐색',
    title_evo:     '기술 출현 트리',
    title_journals:'저널 현황',
    sub_journals:  '편 · 인용 수 (OpenAlex)',
    /* buttons */
    btn_last30:    '최근 30일',
    btn_last7:     '최근 7일',
    btn_refresh:   '↻ 새로고침',
    btn_by_theme:  '📌 테마별',
    btn_last3y:    '최근 3년',
    btn_last3m:    '최근 3개월',
    btn_open_graph:'⧁ 인터랙티브 그래프 열기 →',
    btn_close:     '✕ 닫기',
    btn_alltime:   '전체 기간',
    btn_3y:        '3년',
    btn_1y:        '1년',
    btn_6m:        '6개월',
    btn_force2d:   '🔗 2D 네트워크',
    btn_force3d:   '🔮 3D 네트워크',
    btn_map:       '🗺 지도',
    btn_tree:      '계층 트리',
    btn_force:     '지식 그래프',
    btn_summary:   'KG 요약',
    btn_emerge:    '🌿 출현 트리',
    btn_bump:      '📈 순위 추이',
    btn_specific:  '세부 기술만',
    btn_all:       '전체',
    /* graph hint */
    graph_hint:    '방사형 계층 트리 · 색상=테마 · 크기=논문수 · 슬라이더=월별 · 노드 클릭=상세',
    /* sidebar */
    side_seltech:  '선택된 기술',
    side_seltech_hint: '그래프에서 노드를 클릭하세요.',
    side_trends:   '기술 트렌드 (논문)',
    side_rising:   '🚀 급성장 기술',
    side_legend:   '범례',
    legend_fill:   '색상 = 테마',
    legend_size:   '노드 크기 ∝ 논문수\n링크 굵기 ∝ 공동출현',
    /* country */
    ctry_rank:     '논문 순위',
    ctry_compare:  '연도별 논문 비교',
    ctry_clear:    '선택 초기화',
    ctry_ontology: '키워드 온톨로지',
    ctry_nodesize: '노드 크기 = 논문수',
    /* network */
    net_period:    '기간:',
    /* journals table */
    jt_num:   '#',
    jt_name:  '저널',
    jt_papers:'논문수',
    jt_share: '비중',
    jt_cites: '인용수',
    jt_if:    'IF (2년)',
    jt_h:     'h-index',
    /* journal detail */
    jd_if:        'IF (2년)',
    jd_h:         'h-index',
    jd_i10:       'i10-index',
    jd_cites_p:   '논문당 인용',
    jd_total:     '총 논문수',
    jd_oa:        'OA 비율',
    jd_apc:       'APC (USD)',
    jd_founded:   '창간연도',
    jd_country:   '국가',
    jd_city:      '출판사 도시',
    jd_topics:    '주제:',
    jd_chart:     '연도별 논문 수',
    jd_source:    '출처: OpenAlex · IF = 2년 평균 피인용 · JCR 분위수는 Clarivate 구독 필요',
    /* graph placeholder */
    gph_title:    '🧬 기술 온톨로지',
    gph_sub:      '건설 기술 개념 인터랙티브 시각화 — 계층 트리, 네트워크 그래프, 테마 요약 등 100개 이상의 기술 추적',
    gph_btn:      '⧁ 인터랙티브 그래프 열기 →',
    gph_inside:   '구성 내용',
    gph_desc:     '🌿 계층 트리 — 방사형 개념 구조\n🔗 지식 그래프 — 연결망 시각화\n📊 KG 요약 — 테마별 개요\n📅 월별 슬라이더 — 월간 트렌드 추적',
    /* states */
    loading:      '불러오는 중...',
    no_papers:    '논문을 찾을 수 없습니다.',
    no_theme:     '테마 데이터가 없습니다.',
    no_match:     '이 테마에 매핑된 논문이 없습니다',
    /* impact card */
    impact_top:   (n) => `— 상위 ${n}편`,
    impact_score: '임팩트 점수',
    impact_fwci:  'FWCI',
    impact_oa:    'OA',
    impact_full:  '→ 원문 보기',
    /* evo */
    evo_node:     '노드 크기=논문수 · 색상=성장세(🟢증가 🔴감소 ⬜보합) · 클릭으로 확장/축소',
    evo_level:    '레벨 필터:',
    evo_hint:     '실선=세부 기술 · 점선=광범위 · 마우스오버=위계 확인',
    /* top slider */
    top_label:    '상위',
    top_items:    '개',
    period_label: '기간',
  }
};

let _lang = localStorage.getItem('ckn_lang') ||
            (navigator.language.startsWith('ko') ? 'ko' : 'en');

function T(key, ...args){
  const v = (I18N[_lang] && I18N[_lang][key]) || (I18N['en'] && I18N['en'][key]) || key;
  return typeof v === 'function' ? v(...args) : v;
}

function applyLang(){
  document.documentElement.lang = _lang;
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    const key = el.dataset.i18n;
    el.textContent = T(key);
  });
  // 동적 렌더링 재실행
  if(typeof fillJournals === 'function' && JOURNALS.length) fillJournals();
  if(typeof renderImpact === 'function' && PAPERS.length) renderImpact(_impactPeriod||'theme');
  if(typeof renderLatest === 'function' && LATEST) renderLatest();
  if(typeof fillSidebar === 'function') fillSidebar();
  // 토글 버튼 활성화
  document.querySelectorAll('.lang-btn').forEach(b=>{
    b.classList.toggle('active', b.dataset.lang===_lang);
  });
}

function setLang(lang){
  _lang = lang;
  localStorage.setItem('ckn_lang', lang);
  applyLang();
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. lang toggle 버튼 CSS
# ─────────────────────────────────────────────────────────────────────────────
LANG_CSS = """
  /* lang toggle */
  .lang-toggle{display:flex;gap:2px;margin-left:8px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:2px}
  .lang-btn{background:transparent;border:none;color:var(--muted);padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700}
  .lang-btn.active{background:var(--accent);color:#0e1116}
  .lang-btn:hover:not(.active){color:var(--txt)}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. CSS 추가
# ─────────────────────────────────────────────────────────────────────────────
c = c.replace("</style>", LANG_CSS + "</style>")

# ─────────────────────────────────────────────────────────────────────────────
# 4. nav에 lang toggle 버튼 추가
# ─────────────────────────────────────────────────────────────────────────────
c = c.replace(
    "</nav>\n</header>",
    """</nav>
  <div class="lang-toggle">
    <button class="lang-btn" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="lang-btn" data-lang="ko" onclick="setLang('ko')">KO</button>
  </div>
</header>"""
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. 정적 HTML에 data-i18n 속성 추가
# ─────────────────────────────────────────────────────────────────────────────

# nav 버튼
nav_pairs = [
    ('🔬 Latest',            'data-spy="view-latest"',   'nav_latest'),
    ('Impact Papers',         'data-spy="view-impact"',   'nav_impact'),
    ('🧬 Tech Ontology',      'data-spy="view-graph-ph"', 'nav_graph'),
    ('Country Analysis',      'data-spy="view-country"',  'nav_country'),
    ('Institution Network',   'data-spy="view-network"',  'nav_network'),
    ('Tech Evolution',        'data-spy="view-evo"',      'nav_evo'),
    ('Journals',              'data-spy="view-journals"', 'nav_journals'),
]
for text, attr, key in nav_pairs:
    c = c.replace(
        f'{attr} onclick',
        f'{attr} data-i18n="{key}" onclick'
    )

# section titles
static_replacements = [
    # Latest
    ('<div class="panel-title">🔬 Latest Research Highlights</div>',
     '<div class="panel-title" data-i18n="title_latest">🔬 Latest Research Highlights</div>'),
    ('<div class="panel-sub" id="latestSub">Top-cited recent paper per theme · FWCI-ranked · Updated regularly</div>',
     '<div class="panel-sub" id="latestSub" data-i18n="sub_latest">Top-cited recent paper per theme · FWCI-ranked · Updated regularly</div>'),
    # Impact
    ('<div class="panel-title">Impact Paper Analysis</div>',
     '<div class="panel-title" data-i18n="title_impact">Impact Paper Analysis</div>'),
    ('<div class="panel-sub">Impact Score = Citations + FWCI + Recency + Open Access</div>',
     '<div class="panel-sub" data-i18n="sub_impact">Impact Score = Citations + FWCI + Recency + Open Access</div>'),
    # Country
    ('<div class="panel-title">Country Tech Influence</div>',
     '<div class="panel-title" data-i18n="title_country">Country Tech Influence</div>'),
    # Network
    ('<div class="panel-title" style="padding:0;margin:0">Institution Co-author Network</div>',
     '<div class="panel-title" style="padding:0;margin:0" data-i18n="title_network">Institution Co-author Network</div>'),
    ('<div class="panel-sub" id="netSub">Node=institution(color=country) · Link=co-papers. Drag &amp; zoom to explore.</div>',
     '<div class="panel-sub" id="netSub" data-i18n="sub_network">Node=institution(color=country) · Link=co-papers. Drag &amp; zoom to explore.</div>'),
    # Journals
    ('<div class="panel-title">Journal Coverage</div>',
     '<div class="panel-title" data-i18n="title_journals">Journal Coverage</div>'),
    # Graph hint
    ('<div class="hint" id="graphHint">Radial hierarchy tree · Color=theme · Size=papers · Slider=monthly · Click node for details</div>',
     '<div class="hint" id="graphHint" data-i18n="graph_hint">Radial hierarchy tree · Color=theme · Size=papers · Slider=monthly · Click node for details</div>'),
    # Sidebar
    ('<h3>Selected Technology</h3>',
     '<h3 data-i18n="side_seltech">Selected Technology</h3>'),
    ('<div style="color:var(--muted);font-size:13px">Click a node in the graph.</div>',
     '<div style="color:var(--muted);font-size:13px" data-i18n="side_seltech_hint">Click a node in the graph.</div>'),
    ('<h3>Tech Trends (Papers)</h3>',
     '<h3 data-i18n="side_trends">Tech Trends (Papers)</h3>'),
    ('<h3>Legend</h3>',
     '<h3 data-i18n="side_legend">Legend</h3>'),
    # Graph mode buttons
    ('<button class="mode-btn active" id="btn-tree"    onclick="setGraphMode(\'tree\')">Hierarchy Tree</button>',
     '<button class="mode-btn active" id="btn-tree" data-i18n="btn_tree" onclick="setGraphMode(\'tree\')">Hierarchy Tree</button>'),
    ('<button class="mode-btn"        id="btn-force"   onclick="setGraphMode(\'force\')">Knowledge Graph</button>',
     '<button class="mode-btn" id="btn-force" data-i18n="btn_force" onclick="setGraphMode(\'force\')">Knowledge Graph</button>'),
    ('<button class="mode-btn"        id="btn-summary" onclick="setGraphMode(\'summary\')">KG Summary</button>',
     '<button class="mode-btn" id="btn-summary" data-i18n="btn_summary" onclick="setGraphMode(\'summary\')">KG Summary</button>'),
    # Network mode buttons
    ('<button class="mode-btn active" id="btn-net-force" onclick="switchNetView(\'force\')">🔗 Force 2D</button>',
     '<button class="mode-btn active" id="btn-net-force" data-i18n="btn_force2d" onclick="switchNetView(\'force\')">🔗 Force 2D</button>'),
    ('<button class="mode-btn" id="btn-net-3d"   onclick="switchNetView(\'3d\')">🔮 Force 3D</button>',
     '<button class="mode-btn" id="btn-net-3d" data-i18n="btn_force3d" onclick="switchNetView(\'3d\')">🔮 Force 3D</button>'),
    ('<button class="mode-btn" id="btn-net-map"  onclick="switchNetView(\'map\')">🗺 Map</button>',
     '<button class="mode-btn" id="btn-net-map" data-i18n="btn_map" onclick="switchNetView(\'map\')">🗺 Map</button>'),
    # Period buttons
    ('<button class="net-period-btn active" data-period="all" onclick="setNetPeriod(\'all\')">All Time</button>',
     '<button class="net-period-btn active" data-period="all" data-i18n="btn_alltime" onclick="setNetPeriod(\'all\')">All Time</button>'),
    ('<button class="net-period-btn" data-period="3y" onclick="setNetPeriod(\'3y\')">3-Year</button>',
     '<button class="net-period-btn" data-period="3y" data-i18n="btn_3y" onclick="setNetPeriod(\'3y\')">3-Year</button>'),
    ('<button class="net-period-btn" data-period="1y" onclick="setNetPeriod(\'1y\')">1-Year</button>',
     '<button class="net-period-btn" data-period="1y" data-i18n="btn_1y" onclick="setNetPeriod(\'1y\')">1-Year</button>'),
    ('<button class="net-period-btn" data-period="6m" onclick="setNetPeriod(\'6m\')">6-Month</button>',
     '<button class="net-period-btn" data-period="6m" data-i18n="btn_6m" onclick="setNetPeriod(\'6m\')">6-Month</button>'),
    # Latest range buttons
    ('<button class="latest-range-btn active" data-range="month" onclick="setLatestRange(\'month\')">Last 30 Days</button>',
     '<button class="latest-range-btn active" data-range="month" data-i18n="btn_last30" onclick="setLatestRange(\'month\')">Last 30 Days</button>'),
    ('<button class="latest-range-btn" data-range="week" onclick="setLatestRange(\'week\')">Last 7 Days</button>',
     '<button class="latest-range-btn" data-range="week" data-i18n="btn_last7" onclick="setLatestRange(\'week\')">Last 7 Days</button>'),
    # Impact filter buttons
    ('<button class="impact-filter active" data-period="theme">📌 By Theme</button>',
     '<button class="impact-filter active" data-period="theme" data-i18n="btn_by_theme">📌 By Theme</button>'),
    ('<button class="impact-filter" data-period="3y">Last 3 Years</button>',
     '<button class="impact-filter" data-period="3y" data-i18n="btn_last3y">Last 3 Years</button>'),
    ('<button class="impact-filter" data-period="3m">Last 3 Months</button>',
     '<button class="impact-filter" data-period="3m" data-i18n="btn_last3m">Last 3 Months</button>'),
    # Evo buttons
    ('<button class="evo-view-btn active" data-eview="tree">🌿 Emergence Tree</button>',
     '<button class="evo-view-btn active" data-eview="tree" data-i18n="btn_emerge">🌿 Emergence Tree</button>'),
    ('<button class="evo-view-btn" data-eview="bump">📈 Rank Trend</button>',
     '<button class="evo-view-btn" data-eview="bump" data-i18n="btn_bump">📈 Rank Trend</button>'),
    ('<button class="evo-filter active" data-level="specific">Specific only</button>',
     '<button class="evo-filter active" data-level="specific" data-i18n="btn_specific">Specific only</button>'),
    ('<button class="evo-filter" data-level="all">All</button>',
     '<button class="evo-filter" data-level="all" data-i18n="btn_all">All</button>'),
    # Journal table headers
    ('<thead><tr><th>#</th><th>Journal</th><th style="text-align:right">Papers</th><th>Paper Share</th><th style="text-align:right">Citations</th><th style="text-align:right">IF (2yr)</th><th style="text-align:right">h-index</th><th></th></tr></thead>',
     '<thead><tr><th data-i18n="jt_num">#</th><th data-i18n="jt_name">Journal</th><th style="text-align:right" data-i18n="jt_papers">Papers</th><th data-i18n="jt_share">Paper Share</th><th style="text-align:right" data-i18n="jt_cites">Citations</th><th style="text-align:right" data-i18n="jt_if">IF (2yr)</th><th style="text-align:right" data-i18n="jt_h">h-index</th><th></th></tr></thead>'),
    # Evo hint
    ('<div id="evoTreeCtrl" style="color:var(--muted);font-size:12px;margin-bottom:12px">\n          Node size=papers · Color=growth(🟢up 🔴down ⬜stable) · Click to expand/collapse\n        </div>',
     '<div id="evoTreeCtrl" data-i18n="evo_node" style="color:var(--muted);font-size:12px;margin-bottom:12px">\n          Node size=papers · Color=growth(🟢up 🔴down ⬜stable) · Click to expand/collapse\n        </div>'),
    # Country section sub
    ('<div class="panel-sub">색이 진할수록 Paper Count가 많습니다. Click map or rank to see key institutions &amp; technologies. <b>여러 나라를 클릭</b>하면 연도별 비교 차트가 표시됩니다.</div>',
     '<div class="panel-sub" data-i18n="sub_country">색이 진할수록 Paper Count가 많습니다. Click map or rank to see key institutions &amp; technologies. 여러 나라를 클릭하면 연도별 비교 차트가 표시됩니다.</div>'),
    # Refresh button
    ('<button id="latestRefreshBtn" onclick="refreshLatest()" style="margin-left:auto;background:var(--panel2);border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:4px 12px;font-size:11px;cursor:pointer">↻ Refresh</button>',
     '<button id="latestRefreshBtn" data-i18n="btn_refresh" onclick="refreshLatest()" style="margin-left:auto;background:var(--panel2);border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:4px 12px;font-size:11px;cursor:pointer">↻ Refresh</button>'),
]

for old, new in static_replacements:
    if old in c:
        c = c.replace(old, new)
    else:
        print(f"WARN not found: {old[:60]}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. JS 동적 렌더링에 T() 적용
# ─────────────────────────────────────────────────────────────────────────────

# loadLatest: Loading/error 메시지
c = c.replace(
    "grid.innerHTML = '<div style=\"padding:40px;text-align:center;color:var(--muted)\">Loading...</div>';",
    "grid.innerHTML = `<div style=\"padding:40px;text-align:center;color:var(--muted)\">${T('loading')}</div>`;"
)
c = c.replace(
    "grid.innerHTML = '<div style=\"padding:40px;text-align:center;color:var(--muted)\">Failed to load: ' + e.message + '</div>';",
    "grid.innerHTML = `<div style=\"padding:40px;text-align:center;color:var(--muted)\">Failed to load: ${e.message}</div>`;"
)

# renderLatest: no papers
c = c.replace(
    "grid.innerHTML='<div style=\"padding:40px;text-align:center;color:var(--muted)\">No papers found.</div>'; return; }",
    "grid.innerHTML=`<div style=\"padding:40px;text-align:center;color:var(--muted)\">${T('no_papers')}</div>`; return; }"
)

# renderLatest: Full Paper
c = c.replace(
    "'→ Full Paper'",
    "T('impact_full')"
)

# renderImpactByTheme: no data
c = c.replace(
    '"<div style=\'padding:40px;color:var(--muted);text-align:center\'>No theme data available.</div>"',
    "`<div style='padding:40px;color:var(--muted);text-align:center'>${T('no_theme')}</div>`"
)

# renderImpactByTheme: no match
c = c.replace(
    "'<div style=\"font-size:12px;color:var(--muted);text-align:center;padding:20px 0\">No papers matched this theme</div>'",
    "`<div style=\"font-size:12px;color:var(--muted);text-align:center;padding:20px 0\">${T('no_match')}</div>`"
)

# renderImpactByTheme: top N label
c = c.replace(
    '`— Top ${papers.length} papers`',
    "T('impact_top', papers.length)"
)

# impact full paper button
c = c.replace(
    "'→ Full Paper'",
    "T('impact_full')"
)

# fillJournals journal detail labels
jd_pairs = [
    ("'IF (2yr)'",       "T('jd_if')"),
    ("'h-index'",        "T('jd_h')"),
    ("'i10-index'",      "T('jd_i10')"),
    ("'Cites/Paper'",    "T('jd_cites_p')"),
    ("'Total Papers'",   "T('jd_total')"),
    ("'OA Rate'",        "T('jd_oa')"),
    ("'APC (USD)'",      "T('jd_apc')"),
    ("'Founded'",        "T('jd_founded')"),
    ("'Country'",        "T('jd_country')"),
    ("'Publisher City'", "T('jd_city')"),
]
for old, new in jd_pairs:
    c = c.replace(f'<div class="lbl">{old[1:-1]}</div>', f'<div class="lbl">${{{new}}}</div>')

# journal detail: Topics label, chart label, source
c = c.replace(
    "'<b style=\"color:var(--txt)\">Topics:</b>'",
    "`<b style=\"color:var(--txt)\">${T('jd_topics')}</b>`"
)
c = c.replace(
    "'<div style=\"font-size:10px;color:var(--muted);margin-bottom:4px\">Papers published per year</div>'",
    "`<div style=\"font-size:10px;color:var(--muted);margin-bottom:4px\">${T('jd_chart')}</div>`"
)
c = c.replace(
    "'Source: OpenAlex · IF = 2yr mean citedness · JCR quartile/% requires Clarivate subscription'",
    "T('jd_source')"
)

# meta.json sub text
c = c.replace(
    "if(subEl) subEl.textContent = `Live Data · ${meta.total_papers.toLocaleString()} papers · ${meta.generated_at} collected`;",
    "if(subEl) subEl.textContent = T('live_data', meta.total_papers.toLocaleString(), meta.generated_at);"
)

# countryBars h3
c = c.replace(
    "<h3>Paper Rank</h3>",
    "<h3 data-i18n=\"ctry_rank\">Paper Rank</h3>"
)

# country chart title
c = c.replace(
    "'Annual Paper Comparison'",
    "T('ctry_compare')"
)
c = c.replace(
    "'Clear Selection'",
    "T('ctry_clear')"
)

# legend
c = c.replace(
    '<div style="margin-bottom:4px"><b>Fill = theme</b></div>',
    '<div style="margin-bottom:4px"><b data-i18n="legend_fill">Fill = theme</b></div>'
)

# ─────────────────────────────────────────────────────────────────────────────
# 7. I18N_JS를 NAV JS 앞에 삽입
# ─────────────────────────────────────────────────────────────────────────────
c = c.replace(
    '/* ===================== NAV',
    I18N_JS + '\n/* ===================== NAV'
)

# ─────────────────────────────────────────────────────────────────────────────
# 8. INIT에 applyLang() 호출 추가
# ─────────────────────────────────────────────────────────────────────────────
c = c.replace(
    "  loadLatest();\n  document.querySelectorAll(\"#scrollMain .view[id]\").forEach(el=>{",
    "  loadLatest();\n  applyLang();\n  document.querySelectorAll(\"#scrollMain .view[id]\").forEach(el=>{"
)
# fallback for index.html (tab layout has different init)
c = c.replace(
    "  loadLatest(); // Latest 탭 초기 로드\n})()",
    "  loadLatest();\n  applyLang();\n})()"
)

open(SRC, 'w', encoding='utf-8').write(c)
print(f"Done. {len(c):,} chars")
