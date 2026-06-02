import re

src  = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
dst  = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index2.html'

c = open(src, encoding='utf-8').read()

# 1. body
c = c.replace(
    "body{font-family:'Segoe UI','Malgun Gothic',system-ui,sans-serif;background:var(--bg);color:var(--txt);height:100vh;overflow:hidden}",
    "body{font-family:'Segoe UI','Malgun Gothic',system-ui,sans-serif;background:var(--bg);color:var(--txt);overflow-x:hidden}"
)

# 2. header sticky
c = c.replace(
    "header{display:flex;align-items:center;gap:16px;padding:12px 20px;border-bottom:1px solid var(--line);background:var(--panel)}",
    "header{display:flex;align-items:center;gap:16px;padding:12px 20px;border-bottom:1px solid var(--line);background:var(--panel);position:sticky;top:0;z-index:200}"
)

# 3. layout/main/aside
c = c.replace("  .layout{display:flex;height:calc(100vh - 57px)}", "  /* .layout removed */")
c = c.replace("  main{flex:1;position:relative;overflow:hidden}", "  main{display:block}")
c = c.replace(
    "  aside{width:320px;border-left:1px solid var(--line);background:var(--panel);overflow-y:auto;padding:16px}",
    "  aside{width:320px;border-left:1px solid var(--line);background:var(--panel);overflow-y:auto;padding:16px;display:none}"
)

# 4. .view scroll blocks
c = c.replace(
    "  .view{position:absolute;inset:0;display:none}\n  .view.active{display:block}",
    "  .view{display:block;position:relative;width:100%;padding-bottom:64px;border-bottom:2px solid var(--line);scroll-margin-top:58px}"
)

# 5. typography
c = c.replace(
    "  .panel-title{font-size:20px;font-weight:700;padding:20px 24px 6px;}",
    "  .panel-title{font-size:clamp(22px,3vw,32px);font-weight:800;padding:36px 32px 8px;}"
)
c = c.replace(
    "  .panel-sub{font-size:13px;color:var(--muted);padding:0 24px 16px}",
    "  .panel-sub{font-size:14px;color:var(--muted);padding:0 32px 20px;max-width:720px;line-height:1.6}"
)
c = c.replace("  .net-wrap{padding:0 24px}", "  .net-wrap{padding:0 32px}")

# 6. evo height
c = c.replace(
    "  .evo{padding:40px 60px;height:100%;overflow-y:auto}",
    "  .evo{padding:40px 60px;}"
)

