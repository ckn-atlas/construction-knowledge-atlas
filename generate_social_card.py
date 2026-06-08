#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_social_card.py — Latest 데이터로 LinkedIn 카드 이미지 + 캡션 생성

출력:
  data/social/card.png      — 1200x1200 브랜드 카드 (digest)
  data/social/caption.txt   — LinkedIn 게시용 본문

실행: python generate_social_card.py
daily_update.ps1 의 generate_latest.py 다음에 추가하면 매일 자동 생성됨.
"""
import sys, io, os, json, html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
LATEST = os.path.join(BASE, "data", "latest.json")
OUTDIR = os.path.join(BASE, "data", "social")
SITE   = "https://construction-knowledge-atlas.pages.dev"

GROUP_EMOJI = {
    "AI":"🤖","Vision":"📷","Material":"🧱","Structural":"🏗️","Eco":"🌿",
    "Mgmt":"👷","BIM":"📐","Geo":"⛏️","Robot":"🦾","DT":"🔮","Sensing":"📡",
}
GROUP_COLOR = {
    "AI":"#4dabf7","Vision":"#9775fa","Material":"#ff922b","Structural":"#ff6b6b",
    "Eco":"#51cf66","Mgmt":"#fab005","BIM":"#22b8cf","Geo":"#a98467",
    "Robot":"#f06595","DT":"#cc5de8","Sensing":"#20c997",
}

def esc(s): return html.escape(str(s or ""))

def build_html(data):
    papers = data.get("papers", [])
    # FWCI 내림차순, 상위 5개 강조
    papers = sorted(papers, key=lambda p: (p.get("fwci") or 0), reverse=True)
    date_from = data.get("date_from", "")
    today = datetime.now().strftime("%Y.%m.%d")

    rows = ""
    for p in papers:
        g = p.get("group","")
        col = GROUP_COLOR.get(g, "#4dabf7")
        emo = GROUP_EMOJI.get(g, "🔬")
        title = esc(p.get("title",""))[:95]
        journal = esc(p.get("journal",""))
        fwci = p.get("fwci")
        fwci_badge = f'<span class="fwci">FWCI {fwci:.1f}</span>' if fwci and fwci>0 else ''
        rows += f'''
        <div class="row">
          <div class="theme" style="background:{col}22;color:{col};border:1px solid {col}66">{emo} {esc(p.get("group_label",g))}</div>
          <div class="paper">
            <div class="ti">{title}</div>
            <div class="jr">{journal} {fwci_badge}</div>
          </div>
        </div>'''

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  *{{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI','Malgun Gothic',sans-serif}}
  body{{width:1200px;height:1200px;background:linear-gradient(135deg,#0e1116 0%,#161b22 100%);color:#e6edf3;padding:60px 56px;display:flex;flex-direction:column}}
  .brand{{display:flex;align-items:center;gap:14px;margin-bottom:8px}}
  .brand .logo{{font-size:34px}}
  .brand .name{{font-size:30px;font-weight:800}}
  .brand .name span{{color:#4dabf7}}
  .head{{font-size:46px;font-weight:800;margin:18px 0 6px;line-height:1.15}}
  .sub{{font-size:20px;color:#8b97a6;margin-bottom:28px}}
  .rows{{flex:1;display:flex;flex-direction:column;gap:14px}}
  .row{{display:flex;align-items:center;gap:18px;background:rgba(255,255,255,.03);border:1px solid #2a323d;border-radius:14px;padding:16px 20px}}
  .theme{{font-size:17px;font-weight:700;border-radius:20px;padding:6px 14px;white-space:nowrap;min-width:150px;text-align:center}}
  .paper{{flex:1;min-width:0}}
  .ti{{font-size:21px;font-weight:600;line-height:1.3;color:#e6edf3;margin-bottom:4px}}
  .jr{{font-size:16px;color:#8b97a6}}
  .fwci{{display:inline-block;background:#1a3550;color:#63e6be;border-radius:6px;padding:1px 8px;font-size:13px;font-weight:700;margin-left:6px}}
  .foot{{display:flex;align-items:center;justify-content:space-between;margin-top:26px;padding-top:22px;border-top:1px solid #2a323d}}
  .foot .url{{font-size:22px;font-weight:700;color:#4dabf7}}
  .foot .tag{{font-size:17px;color:#8b97a6}}
</style></head><body>
  <div class="brand"><span class="logo">🏗️</span><span class="name">Construction <span>Knowledge Atlas</span></span></div>
  <div class="head">Latest Research Highlights</div>
  <div class="sub">Top-cited construction & civil engineering papers · since {esc(date_from)}</div>
  <div class="rows">{rows}</div>
  <div class="foot"><span class="url">construction-knowledge-atlas.pages.dev</span><span class="tag">{today} · 222 journals · 260K+ papers</span></div>
</body></html>'''

def build_caption(data):
    papers = sorted(data.get("papers",[]), key=lambda p:(p.get("fwci") or 0), reverse=True)
    date_from = data.get("date_from","")
    lines = [
        "🏗️ Construction Knowledge Atlas — Latest Research Highlights",
        f"Top construction & civil engineering papers (since {date_from}):",
        "",
    ]
    for p in papers[:6]:
        emo = GROUP_EMOJI.get(p.get("group",""), "🔬")
        t = (p.get("title","") or "")[:90]
        j = p.get("journal","")
        lines.append(f"{emo} {t} — {j}")
    lines += [
        "",
        f"Explore all 11 themes, 222 journals, 260K+ papers:",
        SITE,
        "",
        "#construction #civilengineering #BIM #research #AEC #structuralengineering #constructiontech",
    ]
    return "\n".join(lines)

def _signature(data):
    # 게시 내용 변경 감지용: 논문 제목+저널 집합
    import hashlib
    items = sorted((p.get("title","")+"|"+p.get("journal","")) for p in data.get("papers",[]))
    return hashlib.md5("\n".join(items).encode("utf-8")).hexdigest()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    data = json.load(open(LATEST, encoding="utf-8"))
    if not data.get("papers"):
        print("latest.json 비어있음 — 카드 생성 생략"); return

    # 변경 감지: 이전 시그니처와 같으면 신규 카드 생성 안 함
    sig = _signature(data)
    sig_path = os.path.join(OUTDIR, "last_signature.txt")
    prev = open(sig_path, encoding="utf-8").read().strip() if os.path.exists(sig_path) else ""
    changed = (sig != prev)
    # 플래그 파일: post_linkedin.py가 이걸 보고 게시 여부 결정
    open(os.path.join(OUTDIR, "changed.flag"), "w").write("1" if changed else "0")
    if not changed:
        print("변경 없음 — 기존 카드 유지, 게시 안 함")
        return
    open(sig_path, "w", encoding="utf-8").write(sig)
    print("신규 내용 감지 — 카드 생성")

    html_str = build_html(data)
    html_path = os.path.join(OUTDIR, "_card.html")
    open(html_path, "w", encoding="utf-8").write(html_str)

    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        page = b.new_context(viewport={"width":1200,"height":1200}, device_scale_factor=2).new_page()
        page.goto("file://" + html_path.replace("\\","/"))
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(OUTDIR, "card.png"), clip={"x":0,"y":0,"width":1200,"height":1200})
        b.close()

    open(os.path.join(OUTDIR, "caption.txt"), "w", encoding="utf-8").write(build_caption(data))
    print(f"생성 완료:")
    print(f"  {os.path.join(OUTDIR,'card.png')}")
    print(f"  {os.path.join(OUTDIR,'caption.txt')}")

if __name__ == "__main__":
    main()
