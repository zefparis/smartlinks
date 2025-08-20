function Set-Env {
  if (-not $env:VIRTUAL_ENV -and (Test-Path .\.venv\Scripts\Activate.ps1)) { . .\.venv\Scripts\Activate.ps1 }
  $env:PYTHONPATH = "src"
}
function S1 { Set-Env; python -m soft.router }
function S2 { Set-Env; python -m soft.autopilot }
function Seed { Set-Env; python -m soft.initdb; python -m soft.simulate }
function Health([string]$Base="http://127.0.0.1:8000") { Invoke-RestMethod -Uri "$Base/health" -Method GET }
function Probe([string]$u="creator_1",[string]$geo="FR",[string]$device="mobile",[string]$Base="http://127.0.0.1:8000"){
  $resp = Invoke-WebRequest -Uri "$Base/r/x?u=$u&geo=$geo&device=$device" -MaximumRedirection 0 -ErrorAction SilentlyContinue
  [PSCustomObject]@{ Status=$resp.StatusCode; Location=$resp.Headers.Location; ClickId=$resp.Headers["X-Click-Id"] }
}
function Smoke([int]$n=5,[string]$u="creator_1",[string]$geo="FR",[string]$device="mobile",[string]$Base="http://127.0.0.1:8000"){
  1..$n | ForEach-Object { Probe -u $u -geo $geo -device $device -Base $Base }
}
"Loaded: S1, S2, Seed, Health, Probe, Smoke"
