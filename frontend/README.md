# Frontend

## Run

1. Install dependencies:
   npm install
2. Start dev server:
   npm run dev

The frontend defaults to same-origin API calls and uses Vite proxy (`/api` -> `http://127.0.0.1:8000`) during local dev.

Set `VITE_API_BASE_URL` only if you need a specific backend URL.

## Controls

- Start a new game with your selected color and bot mode.
- Click a piece, then click a highlighted destination square to move.
- You can still type UCI moves manually (for example `e2e4`).
- Use "Recommend Move" to call the backend recommendation endpoint.
- Use "Load PGN" then "Copy PGN" to export game notation.
