$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

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
