import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open(r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html', encoding='utf-8').read()

# ── 1. Year View 버튼 추가 ──
c = c.replace(
    '<button class="evo-view-btn" data-eview="bump" data-i18n="btn_bump">\U0001f4c8 Rank Trend</button>',
    '<button class="evo-view-btn" data-eview="bump" data-i18n="btn_bump">\U0001f4c8 Rank Trend</button>\n'
    '            <button class="evo-view-btn" data-eview="year">\U0001f4c5 Year View</button>'
)

# ── 2. year view 컨트롤 div 삽입 ──
c = c.replace(
    '        <div id="evoTimeline"></div>',
    '        <!-- year view controls -->\n'
    '        <div id="evoYearCtrl" style="display:none;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:20px">\n'
    '          <button id="evoPlayBtn" onclick="evoPlayToggle()" style="background:var(--accent);color:#0e1116;border:none;border-radius:8px;padding:6px 18px;font-size:13px;font-weight:700;cursor:pointer">▶ Play</button>\n'
    '          <input type="range" id="evoYearSlider" min="2020" max="2025" value="2020" step="1"\n'
    '            style="width:200px;accent-color:var(--accent)" oninput="evoSetYear(+this.value)">\n'
    '          <span id="evoYearLabel" style="font-size:32px;font-weight:800;color:var(--accent);min-width:70px">2020</span>\n'
    '          <span style="font-size:12px;color:var(--muted)">bubble size = papers · color = theme · ★ = new this year</span>\n'
    '        </div>\n'
    '        <div id="evoTimeline"></div>'
)

# ── 3. _switchEvoView 패치 ──
old_switch = (
    'function _switchEvoView(){\n'
    '  const isTree = _evoView === "tree";\n'
    '  document.getElementById("evoTitle").textContent = isTree ? "Technology Emergence Tree" : "Technology Emergence Tracking — Monthly Rank";\n'
    '  document.getElementById("evoTreeCtrl").style.display = isTree ? "block" : "none";\n'
    '  document.getElementById("evoBumpCtrl").style.display = isTree ? "none" : "flex";\n'
    '  if(isTree) buildEvoTree();'
)
new_switch = (
    'function _switchEvoView(){\n'
    '  const isTree = _evoView === "tree";\n'
    '  const isYear = _evoView === "year";\n'
    '  document.getElementById("evoTitle").textContent =\n'
    '    isTree ? T("title_evo") : isYear ? (`${T("nav_evo")} — Year by Year`) : "Technology Rank Trend";\n'
    '  document.getElementById("evoTreeCtrl").style.display = isTree ? "block" : "none";\n'
    '  document.getElementById("evoBumpCtrl").style.display = (!isTree && !isYear) ? "flex" : "none";\n'
    '  document.getElementById("evoYearCtrl").style.display = isYear ? "flex" : "none";\n'
    '  if(isTree) buildEvoTree();\n'
    '  if(isYear){ evoStopPlay(); renderEvoYear(_evoCurrentYear||2020); }'
)
if old_switch in c:
    c = c.replace(old_switch, new_switch)
    print('_switchEvoView patched')
else:
    print('WARN: _switchEvoView not found')

# ── 4. renderEvoYear JS 함수 삽입 (buildEvoTree 앞) ──
EVO_YEAR_JS = r"""
/* ===================== EVO YEAR VIEW ===================== */
let _evoCurrentYear = 2020;
let _evoPlayTimer = null;
const EVO_YEARS = [2020,2021,2022,2023,2024,2025];

// 연도별 노드 paper count 캐시
function _evoYearData(){
  const cache = {};
  EVO_YEARS.forEach(yr=>{
    cache[yr] = {};
    NODES.forEach(n=>{
      let total = 0;
      Object.entries(n.monthly||{}).forEach(([m,cnt])=>{
        if(parseInt(m.slice(0,4))===yr) total+=cnt;
      });
      if(total>0) cache[yr][n.id]={count:total, group:n.group, parent:n.parent||null};
    });
  });
  return cache;
}
let _evoCache = null;

function renderEvoYear(year){
  _evoCurrentYear = year;
  if(!_evoCache) _evoCache = _evoYearData();

  document.getElementById('evoYearSlider').value = year;
  document.getElementById('evoYearLabel').textContent = year;

  const container = document.getElementById('evoTimeline');
  const data = _evoCache[year] || {};
  const prevData = year>2020 ? (_evoCache[year-1]||{}) : {};

  // 신규 등장: 이전 연도에 없던 키워드
  const isNew = id => !prevData[id];

  // paper count 기준 정렬, 상위 60개
  const items = Object.entries(data)
    .sort((a,b)=>b[1].count-a[1].count)
    .slice(0,60);

  if(!items.length){
    container.innerHTML = `<div style="padding:60px;text-align:center;color:var(--muted)">No data for ${year}</div>`;
    return;
  }

  const maxCount = items[0][1].count;

  // 그룹별 색상
  const html = `
    <div id="evoBubbleWrap" style="display:flex;flex-wrap:wrap;gap:10px;padding:16px 0;align-items:center">
      ${items.map(([id,d])=>{
        const pct = d.count/maxCount;
        const sz = Math.max(28, Math.round(28 + pct*60));
        const col = groupColor(d.group||'AI');
        const novel = isNew(id);
        return `<div class="evo-bubble${novel?' evo-bubble-new':''}"
          title="${id}: ${d.count.toLocaleString()} papers${novel?' ★ New this year':''}"
          style="
            background:${col}22;
            border:2px solid ${col}${novel?';box-shadow:0 0 8px '+col:''};
            color:${col};
            border-radius:${sz}px;
            padding:0 ${Math.round(sz*0.5)}px;
            height:${sz}px;
            font-size:${Math.max(10,Math.round(sz*0.3))}px;
            font-weight:700;
            display:inline-flex;align-items:center;gap:4px;
            cursor:default;white-space:nowrap;
            animation:bubblePop .35s ease both;
          ">${novel?'★ ':''}${id}
          <span style="font-size:${Math.max(9,Math.round(sz*0.26))}px;opacity:.7">${d.count>999?(d.count/1000).toFixed(1)+'k':d.count}</span>
        </div>`;
      }).join('')}
    </div>
    <div style="margin-top:16px;font-size:12px;color:var(--muted)">
      Showing top ${items.length} keywords · ${Object.keys(data).length} total active ·
      <span style="color:var(--accent)">★ ${items.filter(([id])=>isNew(id)).length} new this year</span>
    </div>`;

  container.innerHTML = html;
}

function evoSetYear(yr){
  renderEvoYear(yr);
}

function evoPlayToggle(){
  if(_evoPlayTimer){ evoStopPlay(); return; }
  const btn = document.getElementById('evoPlayBtn');
  btn.textContent = '⏸ Pause';
  if(_evoCurrentYear >= 2025) _evoCurrentYear = 2019;
  function step(){
    _evoCurrentYear = Math.min(_evoCurrentYear+1, 2025);
    renderEvoYear(_evoCurrentYear);
    if(_evoCurrentYear < 2025){
      _evoPlayTimer = setTimeout(step, 1200);
    } else {
      evoStopPlay();
    }
  }
  step();
}

function evoStopPlay(){
  if(_evoPlayTimer){ clearTimeout(_evoPlayTimer); _evoPlayTimer=null; }
  const btn = document.getElementById('evoPlayBtn');
  if(btn) btn.textContent = '▶ Play';
}
"""

# buildEvoTree 함수 앞에 삽입
if 'function buildEvoTree(' in c:
    c = c.replace('function buildEvoTree(', EVO_YEAR_JS + '\nfunction buildEvoTree(')
    print('EVO_YEAR_JS inserted')
else:
    print('WARN: buildEvoTree not found')

# ── 5. CSS 추가 ──
EVO_CSS = """
  @keyframes bubblePop{
    0%{transform:scale(0);opacity:0}
    70%{transform:scale(1.15)}
    100%{transform:scale(1);opacity:1}
  }
  .evo-bubble{transition:transform .15s}
  .evo-bubble:hover{transform:scale(1.08)!important}
  .evo-bubble-new{animation-duration:.5s!important}
"""
c = c.replace("</style>", EVO_CSS + "</style>")

open(r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html', 'w', encoding='utf-8').write(c)
print(f'Done. {len(c):,} chars')
