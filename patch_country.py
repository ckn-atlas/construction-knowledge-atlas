import sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
c = open(SRC, encoding='utf-8').read()

OLD = """    <!-- COUNTRY -->
    <section class="view" id="view-country" style="overflow-y:auto">
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

NEW = """    <!-- COUNTRY - 2x2 grid layout -->
    <section class="view" id="view-country" style="display:grid;grid-template-rows:36px 1fr 1fr;grid-template-columns:1fr 1fr;height:100%;overflow:hidden">

      <!-- 헤더 (전체 너비) -->
      <div style="grid-column:1/-1;display:flex;align-items:center;gap:12px;padding:0 16px;border-bottom:1px solid var(--line);background:var(--panel)">
        <span class="panel-title" data-i18n="title_country" style="padding:0;font-size:16px;font-weight:700">Country Tech Influence</span>
        <span style="font-size:11px;color:var(--muted)">Darker = more papers · Click to explore · Multi-select to compare</span>
        <button id="ctryChartClear" onclick="clearCountrySelection()" style="margin-left:auto;display:none;background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer">Clear Selection</button>
      </div>

      <!-- TOP-LEFT: World Map -->
      <div style="position:relative;border-right:1px solid var(--line);border-bottom:1px solid var(--line);overflow:hidden">
        <svg id="worldMap" style="width:100%;height:100%"></svg>
        <div class="maptip" id="mapTip"></div>
        <div class="map-legend" style="position:absolute;left:8px;bottom:8px">Paper Count<div class="grad"></div><span id="legLo">0</span> ~ <span id="legHi">max</span></div>
      </div>

      <!-- TOP-RIGHT: Keyword Ontology -->
      <div style="position:relative;border-bottom:1px solid var(--line);background:var(--panel2);overflow:hidden">
        <div style="position:absolute;top:8px;left:12px;z-index:2;display:flex;align-items:center;gap:8px;pointer-events:none">
          <span id="ctryOntologyTitle" style="font-size:12px;font-weight:700;color:var(--txt)">Keyword Ontology</span>
          <span style="font-size:11px;color:var(--muted)">Node size = papers</span>
        </div>
        <div id="ctryOntologyGraph" style="width:100%;height:100%;position:relative"></div>
        <div id="ctryOntologyPlaceholder" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px;pointer-events:none">
          Click a country to see keyword ontology
        </div>
      </div>

      <!-- BOTTOM-LEFT: Paper Rank (세로 막대, 가로 스크롤) -->
      <div style="border-right:1px solid var(--line);overflow:hidden;display:flex;flex-direction:column">
        <div style="padding:6px 12px 2px;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;flex-shrink:0">Paper Rank</div>
        <div style="flex:1;overflow-x:auto;overflow-y:hidden;padding:0 8px 4px">
          <div id="countryBars" style="display:flex;gap:4px;align-items:flex-end;height:100%;min-width:max-content;padding-bottom:22px"></div>
        </div>
      </div>

      <!-- BOTTOM-RIGHT: Annual Paper Comparison -->
      <div style="overflow:hidden;display:flex;flex-direction:column;padding:6px 12px 8px;position:relative">
        <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;margin-bottom:2px">
          <span style="font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">Annual Paper Comparison</span>
          <div id="ctryChipList" style="display:flex;gap:4px;flex-wrap:wrap"></div>
        </div>
        <div id="countryChart" style="flex:1;min-height:0;position:relative"></div>
        <div id="ctryChartPlaceholder" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px;pointer-events:none">
          Click countries to compare annual trends
        </div>
      </div>

      <!-- 호환성 유지 (기존 JS toggleCountry 참조용 숨김 요소) -->
      <div id="countryChartWrap" style="display:none"></div>
      <div id="ctryOntologyWrap" style="display:none"></div>
      <div class="country-detail card" id="countryDetail" style="display:none"></div>
    </section>"""

if OLD in c:
    c = c.replace(OLD, NEW)
    print('HTML replaced')
else:
    print('NOT FOUND - searching partial...')
    idx = c.find('<!-- COUNTRY -->')
    print('COUNTRY at:', idx)

# CSS: countryBars를 세로 막대 형식으로
# bar-row → 세로 막대 (flex column)
# bar-track → height 기반 세로바

# clearCountrySelection 함수 추가 (JS에 없으면 추가)
if 'function clearCountrySelection' not in c:
    c = c.replace(
        'function scrollSec(id){',
        '''function clearCountrySelection(){
  _selCountries.clear();
  document.querySelectorAll(".country-shape").forEach(el=>el.classList.remove("sel"));
  document.querySelectorAll(".bar-row").forEach(r=>r.style.opacity="1");
  document.getElementById("countryChart").innerHTML="";
  document.getElementById("ctryOntologyGraph").innerHTML="";
  const ph1=document.getElementById("ctryOntologyPlaceholder"); if(ph1) ph1.style.display="flex";
  const ph2=document.getElementById("ctryChartPlaceholder"); if(ph2) ph2.style.display="flex";
  const clr=document.getElementById("ctryChartClear"); if(clr) clr.style.display="none";
}
function scrollSec(id){'''
    )
    print('clearCountrySelection added')

open(SRC, 'w', encoding='utf-8').write(c)
print(f'Done. {len(c):,} chars')
