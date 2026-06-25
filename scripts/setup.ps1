# Meeting Translator setup — ffmpeg + faster-whisper (GPU enabled)
# Run once. Safe to re-run (idempotent).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Write-Host "=== Meeting Translator setup ===" -ForegroundColor Cyan

# 0) Local model cache (.models). Keep whisper model downloads inside the repo so
#    the agent is self-contained instead of relying on a machine-wide HF_HOME.
$models = Join-Path $root ".models"
if (-not (Test-Path $models)) { New-Item -ItemType Directory -Path $models | Out-Null }
$env:HF_HOME = $models
Write-Host "Model cache (HF_HOME): $models" -ForegroundColor Green

# 1) ffmpeg
$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ff) {
    Write-Host "ffmpeg not found, installing via winget..." -ForegroundColor Yellow
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    Write-Host "ffmpeg installed. You may need to reopen the terminal for PATH to update." -ForegroundColor Yellow
} else {
    Write-Host "ffmpeg found: $($ff.Source)" -ForegroundColor Green
}

# 2) python venv + dependencies
$venv = Join-Path $root ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating venv: $venv"
    python -m venv $venv
}
$py = Join-Path $venv "Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install -r (Join-Path $root "requirements.txt")

# 3) Pre-download the transcription model into .models (idempotent — skips if cached).
#    Avoids a surprise multi-GB download on the first real transcription.
Write-Host "Pre-downloading whisper model (large-v3) into .models ..." -ForegroundColor Cyan
$dl = @"
import os
from faster_whisper.utils import download_model
os.environ.setdefault('HF_HOME', r'$models')
path = download_model('large-v3')
print('MODEL_READY:', path)
"@
& $py -c $dl

# 4) GPU test (quick check with tiny model)
Write-Host "GPU test..." -ForegroundColor Cyan
$gpuTest = @"
from faster_whisper import WhisperModel
try:
    WhisperModel('tiny', device='cuda', compute_type='float16')
    print('GPU_OK')
except Exception as e:
    print('GPU_UNAVAILABLE:', e)
"@
& $py -c $gpuTest

Write-Host "=== Setup complete ===" -ForegroundColor Green
