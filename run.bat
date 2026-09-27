@echo off
echo Starting glances-mini...
call .venv\Scripts\activate.bat
python -m uvicorn glances_mini.web.app:app --app-dir src --reload --port 8001