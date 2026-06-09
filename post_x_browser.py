#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_x_browser.py — Playwright로 X.com에 카드 이미지 + 텍스트 게시

사용:
  python post_x_browser.py          # changed.flag=1 일 때만 게시
  python post_x_browser.py --force  # 강제 게시
  python post_x_browser.py --dry    # 미리보기만
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE   = os.path.dirname(os.path.abspath(__file__))
SOCIAL = os.path.join(BASE, "data", "social")
CARD   = os.path.join(SOCIAL, "card.png")
CAP    = os.path.join(SOCIAL, "caption.txt")
FLAG   = os.path.join(SOCIAL, "changed.flag")
PW_PROFILE = os.path.join(SOCIAL, "pw_profile")

def log(m): print(m, flush=True)

def main():
    args  = sys.argv[1:]
    force = "--force" in args
    dry   = "--dry"   in args

    flag = open(FLAG).read().strip() if os.path.exists(FLAG) else "0"
    if flag != "1" and not force:
        log("변경 없음(flag=0) — 게시 안 함"); return

    if not os.path.exists(CARD):
        log("[!] card.png 없음 — generate_social_card.py 먼저 실행"); return

    text = open(CAP, encoding="utf-8").read().strip() if os.path.exists(CAP) else ""
    log("=== X 게시 준비 (브라우저) ===")
    log(f"  트윗({len(text)}자):\n{text}\n")

    if dry:
        log("[--dry] 실제 게시 생략"); return

    os.makedirs(PW_PROFILE, exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=PW_PROFILE,
            channel="chrome",
            headless=False,
            slow_mo=500,
            args=["--disable-blink-features=AutomationControlled"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        log("1) x.com 접속...")
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # 홈 피드가 아니면 로그인 필요
        if "x.com/home" not in page.url:
            log("  → 브라우저에서 X 이메일/비밀번호로 로그인해주세요 (최대 3분 대기)...")
            page.wait_for_url("*x.com/home*", timeout=180000)
            page.wait_for_timeout(3000)
            log("  → 로그인 완료!")

        log("2) 트윗 작성창 클릭...")
        compose = page.get_by_test_id("tweetTextarea_0")
        compose.wait_for(timeout=15000)
        compose.click()
        page.wait_for_timeout(1000)

        log("3) 텍스트 입력...")
        page.keyboard.type(text, delay=30)
        page.wait_for_timeout(1000)

        log("4) 이미지 첨부...")
        # hidden file input에 직접 파일 설정 (클릭 불필요)
        file_input = page.locator('input[data-testid="fileInput"]').first
        file_input.set_input_files(CARD)
        page.wait_for_timeout(5000)  # 업로드 대기

        # 이미지 업로드 확인 스크린샷
        page.screenshot(path=os.path.join(os.path.dirname(CARD), "_before_post.png"))
        log("  → 업로드 확인 스크린샷 저장")

        log("5) 게시 버튼 클릭...")
        post_btn = page.get_by_test_id("tweetButtonInline")
        post_btn.wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(2000)
        # JavaScript로 직접 클릭 (오버레이 우회)
        page.evaluate("""
            const btn = document.querySelector('[data-testid="tweetButtonInline"]');
            if (btn) btn.click();
        """)
        page.wait_for_timeout(4000)
        page.wait_for_timeout(3000)

        log("[완료] 게시됨!")
        ctx.close()

    open(FLAG, "w").write("0")
    log("flag 리셋 완료")

if __name__ == "__main__":
    main()
