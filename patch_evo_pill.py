import sys, re
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas\index.html'
c = open(SRC, encoding='utf-8').read()

OLD = re.search(
    r'/\* ===================== EVO YEAR VIEW \(D3 force\) ===================== \*/.*?function evoStopPlay\(\)\{.*?\n\}',
    c, re.DOTALL
)
if not OLD:
    print('ERROR: block not found'); exit(1)

NEW = r"""/* ===================== EVO YEAR VIEW (pill layout) ===================== */
let _evoCurrentYear = 2020;
let _evoPlayTimer   = null;
const EVO_YEARS     = [2020,2021,2022,2023,2024,2025];

function _evoYearData(){
  const cache = {};
  EVO_YEARS.forEach(yr=>{
    cache[yr] = {};
    NODES.forEach(n=>{
      let total = 0;
      Object.entries(n.monthly||{}).forEach(([m,cnt])=>{
        if(parseInt(m.slice(0,4))===yr) total+=cnt;
      });
      if(total>0) cache[yr][n.id]={count:total, group:n.group};
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

  const data     = _evoCache[year]  || {};
  const prevData = year>2020 ? (_evoCache[year-1]||{}) : {};

  const items = Object.entries(data)
    .sort((a,b)=>b[1].count - a[1].count)
    .slice(0, 60);

  const maxCount = items[0]?.[1]?.count || 1;

  const wrap = document.getElementById('evoTimeline');

  // 기존 pill들 맵
  const existing = {};
  wrap.querySelectorAll('.evo-pill[data-id]').forEach(el=>{
    existing[el.dataset.id] = el;
  });

  const seen = new Set();

  items.forEach(([id, d], i)=>{
    seen.add(id);
    const pct    = d.count / maxCount;
    const fsize  = Math.max(10, Math.round(10 + pct * 14));
    const px     = Math.max(8, Math.round(8 + pct * 20));
    const py     = Math.max(4, Math.round(4 + pct * 8));
    const col    = groupColor(d.group||'AI');
    const isNew  = !prevData[id];

    if(existing[id]){
      // 기존 pill → CSS transition으로 크기/색상 업데이트
      const el = existing[id];
      el.style.fontSize   = fsize+'px';
      el.style.padding    = py+'px '+px+'px';
      el.style.borderColor = col;
      el.style.color      = col;
      el.style.background = col+'22';
      el.style.order      = i;
      el.style.opacity    = '1';
      el.style.transform  = 'scale(1)';
      // 텍스트 업데이트 (★ 제거)
      el.querySelector('.pill-text').textContent = id;
      el.querySelector('.pill-count').textContent = d.count > 999
        ? (d.count/1000).toFixed(1)+'k' : d.count;
      el.title = `${id}: ${d.count.toLocaleString()} papers`;
    } else {
      // 신규 pill → 생성 후 pop 애니메이션
      const el = document.createElement('div');
      el.className = 'evo-pill';
      el.dataset.id = id;
      el.style.cssText = [
        'display:inline-flex','align-items:center','gap:5px',
        `font-size:${fsize}px`,
        `padding:${py}px ${px}px`,
        `border:2px solid ${col}`,
        `color:${col}`,
        `background:${col}22`,
        'border-radius:999px',
        'font-weight:700',
        'cursor:default',
        'white-space:nowrap',
        'transition:font-size .4s, padding .4s, border-color .4s, color .4s, background .4s, opacity .35s, transform .35s',
        `order:${i}`,
        'opacity:0',
        'transform:scale(0.5)',
        isNew ? `box-shadow:0 0 8px ${col}88` : '',
      ].join(';');
      el.title = `${id}: ${d.count.toLocaleString()} papers${isNew?' ★ New':''}`;
      el.innerHTML = `${isNew?'<span style="font-size:.9em">★</span>':''}<span class="pill-text">${id}</span><span class="pill-count" style="opacity:.65;font-size:.85em">${d.count>999?(d.count/1000).toFixed(1)+'k':d.count}</span>`;
      wrap.appendChild(el);
      // 다음 프레임에 등장 애니메이션
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        el.style.opacity   = '1';
        el.style.transform = 'scale(1)';
      }));
    }
  });

  // 사라진 pill → fade out 후 제거
  Object.entries(existing).forEach(([id, el])=>{
    if(!seen.has(id)){
      el.style.opacity   = '0';
      el.style.transform = 'scale(0.4)';
      setTimeout(()=>{ if(el.parentNode) el.parentNode.removeChild(el); }, 380);
    }
  });

  // stat
  let stat = document.getElementById('evoYearStat');
  if(!stat){
    stat = document.createElement('div');
    stat.id = 'evoYearStat';
    stat.style.cssText = 'font-size:12px;color:var(--muted);margin-top:12px';
    wrap.after(stat);
  }
  const newCount = items.filter(([id])=>!prevData[id]).length;
  stat.innerHTML = `Showing top ${items.length} · ${Object.keys(data).length} total active · <span style="color:var(--accent)">★ ${newCount} new this year</span>`;
}

function evoSetYear(yr){ renderEvoYear(yr); }

function evoPlayToggle(){
  if(_evoPlayTimer){ evoStopPlay(); return; }
  const btn = document.getElementById('evoPlayBtn');
  btn.textContent = '⏸ Pause';
  if(_evoCurrentYear >= 2025) _evoCurrentYear = 2019;
  function step(){
    _evoCurrentYear = Math.min(_evoCurrentYear+1, 2025);
    renderEvoYear(_evoCurrentYear);
    if(_evoCurrentYear < 2025){
      _evoPlayTimer = setTimeout(step, 1600);
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
}"""

c = c[:OLD.start()] + NEW.strip() + c[OLD.end():]

# evoTimeline을 flex-wrap 컨테이너로 CSS 지정
EVO_PILL_CSS = """
  #evoTimeline.evo-pill-wrap{
    display:flex;flex-wrap:wrap;gap:8px;
    padding:12px 0;align-items:center;min-height:120px;
  }
"""
c = c.replace("</style>", EVO_PILL_CSS + "</style>")

# _switchEvoView: year 전환 시 evoTimeline에 flex 클래스 토글
c = c.replace(
    "  document.getElementById(\"evoTimeline\").innerHTML = \"\";\n"
    "  d3.select(\"#evoTimeline\").selectAll(\"*\").remove();",
    "  const _et = document.getElementById(\"evoTimeline\");\n"
    "  _et.innerHTML = \"\";\n"
    "  _et.className = (_evoView===\"year\") ? \"evo-pill-wrap\" : \"\";"
)

open(SRC, 'w', encoding='utf-8').write(c)
print(f'Done. {len(c):,} chars')
