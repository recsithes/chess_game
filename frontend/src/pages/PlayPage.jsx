import React, { useMemo, useState } from "react";

import { ChessBoard, PIECE_MAP } from "../components/ChessBoard";

const rawApiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "").trim();
const normalizedApiBaseUrl = rawApiBaseUrl.endsWith("/") ? rawApiBaseUrl.slice(0, -1) : rawApiBaseUrl;
const API_BASE_URL = normalizedApiBaseUrl || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

async function parseJsonPayload(response) {
  const rawText = await response.text();
  if (!rawText) {
    return null;
  }

  try {
    return JSON.parse(rawText);
  } catch {
    throw new Error(`Server returned invalid JSON (HTTP ${response.status}).`);
  }
}

function pickApiErrorMessage(response, payload, fallback) {
  if (payload && typeof payload === "object" && typeof payload.detail === "string") {
    return payload.detail;
  }

  return `${fallback} (HTTP ${response.status})`;
}

function normalizeRequestError(error, fallback) {
  if (!(error instanceof Error)) {
    return fallback;
  }

  if (/Failed to fetch|NetworkError|Load failed/i.test(error.message)) {
    return "Cannot reach backend API. Start backend at http://127.0.0.1:8000 and try again.";
  }

  return error.message || fallback;
}

const INITIAL_PIECE_COUNTS = {
  K: 1,
  Q: 1,
  R: 2,
  B: 2,
  N: 2,
  P: 8,
  k: 1,
  q: 1,
  r: 2,
  b: 2,
  n: 2,
  p: 8,
};

const CAPTURE_ORDER = ["q", "r", "b", "n", "p"];

const PIECE_VALUE = {
  q: 9,
  r: 5,
  b: 3,
  n: 3,
  p: 1,
};

function capitalize(value) {
  return value ? `${value[0].toUpperCase()}${value.slice(1)}` : "";
}

function prettyTermination(termination) {
  if (!termination) {
    return "game finished";
  }
  return termination.replace(/_/g, " ");
}

function statusHeadline(game) {
  if (!game) {
    return "Create a game to begin";
  }

  if (game.status === "active") {
    if (game.is_check) {
      return `${capitalize(game.turn)} to move - Check`;
    }
    return `${capitalize(game.turn)} to move`;
  }

  if (game.winner) {
    return `${capitalize(game.winner)} wins by ${prettyTermination(game.termination)}`;
  }

  return `Draw by ${prettyTermination(game.termination)}`;
}

function legalTargetsForSquare(legalMoves, fromSquare) {
  return legalMoves
    .filter((move) => move.startsWith(fromSquare))
    .map((move) => move.slice(2, 4))
    .filter((square, index, collection) => collection.indexOf(square) === index);
}

function composeMoveFromSelection(legalMoves, fromSquare, toSquare) {
  const baseMove = `${fromSquare}${toSquare}`;
  return legalMoves.includes(baseMove) ? baseMove : null;
}

function promotionOptionsForMove(legalMoves, fromSquare, toSquare) {
  const base = `${fromSquare}${toSquare}`;
  const options = [];
  for (const piece of ["q", "r", "b", "n"]) {
    if (legalMoves.includes(`${base}${piece}`)) {
      options.push(piece);
    }
  }
  return options;
}

function buildMoveRows(moves) {
  const rows = [];
  for (let index = 0; index < moves.length; index += 2) {
    rows.push({
      number: Math.floor(index / 2) + 1,
      white: moves[index] || "",
      black: moves[index + 1] || "",
    });
  }
  return rows;
}

function moveColorByIndex(index) {
  return index % 2 === 0 ? "white" : "black";
}

function opponentLastMoveMetadata(moves, sanMoves, playerColor) {
  if (!moves || moves.length === 0) {
    return { uci: null, san: null };
  }

  const opponentColor = playerColor === "white" ? "black" : "white";
  for (let index = moves.length - 1; index >= 0; index -= 1) {
    if (moveColorByIndex(index) === opponentColor) {
      return {
        uci: moves[index] || null,
        san: sanMoves?.[index] || null,
      };
    }
  }

  return { uci: null, san: null };
}