# 7. graph overlay + extra CSS
extra_css = """
  /* graph overlay */
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
c = c.replace("</style>", extra_css + "</style>")

# 8. nav
old_nav = (
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
new_nav = (
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
c = c.replace(old_nav, new_nav)

# 9. layout div open
c = c.replace(
    '<div class="layout">\n  <main>',
    '<!-- GRAPH OVERLAY -->\n<div id="graphOverlay">\n  <div id="goHeader">\n    <h2>\U0001f9ec Tech Ontology</h2>\n    <span style="font-size:12px;color:var(--muted)">Hierarchy Tree · Knowledge Graph · KG Summary</span>\n    <button id="goClose" onclick="closeGraph()">✕ Close  <kbd style="font-size:10px;opacity:.6">ESC</kbd></button>\n  </div>\n  <div id="goBody">\n    <div id="goMain">'
)

# 10. </main> → close goMain, keep aside in overlay
c = c.replace(
    "    </section>\n  </main>\n\n  <aside id=\"sidebar\">",
    "    </section>\n    </div><!-- goMain -->\n    <aside id=\"sidebar\">"
)

# 11. </aside>\n</div> → close overlay, open scrollMain
c = c.replace(
    "  </aside>\n</div>",
    "  </aside>\n  </div><!-- goBody -->\n</div><!-- graphOverlay -->\n\n<main id=\"scrollMain\">",
    1
)

# 12. graph section inside overlay: make full height
c = c.replace(
    '    <!-- ONTOLOGY GRAPH -->\n    <section class="view" id="view-graph">',
    '    <!-- ONTOLOGY GRAPH (overlay) -->\n    <section id="view-graph" style="display:block;height:100%;position:relative">'
)

# 13. graph placeholder before country
old_ctry = '    <!-- COUNTRY -->\n    <section class="view" id="view-country"'
new_ctry = (
    '    <!-- GRAPH placeholder -->\n'
    '    <section class="view" id="view-graph-ph">\n'
    '      <div class="panel-title">\U0001f9ec Tech Ontology</div>\n'
    '      <p class="panel-sub">Interactive visualization of construction technology concepts — explore hierarchy trees, force-directed networks, and theme summaries across 100+ tracked technologies.</p>\n'
    '      <div class="graph-cta">\n'
    '        <button class="graph-open-btn" onclick="openGraph()">⧁ Open Interactive Graph →</button>\n'
    '        <div class="graph-cta-desc">\n'
    '          <h3>What\'s inside</h3>\n'
    '          <p>\U0001f333 Hierarchy Tree — radial concept structure<br>\n'
    '             \U0001f517 Knowledge Graph — force-directed network<br>\n'
    '             \U0001f4ca KG Summary — theme-level overview<br>\n'
    '             \U0001f4c5 Month slider — track monthly trends</p>\n'
    '        </div>\n'
    '      </div>\n'
    '    </section>\n\n'
    '    <!-- COUNTRY -->\n'
    '    <section class="view" id="view-country"'
)
c = c.replace(old_ctry, new_ctry)

# 14. country map height
c = c.replace(
    '      <div style="display:flex;gap:16px;padding:0 24px;height:calc(100vh - 160px);min-height:280px;max-height:600px">',
    '      <div class="map-zone">'
)

# 15. network heights
c = c.replace(
    '<svg id="netGraph" style="height:calc(100% - 90px)"></svg>',
    '<svg id="netGraph"></svg>'
)
c = c.replace(
    '<div id="net3dWrap" style="display:none;height:calc(100% - 90px);position:relative">',
    '<div id="net3dWrap" style="display:none;position:relative">'
)

# 16. impact list height
c = c.replace(
    '<div class="net-wrap" id="impactList" style="overflow-y:auto;height:calc(100% - 130px)"></div>',
    '<div class="net-wrap" id="impactList"></div>'
)

# 17. journals height
c = c.replace(
    '      <div class="net-wrap" style="overflow-y:auto;height:calc(100% - 92px)">',
    '      <div class="net-wrap journal-wrap">'
)

# 18. NAV JS
old_nav_js = (
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
new_nav_js = (
    '/* ===================== NAV (SCROLL) ===================== */\n'
    'function scrollSec(id){\n'
    '  const el=document.getElementById(id);\n'
    '  if(el) el.scrollIntoView({behavior:"smooth",block:"start"});\n'
    '}\n'
    'function openGraph(){\n'
    '  document.getElementById("graphOverlay").classList.add("open");\n'
    '  document.body.style.overflow="hidden";\n'
    '  buildGraph();\n'
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
    '    if(id==="view-country"&&!_mapOk){_mapOk=true;buildMap();}\n'
    '    if(id==="view-network"&&!_netOk){_netOk=true;switchNetView(_netView);}\n'
    '    if(id==="view-evo"    &&!_evoOk){_evoOk=true;_switchEvoView();}\n'
    '  });\n'
    '},{threshold:0.05,rootMargin:"-58px 0px 0px 0px"});'
)
c = c.replace(old_nav_js, new_nav_js)

# 19. INIT
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
    '  if(document.getElementById("graphOverlay").classList.contains("open")) buildGraph();\n'
    '  if(_mapOk) buildMap();\n'
    '});'
)
c = c.replace(old_init, new_init)

# 20. close scrollMain before </body>
c = c.replace('</body>', '</main><!-- scrollMain -->\n</body>')

open(dst, 'w', encoding='utf-8').write(c)
print(f"Done. {len(c)} chars -> {dst}")
