from __future__ import annotations

from pathlib import Path

import chess
import chess.pgn
import pandas as pd


MAX_PLIES = 60


def fen_to_features(fen: str) -> list[int]:
    board = chess.Board(fen)
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


def build_examples(pgn_path: Path, max_games: int = 200) -> pd.DataFrame:
    rows: list[dict] = []

    with pgn_path.open("r", encoding="utf-8", errors="ignore") as handle:
        game_count = 0
        while game_count < max_games:
            game = chess.pgn.read_game(handle)
            if game is None:
                break

            board = game.board()
            ply = 0
            for move in game.mainline_moves():
                if ply >= MAX_PLIES:
                    break

                rows.append(
                    {
                        "fen": board.fen(),
                        "move": move.uci(),
                        "turn": "white" if board.turn else "black",
                    }
                )
                board.push(move)
                ply += 1

            game_count += 1

    if not rows:
        return pd.DataFrame(columns=["fen", "move", "turn"])

    frame = pd.DataFrame(rows)
    feature_frame = pd.DataFrame(frame["fen"].map(fen_to_features).tolist())
    feature_frame.columns = [f"sq_{idx}" for idx in range(feature_frame.shape[1])]

    return pd.concat([frame, feature_frame], axis=1)


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent
    input_path = data_dir / "sample_games.pgn"
    output_path = data_dir / "training_examples.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            "Expected sample PGN at ml/data/sample_games.pgn. "
            "Add a small PGN file first, then rerun preprocessing."
        )

    dataset = build_examples(input_path)
    dataset.to_csv(output_path, index=False)
    print(f"Saved {len(dataset)} examples to {output_path}")
