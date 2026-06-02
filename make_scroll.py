"""
make_scroll.py  —  index.html → index2.html (scroll layout)
전략:
  1. index.html을 읽어서 섹션별로 분리
  2. view-graph → graphOverlay 안으로
  3. 나머지 섹션 → scrollMain 안으로
  4. CSS/JS 패치
"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
DST = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index2.html'

c = open(SRC, encoding='utf-8').read()

# ──────────────────────────────────────────────────────────────
# 헬퍼: 섹션 추출 (section 태그 기준, 중첩 없으므로 단순 split 가능)
# ──────────────────────────────────────────────────────────────
def extract_sections(html):
    """<section ...> ... </section> 블록을 id 기준으로 추출"""
    sections = {}
    for m in re.finditer(r'(<section[^>]*id="([^"]+)"[^>]*>)(.*?)(</section>)',
                         html, re.DOTALL):
        full  = m.group(0)
        sid   = m.group(2)
        sections[sid] = full
    return sections

# ──────────────────────────────────────────────────────────────
# 1. 원본에서 <header> 앞부분(head) 추출
# ──────────────────────────────────────────────────────────────
head_end = c.index('</head>') + len('</head>')
head_part = c[:head_end]

# ──────────────────────────────────────────────────────────────
# 2. <header>...</header> 추출
# ──────────────────────────────────────────────────────────────
header_m = re.search(r'<header>.*?</header>', c, re.DOTALL)
header_html = header_m.group(0)

# ──────────────────────────────────────────────────────────────
# 3. <aside>...</aside> 추출
# ──────────────────────────────────────────────────────────────
aside_m = re.search(r'<aside id="sidebar">.*?</aside>', c, re.DOTALL)
aside_html = aside_m.group(0)

# ──────────────────────────────────────────────────────────────
# 4. 각 섹션 추출
# ──────────────────────────────────────────────────────────────
secs = extract_sections(c)
print("Sections found:", list(secs.keys()))

# ──────────────────────────────────────────────────────────────
# 5. <script> 블록 추출 (</aside> 이후 ~ </body>)
# ──────────────────────────────────────────────────────────────
script_start = c.index('</aside>') + len('</aside>')
# layout div closing tag
for closer in ['\n</div>', '\n\n</div>']:
    if c[script_start:script_start+10].startswith(closer.strip()):
        script_start += len(closer)
        break
script_end = c.rindex('</body>')
script_part = c[script_start:script_end].strip()

# ──────────────────────────────────────────────────────────────
# 6. adLeft / adBanner HTML (body 안, header 전 또는 후)
# ──────────────────────────────────────────────────────────────
adleft_m  = re.search(r'<!-- 좌측 세로 배너.*?</div>(?=\s*\n)', c, re.DOTALL)
adbanner_m= re.search(r'<div id="adBanner".*?</div>\s*</div>', c, re.DOTALL)

# ──────────────────────────────────────────────────────────────
# 7. CSS 패치
# ──────────────────────────────────────────────────────────────
def patch_css(h):
    # body: scroll 허용
    h = h.replace(
        "body{font-family:'Segoe UI','Malgun Gothic',system-ui,sans-serif;background:var(--bg);color:var(--txt);height:100vh;overflow:hidden}",
        "body{font-family:'Segoe UI','Malgun Gothic',system-ui,sans-serif;background:var(--bg);color:var(--txt);overflow-x:hidden}"
    )
    # header: sticky
    h = h.replace(
        "header{display:flex;align-items:center;gap:16px;padding:12px 20px;border-bottom:1px solid var(--line);background:var(--panel)}",
        "header{display:flex;align-items:center;gap:16px;padding:12px 20px;border-bottom:1px solid var(--line);background:var(--panel);position:sticky;top:0;z-index:200}"
    )
    # layout/main/aside
    h = h.replace("  .layout{display:flex;height:calc(100vh - 57px)}", "  /* .layout removed */")
    h = h.replace("  main{flex:1;position:relative;overflow:hidden}", "  main{display:block}")
    h = h.replace(
        "  aside{width:320px;border-left:1px solid var(--line);background:var(--panel);overflow-y:auto;padding:16px}",
        "  aside{width:320px;border-left:1px solid var(--line);background:var(--panel);overflow-y:auto;padding:16px;display:none}"
    )
    # .view → scroll blocks
    h = h.replace(
        "  .view{position:absolute;inset:0;display:none}\n  .view.active{display:block}",
        "  .view{display:block;position:relative;width:100%;padding-bottom:64px;border-bottom:2px solid var(--line);scroll-margin-top:58px}"
    )
    # typography
    h = h.replace(
        "  .panel-title{font-size:20px;font-weight:700;padding:20px 24px 6px;}",
        "  .panel-title{font-size:clamp(22px,3vw,32px);font-weight:800;padding:36px 32px 8px;}"
    )
    h = h.replace(
        "  .panel-sub{font-size:13px;color:var(--muted);padding:0 24px 16px}",
        "  .panel-sub{font-size:14px;color:var(--muted);padding:0 32px 20px;max-width:720px;line-height:1.6}"
    )
    h = h.replace("  .net-wrap{padding:0 24px}", "  .net-wrap{padding:0 32px}")
    h = h.replace(
        "  .evo{padding:40px 60px;height:100%;overflow-y:auto}",
        "  .evo{padding:40px 60px;}"
    )
    # extra CSS
    extra = """
  /* ── Graph Full-Screen Overlay ── */
  #graphOverlay{display:none;position:fixed;inset:0;z-index:300;background:var(--bg);flex-direction:column}
  #graphOverlay.open{display:flex}
  #goHeader{display:flex;align-items:center;gap:12px;padding:10px 20px;border-bottom:1px solid var(--line);background:var(--panel);flex-shrink:0}
  #goHeader h2{font-size:16px;font-weight:700}
  #goClose{margin-left:auto;background:transparent;border:1px solid var(--line);color:var(--muted);padding:5px 14px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600}
  #goClose:hover{color:var(--txt);border-color:var(--txt)}
  #goBody{display:flex;flex:1;overflow:hidden}
  #goMain{flex:1;position:relative;overflow:hidden}
  #graphOverlay aside{display:block}
  /* graph placeholder */
  .graph-cta{display:flex;align-items:center;gap:32px;flex-wrap:wrap;padding:36px 32px}
  .graph-open-btn{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:#0e1116;border:none;border-radius:10px;padding:16px 32px;font-size:16px;font-weight:700;cursor:pointer;transition:opacity .15s;white-space:nowrap}
  .graph-open-btn:hover{opacity:.85}
  .graph-cta-desc{flex:1;min-width:200px}
  .graph-cta-desc h3{font-size:17px;font-weight:700;margin-bottom:8px}
  .graph-cta-desc p{font-size:13px;color:var(--muted);line-height:1.8}
  /* map/network heights */
  .map-zone{display:flex;gap:16px;padding:0 32px;height:480px}
  #netGraph{height:480px !important}
  #net3dWrap{height:480px !important}
  /* scroll overrides */
  #impactList{height:auto !important;overflow:visible !important}
  .journal-wrap{height:auto !important;overflow:visible !important}
  /* scroll-spy */
  nav button.spy{color:var(--txt);background:var(--panel2);border-color:var(--line)}
  /* mobile */
  @media(max-width:768px){
    .panel-title{padding:24px 16px 6px !important}
    .panel-sub{padding:0 16px 14px !important}
    .net-wrap{padding:0 16px !important}
    .map-zone{height:300px;padding:0 12px}
    #netGraph{height:300px !important}
    #net3dWrap{height:300px !important}
    .graph-cta{padding:20px 16px;gap:16px}
    .evo{padding:24px 16px !important}
  }
"""
    h = h.replace("</style>", extra + "</style>")
    return h

# ──────────────────────────────────────────────────────────────
# 8. Header nav 패치
# ──────────────────────────────────────────────────────────────
def patch_nav(h):
    old = (
        "  <nav>\n"
        "    <button class=\"active\" data-view=\"latest\">\U0001f52c Latest</button>\n"
        "    <button data-view=\"impact\">Impact Papers</button>\n"
        "    <button data-view=\"graph\">Tech Ontology</button>\n"
        "    <button data-view=\"country\">Country Analysis</button>\n"
        "    <button data-view=\"network\">Institution Network</button>\n"
        "    <button data-view=\"evo\">Tech Evolution</button>\n"
        "    <button data-view=\"journals\">Journals</button>\n"
        "  </nav>"
    )
    new = (
        "  <nav id=\"mainNav\">\n"
        "    <button data-spy=\"view-latest\"   onclick=\"scrollSec('view-latest')\">\U0001f52c Latest</button>\n"
        "    <button data-spy=\"view-impact\"   onclick=\"scrollSec('view-impact')\">Impact Papers</button>\n"
        "    <button data-spy=\"view-graph-ph\" onclick=\"openGraph()\">\U0001f9ec Tech Ontology</button>\n"
        "    <button data-spy=\"view-country\"  onclick=\"scrollSec('view-country')\">Country Analysis</button>\n"
        "    <button data-spy=\"view-network\"  onclick=\"scrollSec('view-network')\">Institution Network</button>\n"
        "    <button data-spy=\"view-evo\"      onclick=\"scrollSec('view-evo')\">Tech Evolution</button>\n"
        "    <button data-spy=\"view-journals\" onclick=\"scrollSec('view-journals')\">Journals</button>\n"
        "  </nav>"
    )
    return h.replace(old, new)

# ──────────────────────────────────────────────────────────────
# 9. 섹션별 HTML 패치
# ──────────────────────────────────────────────────────────────
def patch_latest(s):
    # overflow-y:auto 는 scroll layout 에서 높이 없으면 내용 숨김
    # 원본에 class="view active" 포함
    s = s.replace(
        '<section class="view active" id="view-latest" style="overflow-y:auto">',
        '<section class="view" id="view-latest">'
    )
    s = s.replace(
        '<section class="view" id="view-latest" style="overflow-y:auto">',
        '<section class="view" id="view-latest">'
    )
    return s

def patch_country(s):
    s = s.replace(
        '<section class="view" id="view-country" style="overflow-y:auto">',
        '<section class="view" id="view-country">'
    )
    return s.replace(
        '      <div style="display:flex;gap:16px;padding:0 24px;height:calc(100vh - 160px);min-height:280px;max-height:600px">',
        '      <div class="map-zone">'
    )

def patch_network(s):
    s = s.replace(
        '<svg id="netGraph" style="height:calc(100% - 90px)"></svg>',
        '<svg id="netGraph"></svg>'
    )
    s = s.replace(
        '<div id="net3dWrap" style="display:none;height:calc(100% - 90px);position:relative">',
        '<div id="net3dWrap" style="display:none;position:relative">'
    )
    return s

def patch_impact(s):
    return s.replace(
        '<div class="net-wrap" id="impactList" style="overflow-y:auto;height:calc(100% - 130px)"></div>',
        '<div class="net-wrap" id="impactList"></div>'
    )

def patch_journals(s):
    return s.replace(
        '      <div class="net-wrap" style="overflow-y:auto;height:calc(100% - 92px)">',
        '      <div class="net-wrap journal-wrap">'
    )

# ──────────────────────────────────────────────────────────────
# 10. JS 패치
# ──────────────────────────────────────────────────────────────
def patch_js(s):
    # NAV 교체
    old_nav = (
        '/* ===================== NAV ===================== */\n'
        'document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{\n'
        '  document.querySelectorAll("nav button").forEach(x=>x.classList.remove("active"));\n'
        '  b.classList.add("active");\n'
        '  const v=b.dataset.view;\n'
        '  document.querySelectorAll(".view").forEach(x=>x.classList.remove("active"));\n'
        '  document.getElementById("view-"+v).classList.add("active");\n'
        '  document.getElementById("sidebar").style.display = v==="graph"?"block":"none";\n'
        '  if(v==="graph") buildGraph();\n'
        '  if(v==="network") switchNetView(_netView);\n'
        '  if(v==="country") buildMap();\n'
        '  if(v==="evo") _switchEvoView();\n'
        '  if(v==="latest") loadLatest();\n'
        '});'
    )
    new_nav = (
        '/* ===================== NAV (SCROLL) ===================== */\n'
        'function scrollSec(id){\n'
        '  const el=document.getElementById(id);\n'
        '  if(el) el.scrollIntoView({behavior:"smooth",block:"start"});\n'
        '}\n'
        'function openGraph(){\n'
        '  document.getElementById("graphOverlay").classList.add("open");\n'
        '  document.body.style.overflow="hidden";\n'
        '  setTimeout(()=>buildGraph(),80);\n'
        '}\n'
        'function closeGraph(){\n'
        '  document.getElementById("graphOverlay").classList.remove("open");\n'
        '  document.body.style.overflow="";\n'
        '}\n'
        'document.addEventListener("keydown",e=>{if(e.key==="Escape")closeGraph();});\n'
        '\n'
        '// scroll-spy\n'
        'const _spy=new IntersectionObserver(entries=>{\n'
        '  entries.forEach(e=>{\n'
        '    if(e.isIntersecting){\n'
        '      const id=e.target.id;\n'
        '      document.querySelectorAll("#mainNav button").forEach(b=>{\n'
        '        b.classList.toggle("spy",b.dataset.spy===id);\n'
        '      });\n'
        '    }\n'
        '  });\n'
        '},{threshold:0.15,rootMargin:"-58px 0px 0px 0px"});\n'
        '\n'
        '// lazy-init\n'
        'let _mapOk=false,_netOk=false,_evoOk=false;\n'
        'const _lazy=new IntersectionObserver(entries=>{\n'
        '  entries.forEach(e=>{\n'
        '    if(!e.isIntersecting)return;\n'
        '    const id=e.target.id;\n'
        '    if(id==="view-country"&&!_mapOk){_mapOk=true;setTimeout(()=>buildMap(),80);}\n'
        '    if(id==="view-network"&&!_netOk){_netOk=true;setTimeout(()=>switchNetView(_netView),80);}\n'
        '    if(id==="view-evo"    &&!_evoOk){_evoOk=true;setTimeout(()=>_switchEvoView(),80);}\n'
        '  });\n'
        '},{threshold:0.05,rootMargin:"-58px 0px 0px 0px"});'
    )
    s = s.replace(old_nav, new_nav)

    # INIT 교체
    old_init = (
        '/* ===================== INIT ===================== */\n'
        '(async function init(){\n'
        '  await loadData();\n'
        '  initMonthSlider();\n'
        '  fillSidebar(); fillCountry(); fillImpact(); fillEvo(); fillJournals();\n'
        '  buildGroupFilter();\n'
        '  fillThemeLegend();\n'
        '  buildGraph();\n'
        '  updateRankPanel();\n'
        '  precomputeTreeCache();\n'
        '  loadLatest(); // Latest 탭 초기 로드\n'
        '})();\n'
        'window.addEventListener("resize",()=>{\n'
        '  _treeCache.clear(); // 크기 변경 시 cluster 재계산 필요\n'
        '  if(document.querySelector("#view-graph").classList.contains("active")) buildGraph();\n'
        '  if(document.querySelector("#view-country").classList.contains("active")) buildMap();\n'
        '});'
    )
    new_init = (
        '/* ===================== INIT ===================== */\n'
        '(async function init(){\n'
        '  await loadData();\n'
        '  initMonthSlider();\n'
        '  fillSidebar(); fillCountry(); fillImpact(); fillEvo(); fillJournals();\n'
        '  buildGroupFilter();\n'
        '  fillThemeLegend();\n'
        '  updateRankPanel();\n'
        '  precomputeTreeCache();\n'
        '  loadLatest();\n'
        '  document.querySelectorAll("#scrollMain .view[id]").forEach(el=>{\n'
        '    _spy.observe(el);\n'
        '    _lazy.observe(el);\n'
        '  });\n'
        '})();\n'
        'window.addEventListener("resize",()=>{\n'
        '  _treeCache.clear();\n'
        '  if(document.getElementById("graphOverlay").classList.contains("open")) setTimeout(()=>buildGraph(),80);\n'
        '  if(_mapOk) setTimeout(()=>buildMap(),80);\n'
        '});'
    )
    s = s.replace(old_init, new_init)
    return s

# ──────────────────────────────────────────────────────────────
# 11. 조립
# ──────────────────────────────────────────────────────────────
head_part  = patch_css(head_part)
header_html= patch_nav(header_html)

graph_sec = secs.get('view-graph', '')
# graph section: 오버레이 전용 (full height, .view 클래스 불필요)
graph_sec = graph_sec.replace(
    '<section class="view" id="view-graph">',
    '<section id="view-graph" style="display:block;height:100%;position:relative">'
)

# graph placeholder
graph_ph = """    <section class="view" id="view-graph-ph">
      <div class="panel-title">\U0001f9ec Tech Ontology</div>
      <p class="panel-sub">Interactive visualization of construction technology concepts — explore hierarchy trees, force-directed networks, and theme summaries across 100+ tracked technologies.</p>
      <div class="graph-cta">
        <button class="graph-open-btn" onclick="openGraph()">⧁ Open Interactive Graph →</button>
        <div class="graph-cta-desc">
          <h3>What's inside</h3>
          <p>\U0001f333 Hierarchy Tree — radial concept structure<br>
             \U0001f517 Knowledge Graph — force-directed network<br>
             \U0001f4ca KG Summary — theme-level overview<br>
             \U0001f4c5 Month slider — track monthly trends</p>
        </div>
      </div>
    </section>"""

scroll_sections_html = (
    patch_latest(secs.get('view-latest',''))     + "\n\n" +
    patch_impact(secs.get('view-impact',''))     + "\n\n" +
    graph_ph                                     + "\n\n" +
    patch_country(secs.get('view-country',''))   + "\n\n" +
    patch_network(secs.get('view-network',''))   + "\n\n" +
    patch_journals(secs.get('view-journals','')) + "\n\n" +
    secs.get('view-evo','')
)

patched_script = patch_js(script_part)

# adLeft / adBanner
adleft_html  = adleft_m.group(0)  if adleft_m  else ''
adbanner_html= adbanner_m.group(0) if adbanner_m else ''

result = f"""{head_part}
<body>
{header_html}

<!-- GRAPH OVERLAY -->
<div id="graphOverlay">
  <div id="goHeader">
    <h2>\U0001f9ec Tech Ontology</h2>
    <span style="font-size:12px;color:var(--muted)">Hierarchy Tree · Knowledge Graph · KG Summary</span>
    <button id="goClose" onclick="closeGraph()">✕ Close  <kbd style="font-size:10px;opacity:.6">ESC</kbd></button>
  </div>
  <div id="goBody">
    <div id="goMain">
{graph_sec}
    </div>
{aside_html}
  </div>
</div>

<!-- SCROLL MAIN -->
<main id="scrollMain">
{scroll_sections_html}
</main>

{patched_script}

</body>
</html>"""

open(DST, 'w', encoding='utf-8').write(result)
print(f"Done. {len(result):,} chars -> {DST}")
