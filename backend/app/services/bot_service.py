import shutil
from pathlib import Path

import chess

try:
    import joblib
except ImportError:
    joblib = None

try:
    from stockfish import Stockfish
except ImportError:
    Stockfish = None


class BotService:
    _MAX_API_LEVEL = 50
    _MAX_ENGINE_SKILL = 20

    def __init__(
        self,
        engine_path: str | None = None,
        model_path: str | None = None,
        ml_confidence_threshold: float = 0.0,
    ) -> None:
        self._engine_path = engine_path
        self._model_path = model_path
        self._ml_confidence_threshold = ml_confidence_threshold
        self._engine = None
        self._ml_model = None
        self._init_engine()
        self._init_ml_model()

    def _init_engine(self) -> None:
        if Stockfish is None:
            return

        engine_path = self._engine_path
        if engine_path:
            if not Path(engine_path).exists():
                return
        else:
            discovered_path = shutil.which("stockfish")
            if discovered_path is None:
                return
            engine_path = discovered_path

        try:
            self._engine = Stockfish(path=engine_path)
        except Exception:
            self._engine = None
            return

    def _init_ml_model(self) -> None:
        if joblib is None or not self._model_path:
            return

        model_path = Path(self._model_path)
        if not model_path.exists():
            return

        try:
            self._ml_model = joblib.load(model_path)
        except Exception:
            self._ml_model = None

    @staticmethod
    def _board_to_features(board: chess.Board) -> list[int]:
        features: list[int] = []
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                features.append(0)
            else:
                value = piece.piece_type
                features.append(value if piece.color == chess.WHITE else -value)

        features.append(1 if board.turn == chess.WHITE else -1)
        return features

    @classmethod
    def _normalize_level(cls, level: int) -> int:
        return max(0, min(level, cls._MAX_API_LEVEL))

    @staticmethod
    def _evaluate_board(board: chess.Board) -> int:
        if board.is_checkmate():
            return -100000
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
            return 0

        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
        }
        score = 0
        for piece_type, value in piece_values.items():
            score += len(board.pieces(piece_type, chess.WHITE)) * value
            score -= len(board.pieces(piece_type, chess.BLACK)) * value

        return score if board.turn == chess.WHITE else -score

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
    ) -> tuple[int, chess.Move | None]:
        if depth == 0 or board.is_game_over(claim_draw=True):
            return self._evaluate_board(board), None

        best_score = -1_000_000
        best_move: chess.Move | None = None
        ordered_moves = sorted(
            board.legal_moves,
            key=lambda move: (
                board.is_capture(move),
                board.gives_check(move),
                move.promotion is not None,
            ),
            reverse=True,
        )

        for move in ordered_moves:
            board.push(move)
            candidate_score, _ = self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()
            score = -candidate_score

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score, best_move

    def _choose_fallback_move(self, board: chess.Board, level: int) -> str | None:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        normalized_level = self._normalize_level(level)
        depth = min(3, 1 + normalized_level // 20)
        _, best_move = self._negamax(board, depth=depth, alpha=-1_000_000, beta=1_000_000)
        if best_move is None:
            return legal_moves[0].uci()
        return best_move.uci()

    def _choose_engine_move(self, board: chess.Board, level: int) -> tuple[str | None, str]:
        normalized_level = self._normalize_level(level)
        if self._engine is not None:
            try:
                self._engine.set_fen_position(board.fen())
                skill_level = round((normalized_level / self._MAX_API_LEVEL) * self._MAX_ENGINE_SKILL)
                self._engine.set_skill_level(skill_level)
                best_move = self._engine.get_best_move()
                if best_move:
                    return best_move, "engine"
            except Exception:
                pass

        fallback_move = self._choose_fallback_move(board, normalized_level)
        if fallback_move is None:
            return None, "none"

        return fallback_move, "heuristic"

    def _choose_ml_move(self, board: chess.Board) -> tuple[str | None, float | None]:
        if self._ml_model is None:
            return None, None

        legal_moves = {move.uci() for move in board.legal_moves}
        if not legal_moves:
            return None, None

        features = [self._board_to_features(board)]

        try:
            if hasattr(self._ml_model, "predict_proba") and hasattr(self._ml_model, "classes_"):
                probabilities = self._ml_model.predict_proba(features)[0]
                ranked_indices = sorted(range(len(probabilities)), key=lambda idx: probabilities[idx], reverse=True)
                classes = list(self._ml_model.classes_)

                for idx in ranked_indices:
                    candidate = str(classes[idx])
                    if candidate in legal_moves:
                        return candidate, float(probabilities[idx])

            prediction = str(self._ml_model.predict(features)[0])
            if prediction in legal_moves:
                return prediction, None
        except Exception:
            return None, None

        return None, None

    def recommend_move(self, board: chess.Board, level: int, mode: str) -> dict[str, str | float | None]:
        if board.is_game_over(claim_draw=True):
            return {"move": None, "source": "none", "confidence": None}

        if mode == "ml":
            move, confidence = self._choose_ml_move(board)
            if move is not None:
                if confidence is not None and confidence < self._ml_confidence_threshold:
                    fallback_move, fallback_source = self._choose_engine_move(board, level)
                    return {
                        "move": fallback_move,
                        "source": f"{fallback_source}-low-confidence",
                        "confidence": confidence,
                    }
                return {"move": move, "source": "ml", "confidence": confidence}

            fallback_move, fallback_source = self._choose_engine_move(board, level)
            return {"move": fallback_move, "source": fallback_source, "confidence": None}

        move, source = self._choose_engine_move(board, level)
        return {"move": move, "source": source, "confidence": None}

    def choose_move(self, board: chess.Board, level: int, mode: str) -> str | None:
        recommendation = self.recommend_move(board=board, level=level, mode=mode)
        move = recommendation.get("move")
        return str(move) if move is not None else None

    def health(self) -> dict[str, bool | float | str | None]:
        return {
            "engine_available": self._engine is not None,
            "ml_model_loaded": self._ml_model is not None,
            "ml_confidence_threshold": self._ml_confidence_threshold,
            "engine_path_configured": self._engine_path,
            "ml_model_path_configured": self._model_path,
        }
