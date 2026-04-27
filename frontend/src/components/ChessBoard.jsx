import React from "react";

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];

export const PIECE_MAP = {
  K: "\u2654",
  Q: "\u2655",
  R: "\u2656",
  B: "\u2657",
  N: "\u2658",
  P: "\u2659",
  k: "\u265A",
  q: "\u265B",
  r: "\u265C",
  b: "\u265D",
  n: "\u265E",
  p: "\u265F"
};

function fenBoardToMap(fen) {
  const boardPart = fen.split(" ")[0];
  const rows = boardPart.split("/");
  const squareToPiece = new Map();

  rows.forEach((row, rowIndex) => {
    const rank = 8 - rowIndex;
    let fileIndex = 0;
    for (const cell of row) {
      if (/\d/.test(cell)) {
        fileIndex += Number(cell);
      } else {
        const square = `${FILES[fileIndex]}${rank}`;
        squareToPiece.set(square, cell);
        fileIndex += 1;
      }
    }
  });

  return squareToPiece;
}

function buildDisplaySquares(perspective) {
  const rankOrder = perspective === "black" ? [1, 2, 3, 4, 5, 6, 7, 8] : [8, 7, 6, 5, 4, 3, 2, 1];
  const fileOrder = perspective === "black" ? [...FILES].reverse() : FILES;

  const squares = [];
  for (const rank of rankOrder) {
    for (const file of fileOrder) {
      squares.push(`${file}${rank}`);
    }
  }
  return squares;
}

function isDarkSquare(square) {
  const fileIndex = FILES.indexOf(square[0]);
  const rank = Number(square[1]);
  return (fileIndex + rank) % 2 === 1;
}

function isLastMoveSquare(square, lastMove) {
  if (!lastMove) {
    return false;
  }
  const fromSquare = lastMove.slice(0, 2);
  const toSquare = lastMove.slice(2, 4);
  return square === fromSquare || square === toSquare;
}

function coordinateLabels(square, displayIndex) {
  const row = Math.floor(displayIndex / 8);
  const col = displayIndex % 8;
  return {
    rank: col === 0 ? square[1] : null,
    file: row === 7 ? square[0] : null,
  };
}

function promotionPieceCode(option, pieceColor) {
  if (!option) {
    return "";
  }
  const normalized = option.toLowerCase();
  return pieceColor === "black" ? normalized : normalized.toUpperCase();
}

export function ChessBoard({
  fen,
  selectedSquare,
  targetSquares,
  lastMove,
  checkedKingSquare,
  perspective = "white",
  isTransitioning = false,
  promotionPicker = null,
  onSquareClick,
  onPromotionSelect,
  onPromotionCancel,
}) {
  const squareToPiece = fen ? fenBoardToMap(fen) : new Map();
  const displaySquares = buildDisplaySquares(perspective);
  const targetSet = new Set(targetSquares || []);

  return (
    <div className={["board", isTransitioning ? "is-transitioning" : ""].filter(Boolean).join(" ")} role="img" aria-label="Chess board">
      {displaySquares.map((squareName, index) => {
        const pieceCode = squareToPiece.get(squareName) || "";
        const isSelected = selectedSquare === squareName;
        const isTarget = targetSet.has(squareName);
        const isLastMove = isLastMoveSquare(squareName, lastMove);
        const isCheckedKing = checkedKingSquare === squareName;
        const hasPromotionPicker = promotionPicker && promotionPicker.square === squareName;
        const isPromotionFromSquare = promotionPicker && promotionPicker.selectedOption && promotionPicker.fromSquare === squareName;
        const isPromotionPreviewSquare = hasPromotionPicker && promotionPicker.selectedOption;
        const previewPieceCode = isPromotionPreviewSquare
          ? promotionPieceCode(promotionPicker.selectedOption, promotionPicker.pieceColor)
          : "";
        const displayPieceCode = isPromotionFromSquare ? "" : previewPieceCode || pieceCode;
        const piece = displayPieceCode ? PIECE_MAP[displayPieceCode] || "" : "";
        const pieceTone = displayPieceCode && displayPieceCode === displayPieceCode.toUpperCase() ? "white-piece" : "black-piece";
        const labels = coordinateLabels(squareName, index);

        const className = [
          "square",
          isDarkSquare(squareName) ? "dark" : "light",
          isSelected ? "selected" : "",
          isTarget ? "target" : "",
          isLastMove ? "last-move" : "",
          isCheckedKing ? "checked" : "",
        ]
          .filter(Boolean)
          .join(" ");

        return (
          <div key={squareName} className="square-cell">
            <button
              type="button"
              className={className}
              onClick={() => onSquareClick?.(squareName)}
              aria-label={`Square ${squareName}`}
            >
              {isTarget && <span className="target-dot" aria-hidden="true" />}
              <span className={["piece-symbol", pieceTone].filter(Boolean).join(" ")}>{piece}</span>
              {labels.rank && <small className="rank-label">{labels.rank}</small>}
              {labels.file && <small className="file-label">{labels.file}</small>}
            </button>
            {hasPromotionPicker && !promotionPicker.selectedOption && (
              <div className="promotion-picker" role="group" aria-label={`Choose promotion piece on ${squareName}`}>
                {promotionPicker.options.map((option, optionIndex) => {
                  const optionCode = promotionPieceCode(option, promotionPicker.pieceColor);
                  const optionSymbol = PIECE_MAP[optionCode] || option.toUpperCase();
                  const optionTone = optionCode === optionCode.toUpperCase() ? "white-piece" : "black-piece";
                  return (
                    <button
                      key={option}
                      type="button"
                      className="promotion-option"
                      aria-label={`Promote to ${option.toUpperCase()}`}
                      autoFocus={optionIndex === 0}
                      onKeyDown={(event) => {
                        if (event.key === "Escape") {
                          event.preventDefault();
                          onPromotionCancel?.();
                        }
                      }}
                      onClick={() => onPromotionSelect?.(option)}
                    >
                      <span className={["piece-symbol", optionTone].filter(Boolean).join(" ")}>{optionSymbol}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
