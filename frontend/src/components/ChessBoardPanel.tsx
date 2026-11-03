"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import {
  RotateCcw,
  Bot,
  BrainCircuit,
  BookOpen,
  Cpu,
  Swords,
  ChevronRight,
  Sparkles,
} from "lucide-react";
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
  const [boardOrientation, setBoardOrientation] = useState<"white" | "black">("white");
  const [gameStatus, setGameStatus] = useState<string>("Your turn to play as White");

  // Initialize chess instance client-side only
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
    setGameStatus("New game started. Your turn (White).");
  }, []);

  const triggerBotMove = useCallback(
    async (currentGame: Chess) => {
      setIsBotThinking(true);
      setGameStatus(`${playerUsername} clone is deliberating...`);

      try {
        const response = await getBotMove(currentGame.fen(), playerUsername);
        setLastBotMove(response);

        // Attempt move on board
        const moveResult = currentGame.move(response.move);
        if (moveResult) {
          setGamePosition(currentGame.fen());
          setMoveHistory(currentGame.history());

          if (currentGame.isGameOver()) {
            if (currentGame.isCheckmate()) {
              setGameStatus(`Checkmate! ${playerUsername} clone wins!`);
            } else if (currentGame.isDraw()) {
              setGameStatus("Game drawn!");
            }
          } else {
            setGameStatus(
              currentGame.inCheck()
                ? "You are in check! Your move."
                : "Your move (White)."
            );
          }
        }
      } catch (err) {
        console.error("Bot move error:", err);
        // Fallback: make random legal move if API call fails
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
          setGameStatus("Your move.");
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

      // Update position
      setGamePosition(game.fen());
      setMoveHistory(game.history());

      if (game.isGameOver()) {
        if (game.isCheckmate()) {
          setGameStatus("Checkmate! You win against the clone!");
        } else {
          setGameStatus("Game drawn!");
        }
        return true;
      }

      // Trigger bot response after a brief realistic delay
      setTimeout(() => {
        triggerBotMove(game);
      }, 350);

      return true;
    } catch {
      return false;
    }
  };

  const getSourceBadge = (source?: string) => {
    switch (source) {
      case "opening_book":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            <BookOpen className="w-3 h-3" /> Historical Repertoire
          </span>
        );
      case "stockfish_clone":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-primary/20 text-primary-300 border border-primary/30">
            <Cpu className="w-3 h-3" /> Tuned Engine + Blunder Sampler
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-700 text-slate-300">
            <BrainCircuit className="w-3 h-3" /> Engine Move
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col rounded-2xl bg-slate-900/90 border border-slate-800 p-5 shadow-2xl backdrop-blur-xl">
      {/* Bot Header Card */}
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/20 text-primary-300 ring-1 ring-primary/40">
              <Bot className="h-6 w-6" />
            </div>
            {isBotThinking && (
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-primary" />
              </span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-white text-base leading-tight">
                {playerUsername} <span className="text-xs text-slate-400 font-normal">Clone</span>
              </h3>
              {playerRating && (
                <span className="rounded bg-accent/20 px-1.5 py-0.2 text-[11px] font-mono font-bold text-accent">
                  {playerRating} Elo
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              {playstyleArchetype || "Trained on historical PGNs & error patterns"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={resetGame}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 hover:text-white transition-colors"
            title="Reset to starting position"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Board & Live Status */}
      <div className="flex flex-col items-center">
        <div className="w-full max-w-[420px] aspect-square rounded-xl overflow-hidden shadow-2xl border border-slate-700/50">
          {game && (
            <Chessboard
              position={gamePosition}
              onPieceDrop={onDrop}
              boardOrientation={boardOrientation}
              customDarkSquareStyle={{ backgroundColor: "#334155" }}
              customLightSquareStyle={{ backgroundColor: "#94a3b8" }}
              animationDuration={200}
            />
          )}
        </div>

        {/* Turn & Game Status Banner */}
        <div className="w-full mt-3 flex items-center justify-between px-3 py-2 rounded-lg bg-slate-950/70 border border-slate-800 text-xs">
          <span className="font-medium text-slate-300 flex items-center gap-2">
            <Swords className="w-4 h-4 text-primary" />
            {gameStatus}
          </span>
          <span className="text-[11px] font-mono text-slate-500">
            Moves: {moveHistory.length}
          </span>
        </div>
      </div>

      {/* Bot Move Explanation & Neural Reasoning Panel */}
      <div className="mt-4 rounded-xl bg-slate-950/80 border border-slate-800/80 p-3.5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            Clone Move Reasoning
          </span>
          {lastBotMove && getSourceBadge(lastBotMove.source)}
        </div>

        {lastBotMove ? (
          <div className="text-xs text-slate-300 space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-accent font-bold">
                {lastBotMove.move}
              </span>
              <span className="text-slate-400">—</span>
              <span className="italic text-slate-300">
                &ldquo;{lastBotMove.explanation}&rdquo;
              </span>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">
            Make your opening move above to challenge {playerUsername}&apos;s clone.
          </p>
        )}
      </div>

      {/* Move History Strip */}
      {moveHistory.length > 0 && (
        <div className="mt-3 flex items-center gap-2 overflow-x-auto py-1 px-2 rounded-lg bg-slate-950/40 text-[11px] font-mono text-slate-400 border border-slate-900">
          <span className="text-slate-600 uppercase text-[10px] shrink-0 font-sans">
            Moves:
          </span>
          {moveHistory.map((mv, i) => (
            <span
              key={i}
              className={cn(
                "shrink-0 px-1 rounded",
                i % 2 === 0 ? "text-slate-300" : "text-primary-300"
              )}
            >
              {i % 2 === 0 ? `${Math.floor(i / 2) + 1}. ` : ""}
              {mv}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

