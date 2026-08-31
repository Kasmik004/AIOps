# LangOps

An AI-powered Telegram bot that turns natural-language requests into GitHub issues. The bot is built with LangGraph for orchestration, FastAPI for the webhook server, Telegram for user interaction, and a custom MCP server for GitHub actions.

## Overview

This project allows a user to send a message like:

- Create a GitHub issue for a login bug
- Open an issue about slow API responses
- File a bug report for the dashboard not loading

The bot interprets the request, decides whether the action is appropriate, and creates the corresponding GitHub issue through a custom MCP tool layer.

## Architecture

The project is composed of four main parts:

- LangGraph agent: handles intent understanding, decision-making, and workflow orchestration
- FastAPI app: receives Telegram webhook updates and exposes the bot API endpoints
- Telegram bot: interacts with users through chat messages and buttons
- Custom MCP server: exposes GitHub tools to the agent so it can create issues safely

### High-level flow

1. User sends a message to the Telegram bot.
2. FastAPI receives the webhook event.
3. The LangGraph agent reads the request and determines the correct action.
4. The agent calls a GitHub tool exposed by the MCP server.
5. A GitHub issue is created in the target repository.
6. The bot responds to the user with confirmation or status.

## Tech stack

- Python
- FastAPI
- LangGraph
- LangChain Groq
- Telegram Bot API
- Model Context Protocol (MCP)
- GitHub API / PyGithub
- Docker

## Project structure

```text
AIOps/
├── app/
│   ├── agent.py
│   ├── config.py
│   ├── db.py
│   ├── main.py
│   ├── security.py
│   └── telegram.py
├── mcp_server/
│   ├── github_tools.py
│   └── server.py
├── tests/
│   ├── db.py
│   ├── first.py
│   ├── github_api.py
│   ├── server.py
│   └── test_agent.py
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── README.md
├── plan.md
├── not_main.py
└── .env
```

## Features

- Natural-language issue creation from Telegram messages
- Agent-based reasoning using LangGraph and LLM tools
- Custom MCP integration for GitHub actions
- Human approval flow before making critical actions
- FastAPI backend for webhook processing
- Docker support for easy deployment
- Environment-based configuration for secrets and tokens

## Example user flow

A user sends:

"Create a GitHub issue for a bug where users cannot log in after resetting their password."

The bot will:

- parse the message
- determine that the user wants a GitHub issue created
- gather details from the request
- call the MCP server tool to create a GitHub issue
- send a confirmation back to Telegram

## Environment variables

Create a .env file in the project root with values like:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
WEBHOOK_SECRET_TOKEN=your_webhook_secret
GROQ_API_KEY=your_groq_key
GITHUB_TOKEN=your_github_personal_access_token
DATABASE_URL=postgresql://user:password@host:port/dbname
ALLOWED_USERS=123456789,987654321
```

Important:

- Never commit secrets to Git
- Keep tokens inside environment variables only
- Restrict GitHub tokens to the minimum permissions needed

## Local development

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your .env file.
4. Start the app locally:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Expose the app with ngrok or your public tunnel if using Telegram webhooks.

## Docker

Build the Docker image:

```bash
docker build -t telegram-agent-bot .
```

Run the container:

```bash
docker run -d --name telegram-bot-container -p 8000:8000 --env-file .env telegram-agent-bot
```

## Security notes

This project performs real GitHub actions, so security is important.

- Validate Telegram webhook secrets
- Restrict access to allowed user IDs
- Use GitHub tokens with minimal required permissions
- Use a dedicated test repository for development
- Avoid exposing secrets in logs or commit history

## Current purpose

This project demonstrates how to build a practical AI agent that connects:

- a user-facing chat app
- an LLM orchestration layer
- tool execution through MCP
- real external system actions

The core idea is to allow users to request operational tasks in plain English and have an AI workflow translate that into real GitHub work items.

## Future improvements

- Support issue labels, milestone assignment, and assignees
- Add support for pull requests and other GitHub workflows
- Improve approval and confirmation flow for destructive tasks
- Add better logging and observability
- Add tests for webhook handling and GitHub tool execution

## License

This project is for learning and experimentation. Update this section if you plan to release it under a specific license.
