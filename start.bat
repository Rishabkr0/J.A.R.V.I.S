@echo off
echo Starting J.A.R.V.I.S...

echo Starting backend...
start "JARVIS Backend" cmd /k "cd backend && if exist venv\Scripts\activate (call venv\Scripts\activate) && uvicorn app.main:app --reload --loop asyncio"

echo Starting frontend...
start "JARVIS Frontend" cmd /k "cd frontend && npm run dev"

echo Services have been launched in separate windows!
