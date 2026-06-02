import sys, re
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
c = open(SRC, encoding='utf-8').read()

# ── 기존 renderEvoYear 전체를 D3 버전으로 교체 ──
OLD_FN = re.search(
    r'/\* ===================== EVO YEAR VIEW ===================== \*/.*?function evoStopPlay\(\)\{.*?\n\}',
    c, re.DOTALL
)
if not OLD_FN:
    print('ERROR: EVO YEAR VIEW block not found')
    exit(1)

NEW_FN = r"""
/* ===================== EVO YEAR VIEW (D3 force) ===================== */
let _evoCurrentYear = 2020;
let _evoPlayTimer   = null;
let _evoSim         = null;       // D3 force simulation 인스턴스
let _evoNodePos     = {};         // {id: {x,y}} — 연도 전환 시 위치 보존
const EVO_YEARS     = [2020,2021,2022,2023,2024,2025];

/* 연도별 노드 paper count 캐시 */
function _evoYearData(){
  const cache = {};
  EVO_YEARS.forEach(yr => {
    cache[yr] = {};
    NODES.forEach(n => {
      let total = 0;
      Object.entries(n.monthly||{}).forEach(([m,cnt]) => {
        if(parseInt(m.slice(0,4)) === yr) total += cnt;
      });
      if(total > 0) cache[yr][n.id] = {count:total, group:n.group};
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

  const wrap   = document.getElementById('evoTimeline');
  const W      = wrap.clientWidth  || 900;
  const H      = 480;

  const data     = _evoCache[year]  || {};
  const prevData = year > 2020 ? (_evoCache[year-1]||{}) : {};

  /* 상위 55개 */
  const items = Object.entries(data)
    .sort((a,b) => b[1].count - a[1].count)
    .slice(0, 55);

  const maxCount = items[0]?.[1]?.count || 1;
  const r = d => Math.max(18, Math.round(18 + (d.count/maxCount)*44));

  /* SVG 초기화 (최초 1회) */
  let svg = d3.select('#evoTimeline').select('svg.evo-yr-svg');
  if(svg.empty()){
    svg = d3.select('#evoTimeline').append('svg')
      .attr('class','evo-yr-svg')
      .style('width','100%')
      .style('overflow','visible');
    d3.select('#evoTimeline').append('div')
      .attr('id','evoYearStat')
      .style('font-size','12px')
      .style('color','var(--muted)')
      .style('margin-top','8px');
  }
  svg.attr('height', H);

  /* D3 data join */
  const nodeData = items.map(([id, d]) => {
    const prev = _evoNodePos[id];
    return {
      id,
      count : d.count,
      group : d.group,
      isNew : !prevData[id],
      x     : prev ? prev.x : W/2 + (Math.random()-0.5)*60,
      y     : prev ? prev.y : H/2 + (Math.random()-0.5)*60,
      vx:0, vy:0,
    };
  });

  /* Force simulation */
  if(_evoSim) _evoSim.stop();

  // 테마별 x 목표 위치
  const groupOrder = Object.keys(GROUP_KO);
  const themeX = id => {
    const g = (data[id]||{}).group;
    const idx = groupOrder.indexOf(g);
    const total = groupOrder.length;
    return W * 0.08 + (W * 0.84) * (idx<0 ? 0.5 : idx/(total-1));
  };

  _evoSim = d3.forceSimulation(nodeData)
    .force('x',       d3.forceX(d => themeX(d.id)).strength(0.12))
    .force('y',       d3.forceY(H/2).strength(0.06))
    .force('collide', d3.forceCollide(d => r(d) + 3).strength(0.85))
    .force('charge',  d3.forceManyBody().strength(-20))
    .alphaDecay(0.03)
    .on('tick', ticked);

  /* enter / update / exit */
  const sel = svg.selectAll('g.evo-bubble-g')
    .data(nodeData, d => d.id);

  /* EXIT */
  sel.exit()
    .transition().duration(350)
    .style('opacity', 0)
    .attr('transform', d => `translate(${d.x},${d.y}) scale(0)`)
    .remove();

  /* ENTER */
  const entered = sel.enter().append('g')
    .attr('class','evo-bubble-g')
    .attr('transform', d => `translate(${d.x},${d.y}) scale(0)`)
    .style('opacity', 0)
    .style('cursor','default');

  entered.append('circle').attr('class','evo-circ');
  entered.append('text').attr('class','evo-lbl').attr('text-anchor','middle').attr('dominant-baseline','middle');
  entered.append('title');

  /* ENTER 애니메이션 */
  entered.transition().duration(420).delay((d,i)=>i*18)
    .attr('transform', d => `translate(${d.x},${d.y}) scale(1)`)
    .style('opacity', 1);

  /* MERGE: update 공통 속성 */
  const merged = entered.merge(sel);

  merged.select('title').text(d =>
    `${d.id}: ${d.count.toLocaleString()} papers${d.isNew?' ★ New this year':''}`
  );

  /* circle + text smooth transition (기존 노드는 크기 변화만) */
  merged.filter(d => !d.isNew)
    .select('circle.evo-circ')
    .transition().duration(500)
    .attr('r', d => r(d))
    .attr('fill', d => groupColor(d.group)+'33')
    .attr('stroke', d => groupColor(d.group))
    .attr('stroke-width', 1.5);

  merged.filter(d => d.isNew)
    .select('circle.evo-circ')
    .attr('r', d => r(d))
    .attr('fill', d => groupColor(d.group)+'44')
    .attr('stroke', d => groupColor(d.group))
    .attr('stroke-width', 2.5)
    .style('filter', d => `drop-shadow(0 0 5px ${groupColor(d.group)})`);

  merged.select('text.evo-lbl')
    .transition().duration(500)
    .attr('font-size', d => Math.max(9, Math.round(r(d)*0.32))+'px')
    .attr('font-weight', d => d.isNew ? '800' : '700')
    .attr('fill', d => groupColor(d.group))
    .text(d => (d.isNew?'★ ':'')+d.id);

  function ticked(){
    svg.selectAll('g.evo-bubble-g')
      .attr('transform', d => {
        d.x = Math.max(r(d), Math.min(W-r(d), d.x));
        d.y = Math.max(r(d), Math.min(H-r(d), d.y));
        _evoNodePos[d.id] = {x:d.x, y:d.y};
        return `translate(${d.x},${d.y})`;
      });
  }

  /* stat bar */
  const newCount = items.filter(([id])=>!prevData[id]).length;
  d3.select('#evoYearStat').html(
    `Showing top ${items.length} keywords · ${Object.keys(data).length} total active · `+
    `<span style="color:var(--accent)">★ ${newCount} new this year</span>`
  );
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
      _evoPlayTimer = setTimeout(step, 1800);
    } else {
      evoStopPlay();
    }
  }
  step();
}

function evoStopPlay(){
  if(_evoPlayTimer){ clearTimeout(_evoPlayTimer); _evoPlayTimer = null; }
  const btn = document.getElementById('evoPlayBtn');
  if(btn) btn.textContent = '▶ Play';
}
"""

c = c[:OLD_FN.start()] + NEW_FN.strip() + c[OLD_FN.end():]
print('Replaced EVO YEAR VIEW block')

# bubblePop keyframe 제거 (더이상 불필요)
c = c.replace(
    '  @keyframes bubblePop{\n    0%{transform:scale(0);opacity:0}\n    70%{transform:scale(1.15)}\n    100%{transform:scale(1);opacity:1}\n  }\n  .evo-bubble{transition:transform .15s}\n  .evo-bubble:hover{transform:scale(1.08)!important}\n  .evo-bubble-new{animation-duration:.5s!important}\n',
    ''
)

open(SRC, 'w', encoding='utf-8').write(c)
print(f'Done. {len(c):,} chars')
