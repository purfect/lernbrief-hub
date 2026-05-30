$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$exePath = Join-Path $PSScriptRoot "dist\Lernbrief-Hub.exe"

# Prevent WinError 5 by stopping running app instances before rebuilding.
if (Test-Path ".\stop_lernbrief_hub.ps1") {
  & .\stop_lernbrief_hub.ps1
}

# Remove previous build output with a short retry loop in case the handle is released with delay.
for ($i = 1; $i -le 5; $i++) {
  if (-not (Test-Path $exePath)) {
    break
  }
  try {
    Remove-Item $exePath -Force
    break
  } catch {
    if ($i -eq 5) {
      throw "Konnte $exePath nicht entfernen. Bitte Lernbrief-Hub beenden und erneut versuchen."
    }
    Start-Sleep -Milliseconds 500
  }
}

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install "pyinstaller>=6.20.0"

python -m PyInstaller --noconfirm --clean --windowed --onefile --name "Lernbrief-Hub" `
  --add-data "templates;templates" `
  --add-data "static;static" `
  app.py

Write-Host "Build fertig: dist\Lernbrief-Hub.exe"
