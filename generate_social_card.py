#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_social_card.py — 신규 논문 1편 X 카드 이미지 생성

출력:
  data/social/card.png      — 1200x675 논문 카드 (사진 + 논문 정보)
  data/social/caption.txt   — X 게시용 본문
  data/social/changed.flag  — 1=신규 / 0=변경없음

실행: python generate_social_card.py
"""
import sys, io, os, json, html, re, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE   = os.path.dirname(os.path.abspath(__file__))
LATEST = os.path.join(BASE, "data", "latest.json")
OUTDIR = os.path.join(BASE, "data", "social")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
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
GROUP_HASHTAG = {
    "AI":"#AI #MachineLearning","Vision":"#ComputerVision #Sensing",
    "Material":"#BuildingMaterials #Concrete","Structural":"#StructuralEngineering",
    "Eco":"#GreenBuilding #Sustainability","Mgmt":"#ConstructionManagement",
    "BIM":"#BIM #DigitalConstruction","Geo":"#Geotechnical",
    "Robot":"#Robotics #Automation","DT":"#DigitalTwin","Sensing":"#Sensing #Monitoring",
}

def esc(s): return html.escape(str(s or ""))

def gpt_application_summary(title: str, abstract: str) -> str:
    """GPT-4o-mini로 논문 실무 활용 가능성 1문장 생성"""
    if not OPENAI_KEY or not abstract:
        return ""
    prompt = (
        f"Title: {title}\nAbstract: {abstract[:800]}\n\n"
        "In one concise English sentence (under 100 chars), explain how this "
        "construction/civil engineering paper could be useful in practice. "
        "Start with 'This could help...' or 'Useful for...' or similar."
    )
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.5,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {OPENAI_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        text = resp["choices"][0]["message"]["content"].strip()
        return re.split(r'(?<=[.!?])\s+', text)[0][:120]
    except Exception as e:
        print(f"  GPT 오류: {e}")
        return ""

def summarize_abstract(abstract: str, max_chars: int = 160) -> str:
    """abstract 첫 완전한 문장 추출 (Gemini 폴백용)"""
    if not abstract:
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', abstract.strip())
    out = ""
    for s in sentences:
        candidate = (out + " " + s).strip() if out else s
        if len(candidate) <= max_chars:
            out = candidate
        else:
            break
    return out or abstract[:max_chars] + "…"

def fetch_image(url: str, dest: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            open(dest, "wb").write(r.read())
        return True
    except Exception as e:
        print(f"  이미지 다운로드 실패: {e}")
        return False

def build_html(paper: dict, img_b64: str | None) -> str:
    g      = paper.get("group", "")
    color  = GROUP_COLOR.get(g, "#4dabf7")
    emoji  = GROUP_EMOJI.get(g, "🔬")
    label  = esc(paper.get("group_label", g))
    title  = esc(paper.get("title", ""))
    journal = esc(paper.get("journal", ""))
    date   = esc(paper.get("date", "")[:7])
    fwci   = paper.get("fwci")
    fwci_html = f'<span class="fwci">FWCI {fwci:.1f}</span>' if fwci and fwci > 0 else ""
    summary = esc(summarize_abstract(paper.get("abstract", "")))
    photo_credit = ""
    if paper.get("image") and paper["image"].get("photographer"):
        photo_credit = f'Photo by {esc(paper["image"]["photographer"])} on Unsplash'

    if img_b64:
        bg_style = f'background-image:url("data:image/jpeg;base64,{img_b64}");background-size:cover;background-position:center;'
    else:
        bg_style = f'background:linear-gradient(135deg,#0e1116,#1a2535);'

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  *{{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI','Malgun Gothic',sans-serif}}
  body{{width:1200px;height:675px;position:relative;overflow:hidden;color:#fff;{bg_style}}}
  .overlay{{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.35) 0%,rgba(0,0,0,.82) 52%,rgba(0,0,0,.97) 100%)}}
  .content{{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;padding:36px 52px 32px}}
  .brand{{display:flex;align-items:center;gap:10px;margin-bottom:auto}}
  .brand-icon{{font-size:22px}}
  .brand-name{{font-size:19px;font-weight:700;color:rgba(255,255,255,.85)}}
  .brand-name span{{color:#4dabf7}}
  .body{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:14px}}
  .badge{{display:inline-flex;align-items:center;gap:7px;background:{color}22;color:{color};border:1px solid {color}88;border-radius:20px;padding:5px 16px;font-size:15px;font-weight:700;width:fit-content}}
  .title{{font-size:30px;font-weight:800;line-height:1.3;color:#fff;max-width:960px}}
  .meta{{font-size:15px;color:rgba(255,255,255,.6);display:flex;align-items:center;gap:10px}}
  .fwci{{background:#1a3550;color:#63e6be;border-radius:5px;padding:2px 8px;font-size:13px;font-weight:700}}
  .summary{{font-size:17px;color:rgba(255,255,255,.78);line-height:1.55;max-width:980px}}
  .footer{{display:flex;align-items:center;justify-content:space-between;margin-top:18px;padding-top:14px;border-top:1px solid rgba(255,255,255,.12)}}
  .url{{font-size:16px;font-weight:700;color:#4dabf7}}
  .credit{{font-size:12px;color:rgba(255,255,255,.35)}}
</style></head><body>
  <div class="overlay"></div>
  <div class="content">
    <div class="brand"><span class="brand-icon">🏗️</span><span class="brand-name">Construction <span>Knowledge Atlas</span></span></div>
    <div class="body">
      <div class="badge">{emoji} {label}</div>
      <div class="title">{title}</div>
      <div class="meta">{journal} · {date} {fwci_html}</div>
      <div class="summary">{summary}</div>
    </div>
    <div class="footer">
      <span class="url">construction-knowledge-atlas.pages.dev</span>
      <span class="credit">{photo_credit}</span>
    </div>
  </div>
</body></html>'''

def build_tweet(paper: dict, ai_summary: str = "") -> str:
    g      = paper.get("group", "")
    emoji  = GROUP_EMOJI.get(g, "🔬")
    label  = paper.get("group_label", g)
    tags   = GROUP_HASHTAG.get(g, "#construction") + " #CivilEngineering #Research"

    summary = ai_summary or summarize_abstract(paper.get("abstract", ""), max_chars=120)

    head  = f"{emoji} {label} 분야 신규 논문\n\n"
    body  = f"{summary}\n\n" if summary else ""
    foot  = f"🔗 {SITE}\n{tags}"

    tweet = head + body + foot
    if len(tweet) > 280:
        room = 280 - len(head) - len(foot) - 4
        body = summary[:room] + "…\n\n" if room > 20 else ""
        tweet = (head + body + foot)[:280]
    return tweet

def _signature(data: dict) -> str:
    import hashlib
    items = sorted((p.get("title","") + "|" + p.get("journal","")) for p in data.get("papers", []))
    return hashlib.md5("\n".join(items).encode("utf-8")).hexdigest()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    data = json.load(open(LATEST, encoding="utf-8"))
    if not data.get("papers"):
        print("latest.json 비어있음 — 카드 생성 생략"); return

    sig      = _signature(data)
    sig_path = os.path.join(OUTDIR, "last_signature.txt")
    prev     = open(sig_path, encoding="utf-8").read().strip() if os.path.exists(sig_path) else ""
    changed  = (sig != prev)
    open(os.path.join(OUTDIR, "changed.flag"), "w").write("1" if changed else "0")
    if not changed:
        print("변경 없음 — 기존 카드 유지, 게시 안 함"); return
    open(sig_path, "w", encoding="utf-8").write(sig)
    print("신규 내용 감지 — 카드 생성")

    # FWCI 최고 논문 1편 선택
    papers = sorted(data["papers"], key=lambda p: (p.get("fwci") or 0), reverse=True)
    paper  = papers[0]

    # GPT로 활용 요약 생성
    print("GPT 활용 요약 생성 중...")
    ai_summary = gpt_application_summary(
        paper.get("title", ""),
        paper.get("abstract", ""),
    )
    if ai_summary:
        print(f"  → {ai_summary}")

    # Unsplash 이미지 다운로드 → base64
    img_b64 = None
    img_url = (paper.get("image") or {}).get("url", "")
    if img_url:
        img_path = os.path.join(OUTDIR, "_bg.jpg")
        if fetch_image(img_url, img_path):
            import base64
            img_b64 = base64.b64encode(open(img_path, "rb").read()).decode()

    html_str  = build_html(paper, img_b64)
    html_path = os.path.join(OUTDIR, "_card.html")
    open(html_path, "w", encoding="utf-8").write(html_str)

    with sync_playwright() as pw:
        b    = pw.chromium.launch(channel="chrome", headless=True)
        page = b.new_context(viewport={"width":1200,"height":675}, device_scale_factor=2).new_page()
        page.goto("file://" + html_path.replace("\\", "/"))
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUTDIR, "card.png"),
                        clip={"x":0,"y":0,"width":1200,"height":675})
        b.close()

    tweet = build_tweet(paper, ai_summary)
    open(os.path.join(OUTDIR, "caption.txt"), "w", encoding="utf-8").write(tweet)

    print(f"생성 완료:")
    print(f"  {os.path.join(OUTDIR, 'card.png')}")
    print(f"  트윗({len(tweet)}자):\n{tweet}")

if __name__ == "__main__":
    main()
