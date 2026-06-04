"""
Country Analysis → 2x2 grid layout (안전 버전)
- 4분할: 지도 / 온톨로지 / Paper Rank / Annual Comparison
- 그리드 셀은 항상 보임, 함수 display 토글은 dummy로 무해화
- fillCountry: 전체 국가 세로 막대
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
c = open(SRC, encoding='utf-8').read()

# ─────────────────────────────────────────────────────────────
# 1. CSS: 그리드 + 셀 스타일 추가
# ─────────────────────────────────────────────────────────────
CSS = """
  /* ── Country 2x2 grid ── */
  #view-country.active{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;height:100%;overflow:hidden}
  .ctry-cell{position:relative;overflow:hidden;display:flex;flex-direction:column}
  .ctry-cell-hd{display:flex;align-items:center;gap:8px;padding:6px 12px;font-size:12px;font-weight:700;color:var(--txt);flex-shrink:0;border-bottom:1px solid var(--line);background:rgba(255,255,255,.02)}
  .ctry-cell-hd .sub{font-size:10px;color:var(--muted);font-weight:400}
  .ctry-cell-body{flex:1;position:relative;min-height:0}
  .ctry-ph{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px;pointer-events:none;text-align:center;padding:0 20px}
  .ctry-vbar{display:flex;flex-direction:column;align-items:center;gap:2px;cursor:pointer;flex-shrink:0;width:30px;transition:opacity .15s}
  .ctry-vbar .vb{width:18px;border-radius:2px 2px 0 0;transition:height .3s,opacity .15s}
"""
c = c.replace('</style>', CSS + '</style>')

# ─────────────────────────────────────────────────────────────
# 2. HTML: view-country 섹션 교체
# ─────────────────────────────────────────────────────────────
OLD_SECTION = re.search(r'    <!-- COUNTRY -->\n    <section class="view" id="view-country">.*?\n    </section>', c, re.DOTALL).group()

NEW_SECTION = """    <!-- COUNTRY (2x2 grid) -->
    <section class="view" id="view-country">

      <!-- TL: Map -->
      <div class="ctry-cell" style="border-right:1px solid var(--line);border-bottom:1px solid var(--line)">
        <div class="ctry-cell-hd"><span data-i18n="title_country">Country Tech Influence</span></div>
        <div class="ctry-cell-body">
          <div class="map-wrap" style="position:absolute;inset:0">
            <svg id="worldMap"></svg>
            <div class="maptip" id="mapTip"></div>
            <div class="map-legend" style="position:absolute;left:8px;bottom:8px">Paper Count<div class="grad"></div><span id="legLo">0</span> ~ <span id="legHi">max</span></div>
          </div>
        </div>
      </div>

      <!-- TR: Keyword Ontology -->
      <div class="ctry-cell" style="border-bottom:1px solid var(--line);background:var(--panel2)">
        <div class="ctry-cell-hd"><span id="ctryOntologyTitle">Keyword Ontology</span><span class="sub">Node size = papers</span></div>
        <div class="ctry-cell-body">
          <div id="ctryOntologyGraph" style="position:absolute;inset:0"></div>
          <div class="ctry-ph" id="ctryOntoPh">Click a country on the map to see its keyword ontology</div>
        </div>
      </div>

      <!-- BL: Paper Rank -->
      <div class="ctry-cell" style="border-right:1px solid var(--line)">
        <div class="ctry-cell-hd">
          <span data-i18n="ctry_rank">Paper Rank</span>
          <button id="ctryChartClear" onclick="clearCtrySelection()" style="margin-left:auto;display:none;background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:5px;padding:2px 8px;font-size:10px;cursor:pointer">Clear Selection</button>
        </div>
        <div class="ctry-cell-body" style="display:flex">
          <div style="flex:1;overflow-x:auto;overflow-y:hidden;padding:6px 8px 0">
            <div id="countryBars" style="display:flex;gap:3px;align-items:flex-end;height:100%;min-width:max-content;padding-bottom:18px"></div>
          </div>
          <div class="country-detail card" id="countryDetail" style="display:none;width:170px;flex-shrink:0;overflow-y:auto;margin:6px;font-size:12px"></div>
        </div>
      </div>

      <!-- BR: Annual Comparison -->
      <div class="ctry-cell">
        <div class="ctry-cell-hd">
          <span data-i18n="ctry_compare">Annual Paper Comparison</span>
          <div id="ctryChipList" style="display:flex;gap:4px;flex-wrap:wrap"></div>
        </div>
        <div class="ctry-cell-body">
          <div id="countryChart" style="position:absolute;inset:0;padding:8px"></div>
          <div class="ctry-ph" id="ctryChartPh">Click countries on the map to compare annual trends</div>
        </div>
      </div>

      <!-- 호환용 dummy (함수 display 토글 흡수) -->
      <div id="countryChartWrap" style="display:none"></div>
      <div id="ctryOntologyWrap" style="display:none"></div>
    </section>"""

c = c.replace(OLD_SECTION, NEW_SECTION)
print('HTML section replaced')

# ─────────────────────────────────────────────────────────────
# 3. fillCountry: 전체 국가 세로 막대
# ─────────────────────────────────────────────────────────────
OLD_FILL = re.search(r'function fillCountry\(\)\{.*?\n\}', c, re.DOTALL).group()

NEW_FILL = """function fillCountry(){
  const sorted = [...COUNTRIES].sort((a,b)=>b.papers-a.papers);
  const max = Math.max(...sorted.map(c=>c.papers), 1);
  const bars = document.getElementById("countryBars");
  if(!bars) return;
  bars.innerHTML = sorted.map((c,i)=>{
    const pct = Math.max(4, Math.round(c.papers/max*100));
    const col = _ctryColor(c.code);
    const lbl = c.papers>9999 ? (c.papers/1000).toFixed(0)+'k' : c.papers>999 ? (c.papers/1000).toFixed(1)+'k' : String(c.papers);
    return '<div class="ctry-vbar" data-i="'+i+'" data-code="'+c.code+'" title="'+cName(c)+': '+c.papers.toLocaleString()+' papers">'+
      '<span style="font-size:8px;color:var(--muted);line-height:1">'+lbl+'</span>'+
      '<div class="vb" style="height:'+pct+'%;min-height:3px;background:'+col+'"></div>'+
      '<span style="font-size:7px;color:var(--muted);max-width:28px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">'+c.code+'</span>'+
      '</div>';
  }).join("");
  bars.querySelectorAll(".ctry-vbar").forEach(el=>{
    el.onmouseenter = ()=>{ if(!_selCountries.has(el.dataset.code)) el.style.opacity='.7'; };
    el.onmouseleave = ()=>{ el.style.opacity='1'; };
    el.onclick = ()=> toggleCountry(sorted[+el.dataset.i]);
  });
}

