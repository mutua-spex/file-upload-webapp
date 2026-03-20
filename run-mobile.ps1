# Run in PowerShell
# Creates a virtual environment (if missing) and starts the Kivy mobile client.

$env:PYTHONUTF8 = 1
if (-not (Test-Path .\mobile\.venv)) {
    python -m venv .\mobile\.venv
}

& .\mobile\.venv\Scripts\Activate.ps1
pip install -r .\mobile\requirements.txt
python .\mobile\main.py
