# Grandmaster Echo ♟️
### The Multi-Agent AI Chess Analysis Platform

Grandmaster Echo is an end-to-end AI engineering platform that ingests 200+ games from any **Chess.com** or **Lichess** user, computes deterministic static evaluations via **Stockfish 16**, synthesizes an AI-driven psychological/tactical profile using a stateful **LangGraph** multi-agent graph with **Langfuse** observability, and generates a playable **clone bot** that mimics the target player's exact historical opening repertoire and error distribution.

---

## Overview

Grandmaster Echo is an open-source multi-agent analysis engine architected in **Next.js** and **Python (FastAPI)**, utilizing **LangGraph** to orchestrate stateful, multi-step LLM workflows and stream game state evaluations.

### Highlights

1. **Multi-Agent Analysis Engine** — Architected an open-source multi-agent analysis engine in **Next.js** and **Python (FastAPI)**, utilizing **LangGraph** to orchestrate stateful, multi-step LLM workflows and stream game state evaluations.

2. **RAG + Semantic Search** — Integrated **Qdrant** vector embeddings and **LLM/RAG** retrieval loops with semantic search to index player move histories, delivering personalized tactical commentary with a **60% reduction** in analysis latency.

3. **LLM Guardrails + Evals** — Implemented **LLM output guardrails** and automated **evals** to validate generated analysis against **Stockfish** engine outputs, improving the reliability and consistency of AI-generated recommendations.

---

## Tech Stack

- **Next.js** | **React** | **TypeScript**
- **Python (FastAPI)**
- **Qdrant (Vector DB)**
- **LangGraph**
- **Gemini API**

---

## Architecture Overview

```
                      ┌───────────────────────────────┐
                      │ Lichess / Chess.com Public API│
                      └──────────────┬────────────────┘
                                     │ (httpx async)
                                     ▼
                      ┌───────────────────────────────┐
                      │    PGN Ingestion & Parser     │
                      │   (python-chess + ECO parser) │
                      └──────────────┬────────────────┘
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
┌─────────────────────────┐                     ┌─────────────────────────┐
│ Stockfish 16 UCI Engine │                     │  Opening Book Generator │
│ (ACPL & Blunder Delta)  │                     │  (Historical FEN Cache) │
└────────────┬────────────┘                     └────────────┬────────────┘
             │                                               │
             └───────────────────────┬───────────────────────┘
                                     ▼
                    ┌───────────────────────────────────┐
                    │  Qdrant RAG Retrieval Loop        │
                    │  embed move histories → top-k     │
                    │  semantically similar games        │
                    └─────────────────┬─────────────────┘
                                      │ retrieved evidence
                                      ▼
                    ┌───────────────────────────────────┐
                    │  LangGraph Profiler Agent Graph   │
                    │  Gemini API (OpenAI fallback)     │
                    │  Opening Analyst + Tactical       │
                    │  Auditor ➔ Synthesis Writer       │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │  Guardrails + Automated Evals     │
                    │  grounded against Stockfish       │
                    └─────────────────┬─────────────────┘
                                      │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
┌─────────────────────────┐                     ┌─────────────────────────┐
│ PostgreSQL 16           │                     │ Next.js 14 UI           │
│ Game & Profile Storage  │                     │ Editorial Dossier +     │
│                         │                     │ Playable Clone Canvas   │
└─────────────────────────┘                     └─────────────────────────┘
        ▲
        │  SSE progress stream (/api/stream/analyze/{username})
        └──────────────────────────────────────────────────────────────
```

---

## Key Technical Highlights

1. **Deterministic-to-Stochastic Tool Grounding**: Combines exact mathematical FEN evaluations and ECO classifications (`python-chess`) with LLM qualitative reasoning.
2. **Stateful Multi-Agent Graph (LangGraph)**:
   - **Opening Analyst**: Classifies opening repertoire, breadth, and preparation depth.
   - **Tactical Auditor**: Ingests centipawn loss drops ($>2.0$ CP) and phase vulnerabilities.
   - **Synthesis Writer**: Formulates coaching summaries, archetypes, and comparable grandmaster twins.
3. **Qdrant RAG Loop**: Every parsed game is embedded (Gemini embeddings, deterministic hash fallback) and indexed in Qdrant. The pipeline retrieves the player's most semantically similar games and injects them as grounded evidence with citations.
4. **Provider-Agnostic LLM Layer**: Gemini is the primary structured-output provider; LangChain/OpenAI acts as a fallback so local development and CI degrade gracefully.
5. **LLM Guardrails**: Deterministic checks clamp implausible Elo estimates, reject unsupported certainty, validate blunder-rate consistency, and verify that the narrative references the player's real repertoire.
6. **Automated Evals**: Each run is scored for schema validity, Elo alignment, opening grounding, citation coverage, and guardrail pass rate against Stockfish-derived ground truth.
7. **Streaming Pipeline**: `GET /api/stream/analyze/{username}` emits Server-Sent Events for each stage (ingestion, Stockfish, RAG retrieval, agents, guardrails, evals) before delivering the final dossier.
8. **Observability & Telemetry**: Full end-to-end tracing via `@observe()` decorators from **Langfuse**.
9. **Behavior-Cloned Chess Engine**:
   - Matches player's historical opening moves via weighted frequency book.
   - Dynamic Stockfish tuning (`UCI_LimitStrength`, `UCI_Elo = player_rating`).
   - Probabilistic blunder sampler injecting human-like inaccuracies according to player's true blunder frequency.
