# AutoStore Support Agent

AI-powered customer support agent that generates suggested email replies
using AutoStore Interface documentation as the knowledge source.

## Architecture

The agent is driven by prompts under `prompts/` (system instructions, classification,
and templates). The ReadMe-hosted MCP server exposes AutoStore Interface docs to the
IDE. A future production agent may live under `agent/`; see that folder for code layout.

## Status

| Component                  | Status |
|----------------------------|--------|
| ReadMe MCP server          | Live (`https://interface.autostoresystem.com/mcp`) |
| Cursor IDE MCP connection  | **Connected** — config: `.cursor/mcp.json` or `config/mcp.json`; verified via `search` tool |
| ReadMe **AI Booster Pack** | **Active** in the ReadMe application |
| Azure MCP Server (Outlook) | Pending |
| Azure OpenAI               | Pending |

**ReadMe:** AI Booster Pack is enabled for this project in ReadMe. If MCP tools still
fail or return errors, check network connectivity, API token configuration in
`.cursor/mcp.json` / `config/mcp.json`, and ReadMe service status.

## Setup (secrets)

Do not commit API keys. This repo includes:

- `config/mcp.json.example` — copy to `config/mcp.json` (or `.cursor/mcp.json`) and set your ReadMe bearer token.
- `.env.example` — copy to `.env` and fill values for local agent runs.

`config/mcp.json`, `.cursor/mcp.json`, and `.env` are listed in `.gitignore`.

## Quick Start (Cursor Testing)

1. Open this project in Cursor
2. Verify MCP connection: **Settings → Tools and Integrations → MCP Tools**
3. Open AI chat (Ctrl+L) and test:

Read the system prompt in `prompts/system_prompt.md`.
Then use the autostore-docs MCP to answer this customer email:
"Can we use both Task Interface and Bin Interface together?"

## Project Structure

```
.cursor/mcp.json             MCP server connections (Cursor, not in git)
config/mcp.json.example      Template; copy to config/mcp.json locally
config/mcp.json              Local MCP config (gitignored)
.env.example                 Template for agent env vars
.env                         Local secrets (gitignored)
prompts/                     LLM prompt engineering
  system_prompt.md           Core agent instructions
  reply_templates.md         Example replies
  classification.md          Topic classification rules
tests/                       Validation test cases
agent/                       Production agent code paths
```

## Team

| Role               | Responsibility                          |
|--------------------|-----------------------------------------|
| Documentation team | ReadMe MCP, prompts, test cases         |
| IT department      | Azure OpenAI, Outlook MCP provisioning  |
| Engineering        | Production agent development            |
