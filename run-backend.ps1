# Run in PowerShell
# Creates a virtual environment (if missing) and starts the FastAPI backend.

$env:PYTHONUTF8 = 1
if (-not (Test-Path .\backend\.venv)) {
    python -m venv .\backend\.venv
}

& .\backend\.venv\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
