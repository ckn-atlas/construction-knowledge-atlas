# Construction Knowledge Atlas - Daily Update Script
# Runs automatically via Windows Task Scheduler

$ProjectDir = "D:\0_PycharmProject\pythonProject\027_ConstructionKnowledgeAtlas"
$LogFile    = "$ProjectDir\daily_update.log"
$Python     = "python"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts  $msg" | Tee-Object -FilePath $LogFile -Append
}

Log "=== Daily Update Started ==="
Set-Location $ProjectDir

# 1. 신규 논문 수집 (마지막 수집일 이후 증분)
Log "Step 1: collect.py update"
& $Python collect.py update 2>&1 | ForEach-Object { Log "  $_" }

# 2. Latest 논문 (18개 저널, abstract + Unsplash 이미지)
Log "Step 2: generate_latest.py"
& $Python generate_latest.py 2>&1 | ForEach-Object { Log "  $_" }

# 3. index2.html 재생성 (스크롤 레이아웃)
Log "Step 3: make_scroll.py"
& $Python make_scroll.py 2>&1 | ForEach-Object { Log "  $_" }

# 4. sitemap 날짜 업데이트
$today = Get-Date -Format "yyyy-MM-dd"
(Get-Content "sitemap.xml") -replace '<lastmod>.*</lastmod>', "<lastmod>$today</lastmod>" |
    Set-Content "sitemap.xml" -Encoding UTF8
Log "Step 4: sitemap updated to $today"

# 5. Git 커밋 & 푸시
Log "Step 5: git push"
git add data/*.json sitemap.xml index2.html 2>&1 | ForEach-Object { Log "  $_" }
$msg = "data: auto daily update $today"
git commit -m $msg 2>&1 | ForEach-Object { Log "  $_" }
git push 2>&1 | ForEach-Object { Log "  $_" }

Log "=== Daily Update Completed ==="