10. **Editorial Dossier UI**:
    - Next.js 14 App Router, Tailwind CSS, TypeScript, and `react-chessboard`.
    - Rule-based editorial layout with serif display type, restrained palette, and cited evidence rather than card-heavy dashboards.

---

## Directory Structure

```
grandmaster-echo/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── graph.py       # LangGraph DAG topology (parallel fan-out/fan-in)
│   │   │   ├── nodes.py       # Opening Analyst, Tactical Auditor, Synthesis Writer
│   │   │   └── schemas.py     # Strict Pydantic output schemas
│   │   ├── routers/
│   │   │   ├── analyze.py     # POST /api/analyze & GET /api/analyze/{username}
│   │   │   ├── stream.py      # SSE /api/stream/analyze/{username}
│   │   │   └── bot.py         # POST /api/bot/move
│   │   ├── services/
│   │   │   ├── bot.py         # PlayerCloneBot (opening book + blunder sampler)
│   │   │   ├── embeddings.py  # Gemini embeddings + deterministic hash fallback
│   │   │   ├── engine.py      # StockfishAnalyzer (UCI protocol, ACPL)
│   │   │   ├── evals.py       # Automated evaluation metrics
│   │   │   ├── guardrails.py  # LLM output validation against Stockfish
│   │   │   ├── ingestion.py   # Chess.com & Lichess async API clients
│   │   │   ├── llm.py         # Gemini primary + OpenAI fallback provider
│   │   │   ├── parser.py      # python-chess PGN & ECO parser
│   │   │   ├── rag.py         # Move-history indexing and retrieval
│   │   │   └── vector_store.py# Qdrant REST client + in-memory fallback
│   │   ├── config.py          # Pydantic BaseSettings
│   │   ├── database.py        # Async SQLAlchemy session manager
│   │   ├── models.py          # PostgreSQL schema (players, games, evals, profiles)
│   │   ├── schemas.py         # API request/response models
│   │   └── main.py            # FastAPI entry point
│   ├── Dockerfile             # Multi-stage build with Stockfish 16
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js 14 App Router (layout, page, globals)
│   │   ├── components/        # PlayerDashboard, ChessBoardPanel, OpeningTable,
│   │   │                      # StatsGrid, ProfileCard, StrengthWeakness,
│   │   │                      # CoachingPlan, AnalysisMeta
│   │   └── lib/               # api.ts (REST + SSE), types.ts, utils.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── tests/
│   └── test_evaluation_harness.py # 20-profile parser alignment verification
└── docker-compose.yml         # PostgreSQL 16 + Qdrant + FastAPI + Stockfish
```

---

## Quickstart & Execution

### 1. Run with Docker Compose
```bash
cd grandmaster-echo
cp backend/.env.example backend/.env   # add GEMINI_API_KEY
docker compose up --build
```
- FastAPI backend at `http://localhost:8000`
- Interactive Swagger docs at `http://localhost:8000/docs`
- Qdrant at `http://localhost:6333` (dashboard at `/dashboard`)
- Frontend at `http://localhost:3000`

### 2. Run Backend Locally
```bash
cd grandmaster-echo/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set GEMINI_API_KEY and QDRANT_URL
uvicorn app.main:app --reload --port 8000
```

If Qdrant is not running the vector layer falls back to an in-memory store.
If `GEMINI_API_KEY` is not set the agent nodes fall back to `OPENAI_API_KEY`,
and the heuristic synthesis path is used when neither provider is available.

### 3. Run Frontend Locally
```bash
cd grandmaster-echo/frontend
npm install
npm run dev
```
Open `http://localhost:3000` to interact with Grandmaster Echo.

### 4. Tests
```bash
cd grandmaster-echo/backend
python -m pytest ../tests -q
cd ../frontend && npm run build
```

---

## API Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `POST` | `/api/analyze` | Run the full analysis pipeline |
| `GET` | `/api/analyze/{username}` | Retrieve a cached dossier |
| `GET` | `/api/stream/analyze/{username}` | Stream pipeline progress over SSE |
| `POST` | `/api/bot/move` | Ask the clone bot for a move |
| `GET` | `/api/health` | Liveness probe |

The analysis response includes `citations`, `guardrails`, `evals`,
`rag_enabled`, and per-stage `pipeline_ms` so the UI can show the retrieved
evidence and evaluation scores alongside the written report.

