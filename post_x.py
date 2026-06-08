#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_x.py — data/social/card.png + caption 을 X(Twitter)에 게시

게시 조건: data/social/changed.flag == "1" (내용 변경 시에만)

필요 설정 (data/social/x_config.json):
{
  "api_key": "...",
  "api_secret": "...",
  "access_token": "...",
  "access_token_secret": "..."
}
※ x_config.json 은 .gitignore (토큰 노출 금지)
※ 앱 권한은 반드시 "Read and Write"

사용:
  python post_x.py          # flag=1일 때만 게시
  python post_x.py --force  # 강제 게시
  python post_x.py --dry    # 점검만
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import tweepy

BASE   = os.path.dirname(os.path.abspath(__file__))
SOCIAL = os.path.join(BASE, "data", "social")
CARD   = os.path.join(SOCIAL, "card.png")
CAP    = os.path.join(SOCIAL, "caption.txt")
FLAG   = os.path.join(SOCIAL, "changed.flag")
CONF   = os.path.join(SOCIAL, "x_config.json")

SITE = "https://construction-knowledge-atlas.pages.dev"
MAXLEN = 280

def log(m): print(m, flush=True)

def load_config():
    if not os.path.exists(CONF):
        log(f"[!] 설정 없음: {CONF}")
        log("    x_config.json 에 api_key/api_secret/access_token/access_token_secret 입력")
        return None
    return json.load(open(CONF, encoding="utf-8"))

def build_tweet_text():
    """280자 제한 맞춘 트윗 본문 — caption.txt에서 핵심만 추림"""
    data = json.load(open(os.path.join(BASE,"data","latest.json"), encoding="utf-8"))
    papers = sorted(data.get("papers",[]), key=lambda p:(p.get("fwci") or 0), reverse=True)
    date_from = data.get("date_from","")
    EMO = {"AI":"🤖","Vision":"📷","Material":"🧱","Structural":"🏗️","Eco":"🌿",
           "Mgmt":"👷","BIM":"📐","Geo":"⛏️","Robot":"🦾","DT":"🔮","Sensing":"📡"}
    # 테마 이모지 한 줄 + 최상위 논문 1편 + 링크
    themes = " ".join(EMO.get(p.get("group",""), "🔬") for p in papers)
    top = papers[0] if papers else {}
    top_title = (top.get("title","") or "").strip()
    top_journal = top.get("journal","")
    head = f"🏗️ Latest Construction & Civil Engineering Research\n(since {date_from}) · {len(papers)} themes\n\n{themes}\n\n"
    tail = f"\n\nFull highlights · 222 journals · 260K+ papers:\n{SITE}\n#construction #civilengineering #research"
    # 최상위 논문 한 줄 (들어가는 만큼)
    feat = ""
    cand = f"⭐ {top_title} — {top_journal}\n"
    if len(head)+len(cand)+len(tail) <= MAXLEN:
        feat = cand
    else:
        # 제목만 잘라서
        room = MAXLEN - len(head) - len(tail) - len(f"⭐  — {top_journal}\n") - 1
        if room > 20:
            feat = f"⭐ {top_title[:room]}… — {top_journal}\n"
    out = (head + feat + tail)[:MAXLEN]
    # 빈 줄 3개 이상 정리
    import re as _re
    return _re.sub(r"\n{3,}", "\n\n", out)

def main():
    args = sys.argv[1:]
    force = "--force" in args
    dry   = "--dry" in args

    flag = open(FLAG).read().strip() if os.path.exists(FLAG) else "0"
    if flag != "1" and not force:
        log("변경 없음(flag=0) — 게시 안 함")
        return

    if not os.path.exists(CARD):
        log("[!] card.png 없음 — generate_social_card.py 먼저 실행")
        return

    text = build_tweet_text()
    log("=== X 게시 준비 ===")
    log(f"  이미지: {CARD}")
    log(f"  트윗({len(text)}자):\n{text}\n")

    if dry:
        log("[--dry] 실제 게시 생략")
        return

    conf = load_config()
    if not conf:
        return

    try:
        # v1.1 API (미디어 업로드용)
        auth = tweepy.OAuth1UserHandler(
            conf["api_key"], conf["api_secret"],
            conf["access_token"], conf["access_token_secret"]
        )
        api_v1 = tweepy.API(auth)
        log("1) 이미지 업로드...")
        media = api_v1.media_upload(CARD)

        # v2 API (트윗 생성)
        client = tweepy.Client(
            consumer_key=conf["api_key"], consumer_secret=conf["api_secret"],
            access_token=conf["access_token"], access_token_secret=conf["access_token_secret"]
        )
        log("2) 트윗 게시...")
        resp = client.create_tweet(text=text, media_ids=[media.media_id])
        tid = resp.data.get("id","?")
        log(f"[완료] 게시됨: https://x.com/i/status/{tid}")
        open(FLAG, "w").write("0")  # 게시 후 리셋
    except Exception as e:
        log(f"[X] 오류: {e}")

if __name__ == "__main__":
    main()