function countPiecesFromFen(fen) {
  const counts = { ...INITIAL_PIECE_COUNTS };
  Object.keys(counts).forEach((key) => {
    counts[key] = 0;
  });

  if (!fen) {
    return counts;
  }

  const boardPart = fen.split(" ")[0];
  for (const char of boardPart) {
    if (Object.prototype.hasOwnProperty.call(counts, char)) {
      counts[char] += 1;
    }
  }

  return counts;
}

function buildCapturedPieces(fen) {
  if (!fen) {
    return { capturedByWhite: [], capturedByBlack: [] };
  }

  const current = countPiecesFromFen(fen);
  const capturedByWhite = [];
  const capturedByBlack = [];

  for (const piece of ["q", "r", "b", "n", "p"]) {
    const missing = INITIAL_PIECE_COUNTS[piece] - current[piece];
    for (let index = 0; index < missing; index += 1) {
      capturedByWhite.push(piece);
    }
  }

  for (const piece of ["Q", "R", "B", "N", "P"]) {
    const missing = INITIAL_PIECE_COUNTS[piece] - current[piece];
    for (let index = 0; index < missing; index += 1) {
      capturedByBlack.push(piece.toLowerCase());
    }
  }

  return { capturedByWhite, capturedByBlack };
}

function captureSummary(pieces) {
  const tally = new Map();
  for (const piece of pieces) {
    tally.set(piece, (tally.get(piece) || 0) + 1);
  }

  return CAPTURE_ORDER.filter((piece) => tally.has(piece)).map((piece) => ({
    piece,
    symbol: PIECE_MAP[piece],
    count: tally.get(piece),
    points: (PIECE_VALUE[piece] || 0) * (tally.get(piece) || 0),
  }));
}

function captureScore(pieces) {
  return pieces.reduce((score, piece) => score + (PIECE_VALUE[piece] || 0), 0);
}

