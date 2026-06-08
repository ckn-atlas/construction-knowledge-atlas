#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_linkedin.py — data/social/card.png + caption.txt 를 LinkedIn에 게시

게시 조건: data/social/changed.flag == "1" (generate_social_card.py가 신규 감지 시)

필요 설정 (data/social/linkedin_config.json):
{
  "access_token": "AQ...",        # LinkedIn OAuth 2.0 토큰
  "author_urn": "urn:li:person:XXXX"   # 또는 urn:li:organization:XXXX
}
※ linkedin_config.json 은 .gitignore 권장 (토큰 노출 방지)

사용:
  python post_linkedin.py          # flag=1일 때만 게시
  python post_linkedin.py --force  # 강제 게시
  python post_linkedin.py --dry    # 게시 안 하고 점검만
"""
import sys, io, os, json, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE   = os.path.dirname(os.path.abspath(__file__))
SOCIAL = os.path.join(BASE, "data", "social")
CARD   = os.path.join(SOCIAL, "card.png")
CAP    = os.path.join(SOCIAL, "caption.txt")
FLAG   = os.path.join(SOCIAL, "changed.flag")
CONF   = os.path.join(SOCIAL, "linkedin_config.json")

API = "https://api.linkedin.com/v2"

def log(m): print(m, flush=True)

def load_config():
    if not os.path.exists(CONF):
        log(f"[!] 설정 파일 없음: {CONF}")
        log("    linkedin_config.json 에 access_token, author_urn 입력 필요")
        return None
    return json.load(open(CONF, encoding="utf-8"))

def register_upload(token, author_urn):
    """이미지 업로드 슬롯 등록"""
    url = f"{API}/assets?action=registerUpload"
    body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    r = requests.post(url, json=body, headers={
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }, timeout=30)
    r.raise_for_status()
    d = r.json()["value"]
    asset = d["asset"]
    upload_url = d["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    return asset, upload_url

def upload_image(upload_url, token):
    with open(CARD, "rb") as f:
        img = f.read()
    r = requests.post(upload_url, data=img, headers={
        "Authorization": f"Bearer {token}",
    }, timeout=60)
    r.raise_for_status()

def create_post(token, author_urn, asset, text):
    url = f"{API}/ugcPosts"
    body = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "media": asset,
                    "title": {"text": "Latest Research Highlights"},
                }],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = requests.post(url, json=body, headers={
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }, timeout=30)
    r.raise_for_status()
    return r.headers.get("x-restli-id", "?")

def main():
    args = sys.argv[1:]
    force = "--force" in args
    dry   = "--dry" in args

    # 변경 플래그 확인
    flag = open(FLAG).read().strip() if os.path.exists(FLAG) else "0"
    if flag != "1" and not force:
        log("변경 없음(flag=0) — 게시 안 함")
        return

    if not os.path.exists(CARD) or not os.path.exists(CAP):
        log("[!] card.png / caption.txt 없음 — generate_social_card.py 먼저 실행")
        return

    text = open(CAP, encoding="utf-8").read()
    log("=== 게시 준비 ===")
    log(f"  이미지: {CARD}")
    log(f"  캡션 {len(text)}자")

    if dry:
        log("[--dry] 실제 게시 생략")
        return

    conf = load_config()
    if not conf:
        return
    token = conf["access_token"]
    author = conf["author_urn"]

    try:
        log("1) 업로드 슬롯 등록...")
        asset, up_url = register_upload(token, author)
        log("2) 이미지 업로드...")
        upload_image(up_url, token)
        log("3) 게시 생성...")
        pid = create_post(token, author, asset, text)
        log(f"[완료] LinkedIn 게시됨: {pid}")
        # 게시 후 flag 리셋
        open(FLAG, "w").write("0")
    except requests.HTTPError as e:
        log(f"[X] HTTP 오류: {e}")
        log(f"    응답: {e.response.text[:300]}")
    except Exception as e:
        log(f"[X] 오류: {e}")

if __name__ == "__main__":
    main()
