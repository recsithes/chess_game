# Render Deployment Guide

This project includes a Render blueprint at [render.yaml](../render.yaml) for:

1. `chess-game-backend` (FastAPI web service)
2. `chess-game-frontend` (Vite static site)

## One-Time Setup

1. Push this repository to GitHub.
2. In Render, click `New +` -> `Blueprint`.
3. Select your repository.
4. Render will detect [render.yaml](../render.yaml) and create both services.

## Important Environment Values

The defaults in [render.yaml](../render.yaml) assume these hostnames:

1. Frontend: `https://chess-game-frontend.onrender.com`
2. Backend: `https://chess-game-backend.onrender.com`

If Render assigns different names, update these values:

1. Backend `CORS_ORIGINS`
2. Frontend `VITE_API_BASE_URL`

## Backend Notes

1. Start command uses Render's `$PORT` automatically.
2. Current default DB is SQLite (`sqlite:///./chess_game.db`).
3. On free instances, filesystem can be ephemeral; DB may reset on redeploy/restart.

For persistent production data, switch `DATABASE_URL` to a managed Postgres instance.

## Post-Deploy Checks

1. Open backend health URL: `https://<backend-service>.onrender.com/health`
2. Open frontend URL and start a new game.
3. Verify no browser CORS errors in devtools.

## Troubleshooting

1. If Render shows `unknown type "static"`, update `render.yaml` to use `type: static_site` for the frontend service.