export function PlayPage() {
  const [playerColor, setPlayerColor] = useState("white");
  const [botMode, setBotMode] = useState("engine");
  const [botLevel, setBotLevel] = useState(5);
  const [game, setGame] = useState(null);
  const [moveInput, setMoveInput] = useState("");
  const [lastExchange, setLastExchange] = useState(null);
  const [selectedSquare, setSelectedSquare] = useState("");
  const [targetSquares, setTargetSquares] = useState([]);
  const [recommendation, setRecommendation] = useState(null);
  const [pgn, setPgn] = useState("");
  const [pgnCopied, setPgnCopied] = useState(false);
  const [boardPerspective, setBoardPerspective] = useState("white");
  const [pendingPromotion, setPendingPromotion] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const legalMoves = game?.legal_moves || [];

  const canPlayMove = useMemo(() => {
    if (!game) {
      return false;
    }

    return game.status === "active" && game.turn === playerColor;
  }, [game, playerColor]);

  function clearSelection() {
    setSelectedSquare("");
    setTargetSquares([]);
  }

  async function refreshGameState(gameId) {
    const gameStateResponse = await fetch(apiUrl(`/api/games/${gameId}`));
    const gameStatePayload = await parseJsonPayload(gameStateResponse);
    if (!gameStateResponse.ok) {
      throw new Error(pickApiErrorMessage(gameStateResponse, gameStatePayload, "Failed to refresh game"));
    }
    if (!gameStatePayload) {
      throw new Error("Server returned an empty game state response.");
    }

    setGame(gameStatePayload);
  }

  async function startGame() {
    setLoading(true);
    setError("");
    setLastExchange(null);
    setMoveInput("");
    setRecommendation(null);
    setPgn("");
    setPgnCopied(false);
    setBoardPerspective(playerColor);
    setPendingPromotion(null);
    clearSelection();

    try {
      const response = await fetch(apiUrl("/api/games"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          player_color: playerColor,
          bot_mode: botMode,
          bot_level: Number(botLevel)
        })
      });

      const payload = await parseJsonPayload(response);
      if (!response.ok) {
        throw new Error(pickApiErrorMessage(response, payload, "Failed to create game"));
      }
      if (!payload) {
        throw new Error("Server returned an empty response when creating a game.");
      }

      setGame(payload);
    } catch (err) {
      setError(normalizeRequestError(err, "Failed to create game"));
    } finally {
      setLoading(false);
    }
  }

  async function submitMove(overrideMove) {
    const rawMove = typeof overrideMove === "string" ? overrideMove : moveInput;
    const uciMove = rawMove.trim();
    if (!game || !uciMove) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(apiUrl(`/api/games/${game.game_id}/move`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uci: uciMove })
      });

      const payload = await parseJsonPayload(response);
      if (!response.ok) {
        throw new Error(pickApiErrorMessage(response, payload, "Failed to play move"));
      }
      if (!payload) {
        throw new Error("Server returned an empty move response.");
      }

      setLastExchange(payload);
      setMoveInput("");
      setPendingPromotion(null);
      clearSelection();
      await refreshGameState(game.game_id);
    } catch (err) {
      setError(normalizeRequestError(err, "Failed to play move"));
    } finally {
      setLoading(false);
    }
  }

  function handleSquareClick(squareName) {
    if (!canPlayMove || loading || !game) {
      return;
    }

    setError("");

    if (!selectedSquare) {
      const targets = legalTargetsForSquare(legalMoves, squareName);
      if (targets.length === 0) {
        return;
      }

      setSelectedSquare(squareName);
      setTargetSquares(targets);
      return;
    }

    if (squareName === selectedSquare) {
      clearSelection();
      return;
    }

    const selectedMove = composeMoveFromSelection(legalMoves, selectedSquare, squareName);
    if (selectedMove) {
      setMoveInput(selectedMove);
      submitMove(selectedMove);
      return;
    }

    const promotionOptions = promotionOptionsForMove(legalMoves, selectedSquare, squareName);
    if (promotionOptions.length > 0) {
      setPendingPromotion({ from: selectedSquare, to: squareName, options: promotionOptions });
      return;
    }

    const reselectedTargets = legalTargetsForSquare(legalMoves, squareName);
    if (reselectedTargets.length > 0) {
      setSelectedSquare(squareName);
      setTargetSquares(reselectedTargets);
      return;
    }

    setError("That square is not a legal destination.");
  }

  function choosePromotion(piece) {
    if (!pendingPromotion) {
      return;
    }
    const move = `${pendingPromotion.from}${pendingPromotion.to}${piece}`;
    setMoveInput(move);
    submitMove(move);
  }

  async function fetchRecommendation() {
    if (!game) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(apiUrl(`/api/games/${game.game_id}/recommendation`));
      const payload = await parseJsonPayload(response);
      if (!response.ok) {
        throw new Error(pickApiErrorMessage(response, payload, "Failed to fetch recommendation"));
      }
      if (!payload) {
        throw new Error("Server returned an empty recommendation response.");
      }

      setRecommendation(payload);
      if (payload.recommended_move) {
        setMoveInput(payload.recommended_move);
      }
    } catch (err) {
      setError(normalizeRequestError(err, "Failed to fetch recommendation"));
    } finally {
      setLoading(false);
    }
  }

  async function fetchPgn() {
    if (!game) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(apiUrl(`/api/games/${game.game_id}/pgn`));
      const payload = await parseJsonPayload(response);
      if (!response.ok) {
        throw new Error(pickApiErrorMessage(response, payload, "Failed to fetch PGN"));
      }
      if (!payload) {
        throw new Error("Server returned an empty PGN response.");
      }

      setPgn(payload.pgn || "");
      setPgnCopied(false);
    } catch (err) {
      setError(normalizeRequestError(err, "Failed to fetch PGN"));
    } finally {
      setLoading(false);
    }
  }

  async function copyPgn() {
    if (!pgn) {
      return;
    }

    try {
      await navigator.clipboard.writeText(pgn);
      setPgnCopied(true);
    } catch {
      setError("Could not copy PGN. Your browser may block clipboard access.");
    }
  }

  const moveRows = buildMoveRows(game?.moves || []);
  const sanRows = buildMoveRows(game?.san_moves || []);
  const captures = buildCapturedPieces(game?.fen || "");
  const whiteCaptureSummary = captureSummary(captures.capturedByWhite);
  const blackCaptureSummary = captureSummary(captures.capturedByBlack);
  const whiteCaptureScore = captureScore(captures.capturedByWhite);
  const blackCaptureScore = captureScore(captures.capturedByBlack);
  const materialDelta = whiteCaptureScore - blackCaptureScore;
  const materialState = materialDelta === 0
    ? "Material equal"
    : materialDelta > 0
      ? `White +${materialDelta}`
      : `Black +${Math.abs(materialDelta)}`;
  const headline = statusHeadline(game);
  const gameFinished = game?.status === "finished";
  const endgameClassName = gameFinished
    ? game?.winner
      ? "winner"
      : "draw"
    : "";
  const endgameMessage = gameFinished
    ? game?.winner
      ? `${capitalize(game.winner)} wins`
      : "Draw"
    : "";
  const opponentLastMove = opponentLastMoveMetadata(game?.moves || [], game?.san_moves || [], playerColor);
  const selectedSquareHint = selectedSquare ? `Selected: ${selectedSquare} (${targetSquares.length} legal target${targetSquares.length === 1 ? "" : "s"})` : "Click a piece to view legal targets";

  return (
    <main className="page">
      <section className="panel">
        <h1>Chess Bot Arena</h1>
        <p>Realistic play mode with SAN notation, promotion picker, and opponent-move tracking.</p>

        <div className="controls">
          <label>
            Your color
            <select value={playerColor} onChange={(event) => setPlayerColor(event.target.value)}>
              <option value="white">White</option>
              <option value="black">Black</option>
            </select>
          </label>

          <label>
            Bot mode
            <select value={botMode} onChange={(event) => setBotMode(event.target.value)}>
              <option value="engine">Engine Bot</option>
              <option value="ml">ML Bot</option>
            </select>
          </label>

          <label>
            Bot level
            <input
              type="number"
              min={0}
              max={20}
              value={botLevel}
              onChange={(event) => setBotLevel(event.target.value)}
            />
          </label>

          <p className="bot-help">
            Bot level controls engine strength (0-20). Engine Bot always uses this level. ML Bot first tries the ML model, then falls back to engine/random using this level when needed.
          </p>

          <button onClick={startGame} disabled={loading}>
            {loading ? "Starting..." : "Start New Game"}
          </button>

          <button
            type="button"
            onClick={() => setBoardPerspective((current) => (current === "white" ? "black" : "white"))}
          >
            Flip Board
          </button>
        </div>

        {game && (
          <div className="status">
            <p>Game ID: {game.game_id}</p>
            <p>Status: {game.status}</p>
            <p>Result: {game.result || "-"}</p>
            <p>Turn: {game.turn}</p>
            <p>Bot mode: {game.bot_mode}</p>
            <p>Termination: {game.termination || "-"}</p>
            <p>Winner: {game.winner || "-"}</p>
          </div>
        )}

        <p className="headline">{headline}</p>

        <div className="meta-strip">
          <span className="meta-chip">Perspective: {boardPerspective}</span>
          <span className="meta-chip">Opponent Last: {opponentLastMove.san || "-"}</span>
          <span className="meta-chip">Hint: {selectedSquareHint}</span>
        </div>

        <div className="move-box">
          <input
            type="text"
            placeholder="e2e4"
            value={moveInput}
            onChange={(event) => setMoveInput(event.target.value)}
            disabled={!canPlayMove || loading}
          />
          <button onClick={submitMove} disabled={!canPlayMove || loading}>
            Play Move
          </button>
          <button onClick={fetchRecommendation} disabled={!game || loading}>
            Recommend Move
          </button>
          <button onClick={fetchPgn} disabled={!game || loading}>
            Load PGN
          </button>
          <button onClick={copyPgn} disabled={!pgn}>
            {pgnCopied ? "PGN Copied" : "Copy PGN"}
          </button>
        </div>

        {pendingPromotion && (
          <div className="promotion-box">
            <p>
              Choose promotion for {pendingPromotion.from} to {pendingPromotion.to}
            </p>
            <div className="promotion-actions">
              {pendingPromotion.options.map((option) => (
                <button key={option} type="button" onClick={() => choosePromotion(option)}>
                  {option.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        )}

        {sanRows.length > 0 && (
          <section className="history">
            <h2>Move History (SAN)</h2>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>White</th>
                  <th>Black</th>
                </tr>
              </thead>
              <tbody>
                {sanRows.map((row) => (
                  <tr key={row.number}>
                    <td>{row.number}</td>
                    <td>{row.white}</td>
                    <td>{row.black || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {pgn && (
          <section className="pgn-box">
            <h2>PGN</h2>
            <textarea readOnly value={pgn} rows={8} />
          </section>
        )}

        {moveRows.length > 0 && (
          <section className="history">
            <h2>Move History (UCI)</h2>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>White</th>
                  <th>Black</th>
                </tr>
              </thead>
              <tbody>
                {moveRows.map((row) => (
                  <tr key={`uci-${row.number}`}>
                    <td>{row.number}</td>
                    <td>{row.white}</td>
                    <td>{row.black || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {lastExchange && (
          <p className="exchange-line">
            You: {lastExchange.player_move} | Bot: {lastExchange.bot_move || "-"} ({lastExchange.bot_source || "-"})
          </p>
        )}

        {recommendation && (
          <p>
            Recommendation: {recommendation.recommended_move || "-"} from {recommendation.source}
            {recommendation.confidence != null ? ` (${(recommendation.confidence * 100).toFixed(1)}%)` : ""}
          </p>
        )}

        {error && <p className="error">{error}</p>}
      </section>

      <section className="board-wrap">
        <div className="board-shell">
          <aside className="graveyard-panel">
            <h3>White Captures</h3>
            <p className="capture-score">+{whiteCaptureScore}</p>
            <div className="captured-pieces-grid">
              {whiteCaptureSummary.length === 0 && <p className="capture-empty">No captures yet</p>}
              {whiteCaptureSummary.map((item) => (
                <div key={`white-${item.piece}`} className="capture-card">
                  <span className="capture-piece">{item.symbol}</span>
                  <span className="capture-detail">x{item.count}</span>
                  <span className="capture-detail">{item.points} pts</span>
                </div>
              ))}
            </div>
          </aside>

          <div className="board-stack">
            <div className="board-info">
              <span>Turn: {game?.turn || "-"}</span>
              <span>In Check: {game?.is_check ? "Yes" : "No"}</span>
              <span>Last SAN: {game?.last_move_san || "-"}</span>
              <span>{materialState}</span>
            </div>

            <div className={["board-stage", gameFinished ? "is-finished" : "", endgameClassName].filter(Boolean).join(" ")}>
              <ChessBoard
                fen={game?.fen || ""}
                selectedSquare={selectedSquare}
                targetSquares={targetSquares}
                lastMove={opponentLastMove.uci}
                checkedKingSquare={game?.checked_king_square || null}
                perspective={boardPerspective}
                onSquareClick={handleSquareClick}
              />
              {gameFinished && <div className="endgame-banner">{endgameMessage}</div>}
            </div>
          </div>

          <aside className="graveyard-panel">
            <h3>Black Captures</h3>
            <p className="capture-score">+{blackCaptureScore}</p>
            <div className="captured-pieces-grid">
              {blackCaptureSummary.length === 0 && <p className="capture-empty">No captures yet</p>}
              {blackCaptureSummary.map((item) => (
                <div key={`black-${item.piece}`} className="capture-card">
                  <span className="capture-piece">{item.symbol}</span>
                  <span className="capture-detail">x{item.count}</span>
                  <span className="capture-detail">{item.points} pts</span>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
