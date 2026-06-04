"""
Country Analysis 개선 v2
- 레이아웃 구조 유지 (탭 격리 안전)
- Paper Rank: 전체 국가 세로 막대 (가로 스크롤)
- 지도 높이 확보
- 하단 차트/온톨로지는 기존 방식 유지
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
c = open(SRC, encoding='utf-8').read()

# ── 1. view-country HTML 교체 ──────────────────────────────────────
OLD_SECTION = """    <!-- COUNTRY -->
    <section class="view" id="view-country">
      <div class="panel-title" data-i18n="title_country">Country Tech Influence</div>
      <div class="panel-sub" data-i18n="sub_country">색이 진할수록 Paper Count가 많습니다. Click map or rank to see key institutions & technologies. 여러 나라를 클릭하면 연도별 비교 차트가 표시됩니다.</div>
      <div style="display:flex;gap:16px;padding:0 24px;height:420px;min-height:240px">
        <div class="map-wrap">
          <svg id="worldMap"></svg>
          <div class="maptip" id="mapTip"></div>
          <div class="map-legend">Paper Count<div class="grad"></div><span id="legLo">0</span> ~ <span id="legHi">max</span></div>
        </div>
        <div class="ctry-side">
          <h3 data-i18n="ctry_rank">Paper Rank</h3>
          <div id="countryBars"></div>
          <div class="country-detail card" id="countryDetail" style="display:none"></div>
        </div>
      </div>
      <!-- Comparison chart + ontology layout -->
      <div id="countryChartWrap" style="padding:8px 24px 20px;display:none;gap:16px;min-height:320px">
        <!-- Left: annual comparison chart -->
        <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:8px">
          <div style="display:flex;align-items:center;gap:10px">
            <span style="font-size:13px;font-weight:700;color:var(--txt)">Annual Paper Comparison</span>
            <div id="ctryChipList" style="display:flex;gap:6px;flex-wrap:wrap"></div>
            <button id="ctryChartClear" style="margin-left:auto;background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer">Clear Selection</button>
          </div>
          <div id="countryChart" style="height:280px;min-height:280px;position:relative"></div>
        </div>
        <!-- Right: Keyword Ontology (shown when 1 country selected) -->
        <div id="ctryOntologyWrap" style="flex:1;min-width:0;display:none;flex-direction:column;gap:6px">
          <div style="display:flex;align-items:center;gap:8px">
            <span id="ctryOntologyTitle" style="font-size:13px;font-weight:700;color:var(--txt)">Keyword Ontology</span>
            <span style="font-size:11px;color:var(--muted)">Node size = papers</span>
          </div>
          <div id="ctryOntologyGraph" style="flex:1;height:0;min-height:260px;position:relative;background:var(--panel2);border:1px solid var(--line);border-radius:8px;overflow:hidden"></div>
        </div>
      </div>
    </section>"""

NEW_SECTION = """    <!-- COUNTRY -->
    <section class="view" id="view-country" style="overflow-y:auto">
      <!-- 상단: 지도 + Paper Rank 나란히 -->
      <div style="display:flex;gap:0;padding:8px 20px 0;align-items:flex-start">
        <div style="font-size:20px;font-weight:800;padding-bottom:2px" data-i18n="title_country">Country Tech Influence</div>
        <span style="font-size:12px;color:var(--muted);margin-left:14px;align-self:center" data-i18n="sub_country">Darker = more papers · Click to explore</span>
        <button id="ctryChartClear" onclick="clearCtrySelection()" style="margin-left:auto;display:none;background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:4px 12px;font-size:11px;cursor:pointer">Clear Selection</button>
      </div>

      <!-- 지도 + 국가 상세 사이드바 -->
      <div style="display:flex;gap:16px;padding:8px 20px;height:400px;min-height:240px">
        <div class="map-wrap" style="flex:1">
          <svg id="worldMap"></svg>
          <div class="maptip" id="mapTip"></div>
          <div class="map-legend">Paper Count<div class="grad"></div><span id="legLo">0</span> ~ <span id="legHi">max</span></div>
        </div>
        <div class="country-detail card" id="countryDetail" style="display:none;width:220px;flex-shrink:0;overflow-y:auto"></div>
      </div>

      <!-- Paper Rank: 전체 국가 세로 막대 (가로 스크롤) -->
      <div style="padding:0 20px 8px">
        <div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.8px;text-transform:uppercase;margin-bottom:6px" data-i18n="ctry_rank">Paper Rank</div>
        <div style="overflow-x:auto;overflow-y:hidden;padding-bottom:4px">
          <div id="countryBars" style="display:flex;gap:3px;align-items:flex-end;height:130px;padding-bottom:20px;min-width:max-content"></div>
        </div>
      </div>

      <!-- 하단: Annual Comparison + Keyword Ontology (클릭 시) -->
      <div id="countryChartWrap" style="display:none;padding:0 20px 20px;gap:16px;min-height:300px">
        <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:6px">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:13px;font-weight:700;color:var(--txt)" data-i18n="ctry_compare">Annual Paper Comparison</span>
            <div id="ctryChipList" style="display:flex;gap:6px;flex-wrap:wrap"></div>
          </div>
          <div id="countryChart" style="height:260px;position:relative"></div>
        </div>
        <div id="ctryOntologyWrap" style="flex:1;min-width:0;display:none;flex-direction:column;gap:6px">
          <div style="display:flex;align-items:center;gap:8px">
            <span id="ctryOntologyTitle" style="font-size:13px;font-weight:700;color:var(--txt)">Keyword Ontology</span>
            <span style="font-size:11px;color:var(--muted)">Node size = papers</span>
          </div>
          <div id="ctryOntologyGraph" style="flex:1;height:0;min-height:260px;position:relative;background:var(--panel2);border:1px solid var(--line);border-radius:8px;overflow:hidden"></div>
        </div>
      </div>
    </section>"""

if OLD_SECTION in c:
    c = c.replace(OLD_SECTION, NEW_SECTION)
    print('HTML replaced')
else:
    print('NOT FOUND')

# ── 2. fillCountry: 전체 국가 세로 막대 ─────────────────────────────
OLD_FILL = '''function fillCountry(){
  const top = [...COUNTRIES].sort((a,b)=>b.papers-a.papers).slice(0,10);
  const max = Math.max(...top.map(c=>c.papers), 1);
  document.getElementById("countryBars").innerHTML = top.map((c,i)=>`
    <div class="bar-row" data-i="${i}" data-code="${c.code}" style="align-items:center">
      <div class="bar-label">${cName(c)}</div>
      <div class="bar-track" style="flex:1"><div class="bar-fill" style="width:${c.papers/max*100}%;padding-right:0"></div></div>
      <span style="font-size:12px;font-weight:700;color:var(--txt);margin-left:8px;min-width:52px;text-align:right">${c.papers.toLocaleString()}papers</span>
    </div>`).join("");
  document.querySelectorAll(".bar-row").forEach(r=>r.onclick=()=>toggleCountry(top[+r.dataset.i]));
  document.getElementById("ctryChartClear").onclick=()=>{
    _selCountries.clear();
    Object.keys(_cmpColorMap).forEach(k=>delete _cmpColorMap[k]);
    document.querySelectorAll(".bar-row").forEach(r=>r.style.opacity=1);
    document.getElementById("countryDetail").style.display="none";
    renderCountryChart();
    buildCountryOntology();
    if(window._mapSvEl) window._mapSvEl.selectAll(".country-shape").classed("sel",false);
  };
}'''

NEW_FILL = '''function fillCountry(){
  const sorted = [...COUNTRIES].sort((a,b)=>b.papers-a.papers);
  const max = Math.max(...sorted.map(c=>c.papers), 1);
  // 세로 막대 (전체 국가)
  document.getElementById("countryBars").innerHTML = sorted.map((c,i)=>{
    const h = Math.max(3, Math.round(c.papers/max*100));
    const col = _ctryColor(c.code);
    const label = c.papers > 9999 ? (c.papers/1000).toFixed(0)+'k' : c.papers > 999 ? (c.papers/1000).toFixed(1)+'k' : String(c.papers);
    return `<div class="ctry-vcol" data-i="${i}" data-code="${c.code}"
      title="${cName(c)}: ${c.papers.toLocaleString()} papers"
      style="display:flex;flex-direction:column;align-items:center;gap:2px;cursor:pointer;flex-shrink:0;width:30px;opacity:1;transition:opacity .15s">
      <span style="font-size:8px;color:var(--muted);line-height:1">${label}</span>
      <div style="width:18px;height:${h}px;min-height:3px;background:${col};border-radius:2px 2px 0 0;transition:height .3s,opacity .15s"></div>
      <span style="font-size:7px;color:var(--muted);white-space:nowrap;overflow:hidden;max-width:28px;text-overflow:ellipsis">${c.code}</span>
    </div>`;
  }).join("");
  document.querySelectorAll(".ctry-vcol").forEach(el=>{
    el.onmouseenter = ()=>{ if(!_selCountries.has(el.dataset.code)) el.style.opacity='.7'; };
    el.onmouseleave = ()=>{ el.style.opacity='1'; };
    el.onclick = ()=> toggleCountry(sorted[+el.dataset.i]);
  });
}

function clearCtrySelection(){
  _selCountries.clear();
  Object.keys(_cmpColorMap).forEach(k=>delete _cmpColorMap[k]);
  document.querySelectorAll(".ctry-vcol").forEach(el=>el.style.opacity='1');
  document.getElementById("countryDetail").style.display="none";
  document.getElementById("ctryChartClear").style.display="none";
  renderCountryChart();
  buildCountryOntology();
  if(window._mapSvEl) window._mapSvEl.selectAll(".country-shape").classed("sel",false);
}'''

if OLD_FILL in c:
    c = c.replace(OLD_FILL, NEW_FILL)
    print('fillCountry replaced')
else:
    print('WARN: fillCountry not found')

# ── 3. toggleCountry에서 Clear 버튼 표시 + ctry-vcol 하이라이트 ──────
OLD_TOGGLE = '  document.querySelectorAll(".bar-row").forEach(r=>{\n    const cc = r.dataset.code;\n    r.style.opacity = (_selCountries.size === 0 || _selCountries.has(cc)) ? 1 : 0.4;\n  });'
NEW_TOGGLE = '''  document.querySelectorAll(".ctry-vcol").forEach(el=>{
    const cc = el.dataset.code;
    el.style.opacity = (_selCountries.size === 0 || _selCountries.has(cc)) ? '1' : '0.3';
  });
  const clrBtn = document.getElementById("ctryChartClear");
  if(clrBtn) clrBtn.style.display = _selCountries.size > 0 ? "" : "none";'''

if OLD_TOGGLE in c:
    c = c.replace(OLD_TOGGLE, NEW_TOGGLE)
    print('toggleCountry highlight replaced')
else:
    print('WARN: toggleCountry bar-row not found - checking...')
    import re
    m = re.search(r'bar-row.*?opacity.*?0\.4', c, re.DOTALL)
    if m: print('found:', repr(m.group()[:100]))

open(SRC, 'w', encoding='utf-8').write(c)
print(f'Done. {len(c):,} chars')
