$ErrorActionPreference = "Stop"
$root = Get-Location
$stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$trash = Join-Path $root "_trash\$stamp"
$legacy = Join-Path $root "scripts\legacy"
New-Item -ItemType Directory -Force -Path $trash | Out-Null
New-Item -ItemType Directory -Force -Path $legacy | Out-Null

function Move-Safe($p) {
  if (Test-Path $p) {
    $rel = Resolve-Path $p
    $dest = Join-Path $trash (Split-Path $rel -Leaf)
    try { Move-Item -Force $p $dest } catch { Write-Warning "Skip $rel ($($_.Exception.Message))" }
  }
}

# 1) Py caches
Get-ChildItem -Recurse -Force -Directory -Filter "__pycache__" | % { Remove-Item -Recurse -Force $_.FullName -ErrorAction SilentlyContinue }
Get-ChildItem -Recurse -Force -File -Include *.pyc | % { Move-Safe $_.FullName }

# 2) Logs
Get-ChildItem -Recurse -Force -File -Include *.log | % { Move-Safe $_.FullName }

# 3) SQLite journaux (backend arrêté)
foreach ($f in @("smartlinks.db-shm","smartlinks.db-wal")) { if (Test-Path $f) { Move-Safe $f } }

# 4) db.sqlite3 si non référencée
$dbRef = Select-String -Path "src\**\*.py" -Pattern "db\.sqlite3" -ErrorAction SilentlyContinue
if ((Test-Path "db.sqlite3") -and (-not $dbRef)) { Move-Safe "db.sqlite3" }

# 5) Makefile.new si identique
if ((Test-Path "Makefile") -and (Test-Path "Makefile.new")) {
  if ((Get-Content Makefile -Raw) -eq (Get-Content Makefile.new -Raw)) { Move-Safe "Makefile.new" }
}

# 6) Scripts de debug → scripts\legacy
$debug = @("debug_*.py","verify_*.py","quick_*.py","simple_test.py","minimal_test.py","fix_*.py","force_data_generation.py","openai_*health*.py","openai_test.bat")
foreach ($pat in $debug) {
  Get-ChildItem -Force -File -Path $pat -ErrorAction SilentlyContinue | % {
    Move-Item -Force $_.FullName (Join-Path $legacy $_.Name) -ErrorAction SilentlyContinue
  }
}

# 7) Tests en racine → tests\
Get-ChildItem -Force -File -Filter "test_*.py" | % {
  $dest = Join-Path "$root\tests" $_.Name
  if (-not (Test-Path $dest)) { Move-Item -Force $_.FullName $dest -ErrorAction SilentlyContinue }
}

Write-Host "`n✅ Cleanup terminé. Archivés dans: $trash" -ForegroundColor Green
