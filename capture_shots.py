#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""배포 사이트 각 탭 스크린샷 → docs/"""
import sys, io, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

URL = "https://construction-knowledge-atlas.pages.dev"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
os.makedirs(OUT, exist_ok=True)

# (탭 data-view, 파일명, 클릭 후 대기초)
TABS = [
    ("latest",   "01-latest.png",   5),
    ("impact",   "02-impact.png",   4),
    ("graph",    "03-ontology.png", 7),
    ("country",  "04-country.png",  6),
    ("network",  "05-network.png",  7),
    ("evo",      "06-evolution.png",5),
    ("journals", "07-journals.png", 4),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome", headless=True)
    page = browser.new_context(viewport={"width":1600,"height":900}).new_page()
    print("loading site...")
    page.goto(URL, wait_until="networkidle", timeout=40000)
    time.sleep(8)  # 초기 데이터 로드

    for view, fname, wait in TABS:
        try:
            page.click(f'nav button[data-view="{view}"]', timeout=8000)
        except Exception:
            # 스크롤 레이아웃이면 다른 셀렉터
            try: page.click(f'[data-spy="view-{view}"]', timeout=5000)
            except Exception as e: print(f"  {view} click fail: {e}"); continue
        time.sleep(wait)
        path = os.path.join(OUT, fname)
        page.screenshot(path=path)
        print(f"  saved {fname}")

    browser.close()
print("done")
