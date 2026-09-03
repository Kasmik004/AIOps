# AIOps

A Telegram bot that lets you query your codebase and flag Github issues from your phone instead of your editor. It can pull the latest code and rebuild a knowledge graph of it, answer questions about that codebase using the graph instead of guessing, and file a GitHub issue when you spot something wrong, all from a chat message, so you don't have to open VS Code just to flag a bug.

It's built around a [LangGraph](https://github.com/langchain-ai/langgraph) agent that puts a human-approval gate in front of every real action: the agent proposes what it wants to do, you tap **Approve** or **Reject** in Telegram, and only then does it run.

Send the bot a message like:

> Create a GitHub issue for a bug where users can't log in after resetting their password.

The agent parses the request, drafts the tool call, asks you to approve or reject it via a Telegram inline button, and only then creates the issue.

## How it works

1. A user messages the Telegram bot, and Telegram calls the app's `/webhook` endpoint.
2. FastAPI validates the request (webhook secret, user allowlist, duplicate `update_id` filtering) and hands it off to a background task so Telegram gets an immediate `200 OK`.
3. The background task drives a **LangGraph** state machine: an LLM node decides what to do, and if it wants to call a tool, execution stops at a **human-approval** node.
4. The bot sends the proposed action back to the user as an inline-keyboard message (`Approve` / `Reject`).
5. The user's tap comes back as a Telegram `callback_query`, which **resumes the same graph run** from where it paused (via LangGraph's `interrupt`/`Command(resume=...)`), using conversation state checkpointed in Postgres.
6. On approval, the graph executes the tool through one of two **MCP servers**: a custom GitHub server, or a Graphify code-graph server, and the result flows back to the user.

## Core concepts

- **Human-in-the-loop tool execution.** Every tool call the LLM proposes is intercepted by a `human_approval` node ([app/agent.py](app/agent.py)) before it reaches the `tools` node. The graph is paused with LangGraph's `interrupt()`, and only resumed once a decision (`approve`/`reject`) is supplied.
- **Per-conversation tool trust.** Once a tool is approved once in a conversation, it's added to `accepted_tools` in the graph state and auto-approved for the rest of that thread, so you don't get asked to approve `create_github_issue` on every single call. `sync_codebase` is treated as safe and always skips approval entirely.
- **Durable, resumable state.** Each webhook call is a fresh, stateless HTTP request/process invocation, so nothing survives in memory between them. LangGraph's `AsyncPostgresSaver` checkpoints the entire graph state (messages, pending interrupts, accepted tools) to Postgres, keyed by `thread_id = telegram_chat_id`, so a conversation, including a paused approval, survives across separate webhook calls.
- **Multi-server MCP.** The agent doesn't hardcode its tools. `MultiServerMCPClient` (from `langchain-mcp-adapters`) launches and merges tools from two independent [MCP](https://modelcontextprotocol.io/) servers over stdio (a custom GitHub server and Graphify's code-graph server) into one toolset handed to the LLM.
- **Streamed progress, not just a final answer.** The graph is run with `astream(..., stream_mode=["updates", "custom"])`. `"updates"` carries state deltas (including interrupts); `"custom"` carries ad-hoc progress messages pushed via `get_stream_writer()` (e.g. "syncing codebase..."), so long-running tools can narrate what they're doing before the final reply.
- **Codebase Q&A grounded in a real graph, not guesses.** Graphify statically parses a codebase into nodes/edges/communities (functions, classes, files, and how they connect), stores it as `graph.json`, and serves it back over its own MCP server. [graph/code_server.py](graph/code_server.py) shows this in isolation: a LangGraph agent with a system prompt that forces it to call a graph tool and cite `file:line` rather than answer from training data. `sync_codebase` ([mcp_server/server.py](mcp_server/server.py)) keeps that graph fresh by `git pull`-ing the target repo and running `graphify update` after code changes.
- **Idempotent webhook handling.** Telegram retries webhook deliveries it doesn't get a fast `200` for. [app/main.py](app/main.py) tracks seen `update_id`s in a capped in-memory set so retried deliveries are dropped instead of double-processed.

## Tech stack