function clearCtrySelection(){
  _selCountries.clear();
  Object.keys(_cmpColorMap).forEach(k=>delete _cmpColorMap[k]);
  document.querySelectorAll(".ctry-vbar").forEach(el=>el.style.opacity='1');
  const det=document.getElementById("countryDetail"); if(det) det.style.display="none";
  const clr=document.getElementById("ctryChartClear"); if(clr) clr.style.display="none";
  renderCountryChart();
  buildCountryOntology();
  if(window._mapSvEl) window._mapSvEl.selectAll(".country-shape").classed("sel",false);
}"""

c = c.replace(OLD_FILL, NEW_FILL)
print('fillCountry replaced')

# ─────────────────────────────────────────────────────────────
# 4. toggleCountry: 바 하이라이트 + 항상 양쪽 렌더 + placeholder/clear 버튼
# ─────────────────────────────────────────────────────────────
OLD_TG = re.search(r'  // 바 하이라이트\n  document\.querySelectorAll\(".bar-row"\)\.forEach.*?if\(n === 1\) buildCountryOntology\(\);\n  \}\)\);', c, re.DOTALL).group()

NEW_TG = """  // 바 하이라이트
  document.querySelectorAll(".ctry-vbar").forEach(el=>{
    const cc = el.dataset.code;
    el.style.opacity = (_selCountries.size === 0 || _selCountries.has(cc)) ? '1' : '0.3';
  });
  const n = _selCountries.size;
  const clrBtn = document.getElementById("ctryChartClear");
  if(clrBtn) clrBtn.style.display = n > 0 ? "" : "none";
  requestAnimationFrame(() => requestAnimationFrame(() => {
    renderCountryChart();
    buildCountryOntology();
  }));"""

c = c.replace(OLD_TG, NEW_TG)
print('toggleCountry replaced')

# ─────────────────────────────────────────────────────────────
# 5. renderCountryChart: placeholder 제어 (empty 시 clear)
# ─────────────────────────────────────────────────────────────
OLD_RC = """  if(_selCountries.size === 0){
    wrap.style.display = "none";
    document.getElementById("ctryOntologyWrap").style.display = "none";
    return;
  }
  wrap.style.display = "flex";"""

NEW_RC = """  const ph = document.getElementById("ctryChartPh");
  if(_selCountries.size === 0){
    if(container) container.innerHTML = "";
    if(chipList) chipList.innerHTML = "";
    if(ph) ph.style.display = "flex";
    return;
  }
  if(ph) ph.style.display = "none";"""

c = c.replace(OLD_RC, NEW_RC)
print('renderCountryChart placeholder')

# ─────────────────────────────────────────────────────────────
# 6. buildCountryOntology: placeholder 제어
# ─────────────────────────────────────────────────────────────
OLD_BO = """  // 1items 선택일 때만 표시
  if(_selCountries.size !== 1){ wrap.style.display = "none"; return; }
  wrap.style.display = "flex";"""

NEW_BO = """  // 1개 선택일 때만 표시
  const ph = document.getElementById("ctryOntoPh");
  if(_selCountries.size !== 1){
    if(container) container.innerHTML = "";
    if(ph) ph.style.display = "flex";
    return;
  }
  if(ph) ph.style.display = "none";"""

c = c.replace(OLD_BO, NEW_BO)
print('buildCountryOntology placeholder')

open(SRC, 'w', encoding='utf-8').write(c)
print(f'Done. {len(c):,} chars')
