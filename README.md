# J.A.R.V.I.S.

An intelligent personal assistant architecture designed for extreme lightweight local execution.

## Project Structure
- `backend/`: FastAPI Python backend with asynchronous WebSockets, Event Bus, and modular Brain routing.
- `frontend/`: React + TypeScript frontend utilizing Vite.
- `docs/`: Product Requirements and Changelogs.

## Prerequisites
- Python 3.10+
- Node.js v18+
- Optional: A Gemini API Key for Phase 1 functionality.

## Setup & Startup (Phase 1)

### 1. Configuration
In the `backend/` folder, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your `GEMINI_API_KEY`:
```
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-3.6-flash
MAX_CONVERSATION_MESSAGES=20
```
> **SECURITY WARNING:** Never commit `.env` or share your API key. The `.gitignore` prevents checking this file in.

### 2. Start Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

## Running Tests
Tests use a mocked Gemini provider so they won't consume API quota.
```bash
cd backend
.\venv\Scripts\activate
pytest
```

## Manual Gemini Smoke Test
1. Complete the configuration steps above with a valid API key.
2. Start both the backend and frontend.
3. Open `http://localhost:5173` in your browser.
4. Verify the backend and WS status are **CONNECTED**.
5. Type "Hello Jarvis" in the chat box and hit Enter.
6. Observe the text streaming live as JARVIS generates a response.
7. Follow up with "Explain a black hole."
8. Follow up with "What did I just ask you about?" to verify conversation history works.

## Current Capabilities (Phase 3)
- **IMPLEMENTED:** 
  - FastAPI backend, React streaming text chat, Event Bus, WebSocket layer, API Provider abstractions, Gemini streaming integration, session memory.
  - **Fast Command Engine**: Local NLP intent mapping via `FastRouter` for instantaneous action.
  - **Tool Registry**: Deterministic Windows tools (Open Application, Safe URL Launching, Hardware Volume Control, System Information query, Directory Listing).
  - **Real-Time Voice Interface**: Local audio capture, openwakeword activation, INT8 faster-whisper STT, piper-tts sequential synthesis.
- **DEFERRED:** Persistent DB, Local ML intent classifiers, 3D HUD, Knowledge Galaxy.