| Layer | Tools |
|---|---|
| Runtime | Python 3.13 |
| Web server | FastAPI, Uvicorn |
| Chat interface | Telegram Bot API (webhooks, inline keyboards) via `httpx` |
| Agent orchestration | LangGraph (`StateGraph`, `interrupt`/`Command`, streaming, `ToolNode`) |
| LLM layer | LangChain, `langchain-groq` (Groq-hosted `qwen/qwen3.6-27b`) |
| Tool protocol | Model Context Protocol (MCP): `FastMCP` for servers, `langchain-mcp-adapters` (`MultiServerMCPClient`) for the agent |
| GitHub integration | PyGithub |
| Code knowledge graph | Graphify (`graphifyy`): static analysis into graph.json plus a Markdown report, served over its own MCP tools |
| Persistence | PostgreSQL via `psycopg` + `langgraph-checkpoint-postgres` (`AsyncPostgresSaver`) |
| Deployment | Docker |
| Dependency management | `uv` (`pyproject.toml` + `uv.lock`) for dev, `requirements.txt` for the Docker image |
| Testing | `unittest`, `pytest` (with FastAPI's `TestClient`) |

## Project structure

```text
AIOps/
├── app/
│   ├── main.py         # FastAPI app: webhook auth, dedup, message routing, Telegram replies
│   ├── agent.py         # LangGraph agent: MCP client setup, LLM node, human-approval node, streaming
│   ├── db.py            # Postgres helper (WIP, not wired into the running app)
│   ├── config.py        # empty, reserved for centralizing settings
│   ├── security.py      # empty, reserved for auth/allowlist logic
│   └── telegram.py      # empty, reserved for a Telegram client wrapper
├── mcp_server/
│   ├── server.py         # FastMCP server: create_github_issue, sync_codebase tools
│   └── github_tools.py   # PyGithub wrapper used by create_github_issue
├── graph/
│   ├── code_server.py     # Standalone demo: LangGraph agent that answers codebase questions via Graphify's MCP tools
│   ├── test.py            # Toy FastAPI app used as a target to build a graph against
│   └── graphify-out/      # Generated artifacts: graph.json, graph.html (visual), GRAPH_REPORT.md, analysis cache
├── tests/                 # unittest/pytest coverage + exploratory scripts
├── repo/                  # Local clone that sync_codebase pulls into (empty until first sync)
├── not_main.py            # Earlier, minimal webhook prototype kept for reference
├── Dockerfile
├── requirements.txt / pyproject.toml / uv.lock
└── .env.example
```

## Environment variables

The running code reads these (some names differ from the checked-in `.env.example`; this list reflects what's actually used):

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token       # app/main.py
WEBHOOK_SECRET_TOKEN=your_webhook_secret         # app/main.py, checked against Telegram's secret header
ALLOWED_USERS=123456789,987654321                # app/main.py, comma-separated Telegram user IDs
GROQ_API_KEY=your_groq_key                       # read implicitly by langchain_groq.ChatGroq
DATABASE_URL=postgresql://user:pass@host:port/db # app/agent.py, LangGraph's Postgres checkpointer
GITHUB_TOKEN=your_github_personal_access_token   # mcp_server/github_tools.py
GITHUB_REPOSITORY=owner/repo                     # mcp_server/server.py, default target repo for issues
```

Never commit secrets, and scope `GITHUB_TOKEN` to the minimum permissions needed (issue creation only, on a test repo while developing).

## Local development

```bash
# install dependencies (pick one)
uv sync
# or
pip install -r requirements.txt

# configure .env, then run
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Expose the app with a public tunnel (ngrok or similar) and register that URL as your Telegram bot's webhook to test end-to-end.

## Docker

```bash
docker build -t telegram-agent-bot .
docker run -d --name telegram-bot-container -p 8000:8000 --env-file .env telegram-agent-bot
```

## Known limitations

- `mcp_server/server.py` hardcodes the codebase path `sync_codebase` operates on (`REPO_DIR`) to a local absolute path, so it targets a specific repo and branch, not a configurable one.
- `app/config.py`, `app/security.py`, and `app/telegram.py` are empty placeholders; the logic they'd hold currently lives inline in `app/main.py`.
- `app/db.py` isn't imported by the running app; Postgres access for the agent's checkpointer goes through `langgraph-checkpoint-postgres` directly in `app/agent.py`.

