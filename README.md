# Chess ML Game (Full Stack)

Production-ready chess web app with:

1. FastAPI backend (game state, bot moves, recommendations, PGN)
2. React + Vite frontend (click-to-move board, move history, PGN copy)
3. SQLite persistence
4. Engine bot + optional ML model integration
5. Docker deployment setup
6. Render blueprint for cloud deployment

## Project Structure

1. `backend/`: API, chess logic, persistence, tests
2. `frontend/`: UI
3. `ml/`: data, train, eval scripts
4. `docker-compose.yml`: multi-container deployment

## Local Development

Quick start scripts (PowerShell):

1. `./scripts/run-backend.ps1`
2. `./scripts/run-frontend.ps1`

### Backend

Run from repository root in PowerShell:

```powershell
Set-Location "C:\Users\sithe\OneDrive\Desktop\web_dev\chess_game\backend"
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Backend health:

1. `http://127.0.0.1:8000/health`

### Frontend

Open a second terminal:

```powershell
Set-Location "C:\Users\sithe\OneDrive\Desktop\web_dev\chess_game\frontend"
npm install
npm run dev
```

Frontend URL:

1. `http://localhost:5173`

## Testing

```powershell
Set-Location "C:\Users\sithe\OneDrive\Desktop\web_dev\chess_game\backend"
& .\.venv\Scripts\python.exe -m pytest -q
```

## API Overview

1. `POST /api/games`
2. `GET /api/games/{game_id}`
3. `POST /api/games/{game_id}/move`
4. `GET /api/games/{game_id}/recommendation`
5. `GET /api/games/{game_id}/pgn`
6. `GET /api/system/bot-health`

## Environment Variables

Backend:

1. `DATABASE_URL` (default: `sqlite:///./chess_game.db`)
2. `STOCKFISH_PATH` (optional)
3. `ML_MODEL_PATH` (optional)
4. `ML_CONFIDENCE_THRESHOLD` (default: `0.2`)
5. `CORS_ORIGINS` (comma-separated)

Frontend:

1. `VITE_API_BASE_URL` (optional)
2. If unset, frontend uses same-origin requests and Vite proxy for local dev.

## Docker Deployment

### 1) Build and Start

From repository root:

```powershell
copy .env.example .env
docker compose up --build
```

### 2) URLs

1. Frontend: `http://localhost:8080`
2. Backend: `http://localhost:8000`
3. Backend health: `http://localhost:8000/health`

### 3) Stop

```powershell
docker compose down
```

## Render Deployment

This repository includes a Render blueprint file at `render.yaml`.

1. Push code to GitHub.
2. In Render, create a new `Blueprint` and select your repository.
3. Render provisions:
	1. `chess-game-backend` (FastAPI web service)
	2. `chess-game-frontend` (static site)
4. If Render gives different hostnames, update:
	1. Backend `CORS_ORIGINS`
	2. Frontend `VITE_API_BASE_URL`

Detailed steps: `docs/render-deploy.md`

## ML Pipeline Starter

```powershell
Set-Location "C:\Users\sithe\OneDrive\Desktop\web_dev\chess_game"
python ml/data/download_lichess.py
python ml/data/preprocess_pgn.py
python ml/train/train_model.py
python ml/eval/evaluate.py
```

## Troubleshooting

1. PowerShell path typo: use `& .\.venv\Scripts\python.exe ...` (not `..venv`).
2. CORS issues: verify backend is running and `CORS_ORIGINS` includes frontend origin.
3. If local DB schema changed during development, remove `backend/chess_game.db` and restart backend.
# chess_game
