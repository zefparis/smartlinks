# scripts\cleanup.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $root) { $root = Get-Location }
Set-Location $root

$stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$trash = Join-Path $root "_trash\$stamp"
$legacy = Join-Path $root "scripts\legacy"
New-Item -ItemType Directory -Force -Path $trash | Out-Null
New-Item -ItemType Directory -Force -Path $legacy | Out-Null

Write-Host "🔧 Cleanup starting in $root" -ForegroundColor Cyan
$archived = New-Object System.Collections.Generic.List[string]

function Move-Safe($path) {
  if (Test-Path $path) {
    $rel = Resolve-Path $path
    $dest = Join-Path $trash ((Split-Path $rel -Leaf))
    try {
      Move-Item -Force -Path $path -Destination $dest
      $archived.Add($rel)
    } catch {
      Write-Warning "Skip $rel ($($_.Exception.Message))"
    }
  }
}

# 1) __pycache__ + *.pyc
Get-ChildItem -Recurse -Force -Directory -Filter "__pycache__" | ForEach-Object {
  $target = $_.FullName
  try { Remove-Item -Recurse -Force $target; $archived.Add($target) } catch {}
}
Get-ChildItem -Recurse -Force -File -Include *.pyc | ForEach-Object {
  Move-Safe $_.FullName
}

# 2) Logs
Get-ChildItem -Recurse -Force -File -Include *.log | ForEach-Object {
  Move-Safe $_.FullName
}

# 3) SQLite WAL/SHM (si backend arrêté)
foreach ($f in @("smartlinks.db-shm","smartlinks.db-wal")) {
  if (Test-Path $f) { Move-Safe $f }
}

# 4) db.sqlite3 si non référencée
$dbRef = Select-String -Path "src\**\*.py" -Pattern "db\.sqlite3" -ErrorAction SilentlyContinue
if ((Test-Path "db.sqlite3") -and (-not $dbRef)) {
  Move-Safe "db.sqlite3"
}

# 5) Makefile.new si identique à Makefile
if ((Test-Path "Makefile") -and (Test-Path "Makefile.new")) {
  $a = Get-Content "Makefile" -Raw
  $b = Get-Content "Makefile.new" -Raw
  if ($a -eq $b) {
    Move-Safe "Makefile.new"
  } else {
    Write-Host "ℹ️ Makefile.new diffère de Makefile → conservé" -ForegroundColor Yellow
  }
}

# 6) Optionnel agressif: déplacer les scripts de debug dans scripts\legacy
$debugPatterns = @("debug_*.py","verify_*.py","quick_*.py","simple_test.py","minimal_test.py","fix_*.py","force_data_generation.py","openai_*health*.py","openai_test.bat")
foreach ($pat in $debugPatterns) {
  Get-ChildItem -Force -File -Path $pat -ErrorAction SilentlyContinue | ForEach-Object {
    $dest = Join-Path $legacy $_.Name
    try { Move-Item -Force $_.FullName $dest; $archived.Add($_.FullName) } catch {}
  }
}

# 7) Déplacer tests en racine -> tests\
Get-ChildItem -Force -File -Filter "test_*.py" | ForEach-Object {
  $dest = Join-Path "$root\tests" $_.Name
  if (-not (Test-Path $dest)) {
    try { Move-Item -Force $_.FullName $dest; $archived.Add($_.FullName) } catch {}
  }
}

# 8) Node_modules racine (optionnel) si non utilisé
if (Test-Path "node_modules") {
  if (-not (Test-Path "package.json")) {
    Move-Safe "node_modules"
  } else {
    Write-Host "ℹ️ node_modules en racine conservé (package.json présent)" -ForegroundColor Yellow
  }
}

# Résumé
Write-Host "`n✅ Cleanup terminé" -ForegroundColor Green
Write-Host "📦 Archivés → $trash"
Write-Host ("• " + ($archived | ForEach-Object { Split-Path $_ -Leaf } | Sort-Object) -join "`n• ")
