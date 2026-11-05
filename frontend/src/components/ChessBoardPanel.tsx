"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import { RotateCcw } from "lucide-react";
import { getBotMove } from "@/lib/api";
import { BotMoveResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ChessBoardPanelProps {
  playerUsername: string;
  playerRating?: number;
  playstyleArchetype?: string;
}

export default function ChessBoardPanel({
  playerUsername,
  playerRating,
  playstyleArchetype,
}: ChessBoardPanelProps) {
  const [game, setGame] = useState<Chess | null>(null);
  const [gamePosition, setGamePosition] = useState<string>("start");
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [isBotThinking, setIsBotThinking] = useState(false);
  const [lastBotMove, setLastBotMove] = useState<BotMoveResponse | null>(null);
  const [boardOrientation] = useState<"white" | "black">("white");
  const [gameStatus, setGameStatus] = useState<string>("YOUR TURN · WHITE");

  useEffect(() => {
    const newGame = new Chess();
    setGame(newGame);
    setGamePosition(newGame.fen());
  }, []);

  const resetGame = useCallback(() => {
    const newGame = new Chess();
    setGame(newGame);
    setGamePosition(newGame.fen());
    setMoveHistory([]);
    setLastBotMove(null);
    setGameStatus("NEW GAME · YOUR TURN · WHITE");
  }, []);

  const triggerBotMove = useCallback(
    async (currentGame: Chess) => {
      setIsBotThinking(true);
      setGameStatus("CLONE CALCULATING…");

      try {
        const response = await getBotMove(currentGame.fen(), playerUsername);
        setLastBotMove(response);

        const moveResult = currentGame.move(response.move);
        if (moveResult) {
          setGamePosition(currentGame.fen());
          setMoveHistory(currentGame.history());

          if (currentGame.isGameOver()) {
            if (currentGame.isCheckmate()) {
              setGameStatus(`CHECKMATE · CLONE WINS`);
            } else if (currentGame.isDraw()) {
              setGameStatus("GAME DRAWN");
            }
          } else {
            setGameStatus(
              currentGame.inCheck() ? "CHECK · YOUR MOVE" : "YOUR TURN · WHITE"
            );
          }
        }
      } catch (err) {
        console.error("Bot move error:", err);
        const legalMoves = currentGame.moves();
        if (legalMoves.length > 0) {
          const randomMove = legalMoves[Math.floor(Math.random() * legalMoves.length)];
          currentGame.move(randomMove);
          setGamePosition(currentGame.fen());
          setMoveHistory(currentGame.history());
          setLastBotMove({
            move: randomMove,
            fen_after: currentGame.fen(),
            explanation: "Fallback tactical counter-move.",
            source: "stockfish_clone",
            evaluation: 0.0,
          });
          setGameStatus("YOUR MOVE");
        }
      } finally {
        setIsBotThinking(false);
      }
    },
    [playerUsername]
  );

  const onDrop = (sourceSquare: string, targetSquare: string): boolean => {
    if (!game || isBotThinking || game.isGameOver()) return false;

    try {
      const move = game.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: "q",
      });

      if (move === null) return false;

      setGamePosition(game.fen());
      setMoveHistory(game.history());

      if (game.isGameOver()) {
        if (game.isCheckmate()) {
          setGameStatus("CHECKMATE · YOU WIN");
        } else {
          setGameStatus("GAME DRAWN");
        }
        return true;
      }

      setTimeout(() => {
        triggerBotMove(game);
      }, 350);

      return true;
    } catch {
      return false;
    }
  };

  const sourceLabel = (source?: string) => {
    if (source === "opening_book") return "BOOK";
    if (source === "stockfish_clone") return "ENGINE+NOISE";
    return "ENGINE";
  };

  return (
    <div className="border border-term-line bg-term-panel">
      <div className="panel-bar flex items-center justify-between px-3 py-2 font-mono text-[10px] tracking-wider">
        <div className="flex items-center gap-2 text-term-muted">
          <span className="text-term-green">▸</span>
          <span>CLONE CONSOLE</span>
        </div>
        <button
          onClick={resetGame}
          className="flex items-center gap-1.5 text-term-faint transition-colors hover:text-term-text"
          title="Reset to starting position"
        >
          <RotateCcw className="h-3 w-3" />
          RESET
        </button>
      </div>

      <div className="border-b border-term-line px-3 py-2.5">
        <div className="flex items-baseline justify-between gap-3 font-mono">
          <div>
            <div className="text-[12px] text-term-text">{playerUsername}</div>
            <div className="mt-0.5 text-[9px] tracking-wider text-term-faint">
              {playstyleArchetype ? playstyleArchetype.toUpperCase() : "CLONE"}
              {playerRating ? ` · ${playerRating} ELO` : ""}
            </div>
          </div>
          <span
            className={cn(
              "flex items-center gap-1.5 text-[9px] tracking-wider",
              isBotThinking ? "text-term-amber" : "text-term-green"
            )}
          >
            <span
              className={cn(
                "h-1 w-1",
                isBotThinking ? "bg-term-amber" : "bg-term-green"
              )}
              aria-hidden
            />
            {isBotThinking ? "BUSY" : "READY"}
          </span>
        </div>
      </div>

      <div className="p-3">
        <div className="border border-term-line p-1.5">
          <div className="aspect-square w-full overflow-hidden">
            {game && (
              <Chessboard
                position={gamePosition}
                onPieceDrop={onDrop}
                boardOrientation={boardOrientation}
                customDarkSquareStyle={{ backgroundColor: "#26312C" }}
                customLightSquareStyle={{ backgroundColor: "#C6CEC5" }}
                animationDuration={200}
              />
            )}
          </div>
        </div>

        <div className="mt-2 flex items-center justify-between border border-term-line bg-term-raised px-2 py-1.5 font-mono text-[9px] tracking-wider">
          <span className="text-term-muted">{gameStatus}</span>
          <span className="text-term-faint">{moveHistory.length} PLIES</span>
        </div>
      </div>

      <div className="border-t border-term-line p-3">
        <div className="flex items-center justify-between font-mono text-[9px] tracking-wider">
          <span className="text-term-faint">CLONE_REASONING</span>
          {lastBotMove && (
            <span className="text-term-green">{sourceLabel(lastBotMove.source)}</span>
          )}
        </div>

        {lastBotMove ? (
          <p className="mt-2 text-[12px] leading-5 text-term-muted">
            <span className="font-mono text-[11px] text-term-green">
              {lastBotMove.move}
            </span>
            <span className="mx-2 text-term-faint">→</span>
            <span className="italic">&ldquo;{lastBotMove.explanation}&rdquo;</span>
          </p>
        ) : (
          <p className="mt-2 font-mono text-[10px] leading-5 text-term-faint">
            // make an opening move to init the clone
          </p>
        )}
      </div>

      {moveHistory.length > 0 && (
        <div className="border-t border-term-line p-3">
          <div className="flex flex-wrap gap-x-2 gap-y-1 font-mono text-[10px] leading-4">
            {moveHistory.map((move, index) => (
              <span
                key={index}
                className={cn(
                  index % 2 === 0 ? "text-term-muted" : "text-term-green"
                )}
              >
                {index % 2 === 0 ? `${Math.floor(index / 2) + 1}.` : ""}
                {move}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
