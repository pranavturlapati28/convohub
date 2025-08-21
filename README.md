# ConvoHub — Branching Conversations (LLM-friendly)

A tiny, production-minded service for **threaded, branchable conversations** with **merge** and **diff** primitives — built to let you run multiple LLM "what-ifs", compare outcomes, and reconcile them back into a single storyline.

> Think: git for chats. Create a thread, branch it at any time, try different prompts/agents, then diff & merge the best bits back.

---

## Table of Contents

- [Concepts](#concepts)
- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Environment](#environment)
- [API Overview](#api-overview)
  - [Threads](#threads)
  - [Branches](#branches)
  - [Messages](#messages)
  - [Diff](#diff)
  - [Merge](#merge)
  - [Streaming (SSE/WebSocket)](#streaming-ssewebsocket)
- [Idempotency](#idempotency)
- [Pagination](#pagination)
- [Reference Scripts](#reference-scripts)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

---

## Concepts

- **Thread** — A container for a conversation.  
- **Branch** — A linear path of messages inside a thread. Branches can fork from other branches at any message.
- **Message** — `{role: "user"|"assistant"|"system", text: string, ...}` appended to a branch.
- **Diff** — A structural comparison between two branches.
- **Merge** — Combine two branches, honoring a strategy (e.g., "theirs", "ours", or a 3-way merge policy).

---

## Quick Start

### 1) Requirements
- Python 3.11+
- PostgreSQL 15+
- (Optional) Docker & Docker Compose
- `uvicorn` / `fastapi` (installed via `requirements.txt` / `pyproject.toml`)

### 2) Start Postgres (Docker)
```bash
docker-compose up -d  # starts postgres (and anything else defined)
```

> If you don't use Docker, ensure you have a local Postgres listening on `127.0.0.1:5432` and create the role/db below.

### 3) Create DB (first time)

```bash
psql -h 127.0.0.1 -U postgres -c "CREATE ROLE convo WITH LOGIN PASSWORD 'convo' SUPERUSER;"
psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE convohub OWNER convo;"
```

### 4) Configure environment

Create `.env`:

```ini
DATABASE_URL=postgresql+psycopg://convo:convo@127.0.0.1:5432/convohub
# Optional
APP_HOST=127.0.0.1
APP_PORT=8000
```

### 5) Run the API

```bash
# (create and activate venv, then)
pip install -r requirements.txt
uvicorn app.main:app --reload --host ${APP_HOST:-127.0.0.1} --port ${APP_PORT:-8000}
```

Open: `http://127.0.0.1:8000/docs` for Swagger.

---

## Local Development

Typical workflow:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)            # load env (mac/linux)
alembic upgrade head                          # if using migrations
uvicorn app.main:app --reload
```

---

## Environment

| Var            | Description            | Default     |
| -------------- | ---------------------- | ----------- |
| `DATABASE_URL` | SQLAlchemy/psycopg URL | required    |
| `APP_HOST`     | Bind host              | `127.0.0.1` |
| `APP_PORT`     | Bind port              | `8000`      |

---

## API Overview

**Base URL:** `http://127.0.0.1:8000/v1`

Headers to consider:

* `Content-Type: application/json`
* `Idempotency-Key: <uuid>` (for POSTs you may replay)

### Threads

#### Create a thread

```bash
curl -s -X POST http://127.0.0.1:8000/v1/threads \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demo"}'
```

**Response**

```json
{"id":"<thread_id>","title":"Demo","created_at":"..."}
```

#### Get a thread (and basic stats)

```bash
curl -s http://127.0.0.1:8000/v1/threads/<thread_id>
```

### Branches

#### Create a branch

```bash
curl -s -X POST http://127.0.0.1:8000/v1/threads/<thread_id>/branches \
  -H 'Content-Type: application/json' \
  -d '{"name":"main","fork_from_branch_id":null,"fork_from_message_id":null}'
```

> Omit `fork_from_*` for a fresh branch, or set both to fork at a point in another branch.

#### List branches in a thread

```bash
curl -s http://127.0.0.1:8000/v1/threads/<thread_id>/branches
```

### Messages

#### Append a message to a branch

```bash
curl -s -X POST http://127.0.0.1:8000/v1/branches/<branch_id>/messages \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 6f4b8c34-4ef2-4f7d-9988-9a8b831e1cec' \
  -d '{"role":"user","text":"Hello from main"}'
```

#### Read branch messages (paginated)

```bash
curl -s "http://127.0.0.1:8000/v1/branches/<branch_id>/messages?limit=50&cursor=<cursor>"
```

**Response**

```json
{"items":[{"id":"...","role":"user","text":"..."},...],
 "next_cursor":"..."}
```

### Diff

Compare two branches:

```bash
curl -s "http://127.0.0.1:8000/v1/diff?from=<branch_id_A>&to=<branch_id_B>"
```

**Response (example)**

```json
{
  "from":"<branch_id_A>",
  "to":"<branch_id_B>",
  "summary":{"added":2,"removed":0,"changed":1},
  "hunks":[
    {"type":"added","at":5,"messages":[{"id":"...","role":"assistant","text":"..."}]}
  ]
}
```

### Merge

Merge `source_branch_id` into `target_branch_id`. Strategies may include:

* `"ours"` — prefer target on conflict
* `"theirs"` — prefer source on conflict
* `"auto"` — best-effort 3-way (default)

```bash
curl -s -X POST http://127.0.0.1:8000/v1/merge \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 3b21a0b2-8b78-4c41-9f4b-2d9d6f1a0a12' \
  -d '{
    "thread_id":"<thread_id>",
    "source_branch_id":"<branch_id_src>",
    "target_branch_id":"<branch_id_dst>",
    "strategy":"auto",
    "message":"Merge src into dst"
  }'
```

**Response**

```json
{"merged_into":"<branch_id_dst>","conflicts":[],"commit_id":"<merge_id>"}
```

### Streaming (SSE/WebSocket)

If enabled, subscribe for live updates:

* **SSE**: `GET /v1/streams/threads/<thread_id>`
* **WS**: `GET /v1/ws?thread_id=<thread_id>`

Events include: `message.created`, `branch.created`, `merge.committed`.

---

## Idempotency

To safely retry POSTs, send `Idempotency-Key` (a UUID). The server will:

* return the **same** response for retries with the same key within the dedupe window,
* prevent duplicate side effects (e.g., duplicate messages or merges).

Example:

```bash
curl -s -X POST /v1/branches/<id>/messages \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 8ad0f1d1-4c7b-4ff6-9c6b-2e1e0f1a2b3c' \
  -d '{"role":"user","text":"Once only"}'
```

---

## Pagination

All collection endpoints support cursor-based pagination:

* Query params: `?limit=<int>&cursor=<opaque>`
* Response: `{ items: [...], next_cursor: "..." }`
* Pass `next_cursor` to fetch the next page.

---

## Reference Scripts

### Bash helpers (copy/paste)

```bash
set -euo pipefail

# Helpers
json_get_id() { python -c 'import sys,json; print(json.loads(sys.stdin.read())["id"])'; }
last_assistant_id() { python -c 'import sys,json; msgs=json.loads(sys.stdin.read()); print([m["id"] for m in msgs if m.get("role")=="assistant"][-1])'; }

# 1) Create thread + main branch
THREAD_JSON=$(curl -s -X POST http://127.0.0.1:8000/v1/threads -H 'Content-Type: application/json' -d '{"title":"Demo"}')
THREAD_ID=$(echo "$THREAD_JSON" | json_get_id)

B1_JSON=$(curl -s -X POST "http://127.0.0.1:8000/v1/threads/$THREAD_ID/branches" -H 'Content-Type: application/json' -d '{"name":"main"}')
B1_ID=$(echo "$B1_JSON" | json_get_id)

# 2) Seed main (creates user + assistant)
curl -s -X POST "http://127.0.0.1:8000/v1/branches/$B1_ID/messages" -H 'Content-Type: application/json' -d '{"role":"user","text":"Shared context"}' >/dev/null
curl -s -X POST "http://127.0.0.1:8000/v1/branches/$B1_ID/messages" -H 'Content-Type: application/json' -d '{"role":"assistant","text":"Noted."}' >/dev/null

# 3) Fork a feature branch from main tip
B2_JSON=$(curl -s -X POST "http://127.0.0.1:8000/v1/threads/$THREAD_ID/branches" -H 'Content-Type: application/json' -d "{\"name\":\"idea-A\",\"fork_from_branch_id\":\"$B1_ID\"}")
B2_ID=$(echo "$B2_JSON" | json_get_id)

# 4) Explore two different prompts
curl -s -X POST "http://127.0.0.1:8000/v1/branches/$B1_ID/messages" -H 'Content-Type: application/json' -d '{"role":"user","text":"Path A: summarize"}' >/dev/null
curl -s -X POST "http://127.0.0.1:8000/v1/branches/$B2_ID/messages" -H 'Content-Type: application/json' -d '{"role":"user","text":"Path B: brainstorm"}' >/dev/null

# 5) Diff & Merge
curl -s "http://127.0.0.1:8000/v1/diff?from=$B1_ID&to=$B2_ID" | jq .
curl -s -X POST "http://127.0.0.1:8000/v1/merge" -H 'Content-Type: application/json' -d "{\"thread_id\":\"$THREAD_ID\",\"source_branch_id\":\"$B2_ID\",\"target_branch_id\":\"$B1_ID\",\"strategy\":\"auto\",\"message\":\"Merge idea-A back\"}" | jq .
```

---

## Testing

```bash
pytest -q
# or
make test
```

> If a merge/diff test fails, ensure your DB is clean (drop & recreate) and all migrations are applied.

---

## Troubleshooting

**Q: `psql: FATAL: role "convo" does not exist`**
A: Create the role/database:

```bash
psql -h 127.0.0.1 -U postgres -c "CREATE ROLE convo WITH LOGIN PASSWORD 'convo' SUPERUSER;"
psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE convohub OWNER convo;"
```

**Q: Docker Compose warns `the attribute 'version' is obsolete`**
A: Safe to ignore; or remove `version:` from `docker-compose.yml` for newer Compose specs.

**Q: Can't connect to DB from app**

* Verify `DATABASE_URL` matches your Postgres host/port.
* From the app container: `pg_isready -h 127.0.0.1 -p 5432 -U convo`.

**Q: Uvicorn reload not picking up changes**

* Run `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` outside Docker, or mount your code as a volume in Compose.

---

## Roadmap

* **Graph UI (Next.js + React Flow)**

  * Left: DAG view of branches and merges
  * Right: Node inspector (messages, summaries, memory)
  * Actions: Create branch, Merge selected, Send message, View diff
  * Live updates via SSE/WS
* **LLM connectors**: plug any provider per-branch
* **Rich merge policies**: semantic/conflict resolvers with LLM assist
* **Auth & RBAC** for multi-user projects

---

## License

MIT © ConvoHub contributors
