import json
import uuid
from dataclasses import dataclass, field

import chess
import chess.pgn
from sqlalchemy.orm import sessionmaker

from app.models.db_models import GameRecord


@dataclass
class GameSession:
    game_id: str
    player_color: str
    bot_mode: str
    bot_level: int
    board: chess.Board = field(default_factory=chess.Board)
    moves: list[str] = field(default_factory=list)


class ChessService:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create_game(self, player_color: str, bot_mode: str, bot_level: int) -> GameSession:
        game_id = str(uuid.uuid4())
        session = GameSession(
            game_id=game_id,
            player_color=player_color,
            bot_mode=bot_mode,
            bot_level=bot_level,
        )

        record = GameRecord(
            game_id=session.game_id,
            player_color=session.player_color,
            bot_mode=session.bot_mode,
            bot_level=session.bot_level,
            fen=session.board.fen(),
            moves_json=json.dumps(session.moves),
        )

        with self._session_factory() as db:
            db.add(record)
            db.commit()

        return session

    def get_game(self, game_id: str) -> GameSession | None:
        with self._session_factory() as db:
            record = db.get(GameRecord, game_id)
            if record is None:
                return None
            return self._record_to_session(record)

    def _record_to_session(self, record: GameRecord) -> GameSession:
        moves = json.loads(record.moves_json) if record.moves_json else []
        board = chess.Board(record.fen)
        return GameSession(
            game_id=record.game_id,
            player_color=record.player_color,
            bot_mode=record.bot_mode,
            bot_level=record.bot_level,
            board=board,
            moves=moves,
        )

    def save_game(self, session: GameSession) -> None:
        with self._session_factory() as db:
            record = db.get(GameRecord, session.game_id)
            if record is None:
                raise ValueError("Game not found")

            record.player_color = session.player_color
            record.bot_mode = session.bot_mode
            record.bot_level = session.bot_level
            record.fen = session.board.fen()
            record.moves_json = json.dumps(session.moves)

            db.commit()

    def is_player_turn(self, session: GameSession) -> bool:
        player_is_white = session.player_color == "white"
        return session.board.turn == player_is_white

    def apply_move(self, session: GameSession, uci: str) -> None:
        try:
            move = chess.Move.from_uci(uci)
        except ValueError as exc:
            raise ValueError("Invalid UCI move format") from exc

        if move not in session.board.legal_moves:
            raise ValueError("Illegal move")

        session.board.push(move)
        session.moves.append(uci)
        self.save_game(session)

    def get_status(self, session: GameSession) -> tuple[str, str | None]:
        if not session.board.is_game_over(claim_draw=True):
            return "active", None

        outcome = session.board.outcome(claim_draw=True)
        result = outcome.result() if outcome else "1/2-1/2"
        return "finished", result

    def _build_san_moves(self, moves: list[str]) -> list[str]:
        board = chess.Board()
        san_moves: list[str] = []
        for uci in moves:
            move = chess.Move.from_uci(uci)
            if move not in board.legal_moves:
                break
            san_moves.append(board.san(move))
            board.push(move)
        return san_moves

    def _winner_from_outcome(self, outcome: chess.Outcome | None) -> str | None:
        if outcome is None or outcome.winner is None:
            return None
        return "white" if outcome.winner else "black"

    def _termination_label(self, session: GameSession) -> str | None:
        board = session.board
        if not board.is_game_over(claim_draw=True):
            return None
        if board.is_checkmate():
            return "checkmate"
        if board.is_stalemate():
            return "stalemate"
        if board.is_insufficient_material():
            return "insufficient_material"
        if board.can_claim_threefold_repetition():
            return "threefold_repetition"
        if board.can_claim_fifty_moves():
            return "fifty_move_rule"
        return "draw"

    def to_payload(self, session: GameSession) -> dict:
        status, result = self.get_status(session)
        turn = "white" if session.board.turn else "black"
        legal_moves = [move.uci() for move in session.board.legal_moves]
        bot_color = "black" if session.player_color == "white" else "white"
        san_moves = self._build_san_moves(session.moves)
        outcome = session.board.outcome(claim_draw=True)

        checked_king_square = None
        if session.board.is_check():
            king_square = session.board.king(session.board.turn)
            if king_square is not None:
                checked_king_square = chess.square_name(king_square)

        return {
            "game_id": session.game_id,
            "player_color": session.player_color,
            "bot_color": bot_color,
            "bot_mode": session.bot_mode,
            "bot_level": session.bot_level,
            "fen": session.board.fen(),
            "moves": session.moves,
            "san_moves": san_moves,
            "last_move": session.moves[-1] if session.moves else None,
            "last_move_san": san_moves[-1] if san_moves else None,
            "status": status,
            "result": result,
            "termination": self._termination_label(session),
            "winner": self._winner_from_outcome(outcome),
            "turn": turn,
            "is_check": session.board.is_check(),
            "is_checkmate": session.board.is_checkmate(),
            "is_stalemate": session.board.is_stalemate(),
            "checked_king_square": checked_king_square,
            "legal_moves": legal_moves,
        }

    def to_pgn(self, session: GameSession) -> str:
        game = chess.pgn.Game()
        node = game
        for uci in session.moves:
            node = node.add_variation(chess.Move.from_uci(uci))
        return str(game)
