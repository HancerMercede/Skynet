# Project Brain

MCP server with SQLite for persistent AI agent memory.

## Overview

Project Brain is a portable memory layer for AI agents working on software projects. It solves the central problem of LLMs: loss of context between sessions.

## Features

- **Global Installation**: Single database at `~/.brain/skynet.db` - works from any folder
- **Universal Protocol**: Exposed as MCP server (Claude Code, Cursor, Windsurf) and REST API (LangChain, AutoGen, custom agents)
- **Autonomous**: Agent reads and writes to DB without human intervention
- **Session Continuity**: Agent automatically recovers previous state on startup
- **No External Dependencies**: Python stdlib + sqlite3 + FastMCP + FastAPI

## Installation

```bash
pip install -e .
```

## Quick Start

### Start the Brain Server

```bash
brain service install   # Show setup info
brain service start    # Start REST API server (runs in background)
brain service status   # Check if running
```

The server runs at http://localhost:7842

### Use with Claude Code / Cursor / Windsurf

```bash
brain mcp   # Start MCP server (for Claude Code/Cursor)
```

Or configure in `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "skynet": {
      "command": "brain",
      "args": ["mcp"]
    }
  }
}
```

## CLI Commands

```bash
# Service management
brain service start    # Start REST API server
brain service stop     # Stop server
brain service status   # Check if running
brain service install  # Show setup info

# MCP server (for Claude Code/Cursor)
brain mcp

# Project management (uses global ~/.brain/skynet.db)
brain init --name "My Project" --stack python,fastapi
brain status
brain rule add --category code --rule "Always use type hints"
```

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/context/{project_id}` | GET | Get full project context |
| `/sessions` | POST | Start new session |
| `/sessions/{id}` | PATCH | Close session |
| `/memory` | POST | Save memory |
| `/memory/{project_id}` | GET | Recall memories |
| `/memory/{project_id}/{key}` | DELETE | Forget memory |
| `/tasks` | POST | Create task |
| `/tasks/{id}` | PATCH | Update task |
| `/tasks/{project_id}` | GET | Get tasks |
| `/errors` | POST | Log error |
| `/errors/{id}` | PATCH | Resolve error |
| `/decisions` | POST | Add decision |
| `/patterns` | POST | Save pattern |
| `/rules/{project_id}` | GET | Get rules |

## Integration

### Claude Code / Cursor / Windsurf

Add to `.claude/mcp.json` or MCP settings:

```json
{
  "mcpServers": {
    "project-brain": {
      "command": "python",
      "args": ["-m", "server.mcp_server"],
      "cwd": "/path/to/project-brain"
    }
  }
}
```

### LangChain / AutoGen (REST)

```python
import requests

BRAIN = 'http://localhost:7842'

# Start session
session = requests.post(f'{BRAIN}/sessions', json={
    'project_id': 1,
    'agent_id': 'langchain-agent',
    'goal': 'Refactor authentication module'
}).json()

# Get context
ctx = requests.get(f'{BRAIN}/context/1').json()

# Save memory
requests.post(f'{BRAIN}/memory', json={
    'project_id': 1,
    'session_id': session['id'],
    'type': 'insight',
    'key': 'auth_pattern',
    'value': 'Use JWT with refresh tokens',
    'relevance': 0.9
})
```

## Agent Protocol

### At Session Start (Required)

1. Call `brain_start_session` with clear goal
2. Call `brain_get_context` to load project state
3. Call `brain_get_rules` to load constraints
4. Review `open_errors` - don't repeat known errors

### During Work

- **Important discovery**: Call `brain_remember` immediately
- **Start task**: Call `brain_add_task` + `brain_update_task` to 'in_progress'
- **Error occurs**: Call `brain_log_error` with full context
- **Error resolved**: Call `brain_resolve_error` with solution
- **Architecture decision**: Call `brain_add_decision`

### At Session End (Required)

1. Mark all completed tasks as 'done'
2. Call `brain_close_session` with detailed summary

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
