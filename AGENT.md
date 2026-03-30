# Project Brain - Agent Guide

A comprehensive guide for AI agents using Project Brain for persistent memory.

> **Note:** The `project_id` values in this guide (e.g., `project_id: 3`) are **examples only**. 
> In real usage, get your project_id dynamically from:
> - The `.skynet-config.json` file in your project folder
> - Or create a new project with `brain init --name "Your Project"`

---

## Quick Reference

| When | Action | Endpoint |
|------|--------|----------|
| Session Start | Get project context | `GET /context/{project_id}` |
| Session Start | Start session | `POST /sessions` |
| Session Start | Get rules | `GET /rules/{project_id}` |
| Work | Save memory | `POST /memory` |
| Work | Add task | `POST /tasks` |
| Work | Update task | `PATCH /tasks/{id}` |
| Work | Log error | `POST /errors` |
| Work | Add decision | `POST /decisions` |
| Work | Save pattern | `POST /patterns` |
| Session End | Close session | `PATCH /sessions/{id}` |

**Base URL:** `http://localhost:7842`

---

## 1. Session Start (Required)

Every time an agent starts working on a project, it MUST follow this protocol:

### Step 1: Get Full Project Context

```bash
GET /context/{project_id}
```

Returns:
```json
{
  "project": { "id", "name", "stack", "status" },
  "active_tasks": [...],
  "pending_tasks": [...],
  "completed_tasks": [...],
  "top_memory": [...],
  "open_errors": [...],
  "rules": [...],
  "last_session": { "id", "goal", "summary" }
}
```

**Why:** This tells the agent what tasks exist, what's done, what errors to avoid, and project rules.

### Step 2: Start a New Session

```bash
POST /sessions
{
  "project_id": 3,
  "agent_id": "jarvis",
  "goal": "Implement user profile management"
}
```

Returns:
```json
{
  "id": 1,
  "project_id": 3,
  "agent_id": "jarvis",
  "goal": "Implement user profile management",
  "status": "active"
}
```

**Why:** Tracks what the agent is working on and why. Enables session history.

### Step 3: Get Project Rules

```bash
GET /rules/{project_id}
```

Returns:
```json
[
  { "category": "commits", "rule": "Format: type: description", "priority": 10 },
  { "category": "memory", "rule": "Always consult Project Brain", "priority": 10 }
]
```

**Why:** Rules are constraints the agent must follow. Check this every session.

### Step 4: Check Open Errors

Check `open_errors` from `/context/{project_id}`. These are known issues that were logged but not resolved.

```json
{
  "error": "JWT expired error",
  "context": "Token refresh not implemented",
  "file_path": "Controllers/AuthController.cs"
}
```

**Why:** Don't repeat known mistakes. Solve these if possible.

---

## 2. During Work - Saving Information

### Saving Important Discoveries (Memory)

When you learn something important, save it immediately.

```bash
POST /memory
{
  "project_id": 3,
  "session_id": 1,
  "type": "insight",
  "key": "jwt_refresh",
  "value": "Use sliding window refresh - refresh token valid for 7 days",
  "relevance": 0.9,
  "tags": "auth,security"
}
```

**Types:**
- `insight` - Technical discovery or solution
- `context` - Project overview or structure
- `security` - Security-related finding
- `bug` - Bug description and fix
- `api` - API endpoint info
- `config` - Configuration setting

**Relevance:** 0.0 to 1.0 (1.0 = most important)

**Tags:** Comma-separated: "auth,security,important"

### Adding Tasks

When starting a new piece of work, create a task.

```bash
POST /tasks
{
  "project_id": 3,
  "session_id": 1,
  "title": "Implement JWT refresh token",
  "description": "Add refresh token endpoint, store refresh token in DB, implement sliding window",
  "priority": 8
}
```

**Priority:** 1-10 (10 = highest)

**Status values:** `pending`, `in_progress`, `done`, `cancelled`

### Updating Task Status

When you start working on a task:

```bash
PATCH /tasks/{task_id}
{
  "status": "in_progress"
}
```

When you complete a task:

```bash
PATCH /tasks/{task_id}
{
  "status": "done",
  "notes": "Implemented refresh token with 7-day expiry, stored in database"
}
```

**You can update just status OR just notes:**

```bash
# Just status
PATCH /tasks/5 {"status": "done"}

# Just notes
PATCH /tasks/5 {"notes": "Found a better approach using middleware"}

# Both
PATCH /tasks/5 {"status": "done", "notes": "Completed"}
```

### Logging Errors

When you encounter an error you can't immediately fix:

```bash
POST /errors
{
  "project_id": 3,
  "session_id": 1,
  "error": "NullReferenceException in UserService.GetUser",
  "context": "User profile returns null for unverified users",
  "file_path": "Services/UserService.cs"
}
```

### Resolving Errors

When you fix a logged error:

```bash
PATCH /errors/{error_id}
{
  "solution": "Added null check: if user.IsVerified then return user profile, else throw exception"
}
```

### Recording Decisions (ADRs)

When you make an architectural decision:

```bash
POST /decisions
{
  "project_id": 3,
  "session_id": 1,
  "title": "Use JWT with refresh tokens",
  "context": "Need persistent login without storing passwords",
  "chosen": "JWT access tokens (15min) + refresh tokens (7 days)",
  "alternatives": "Session cookies, OAuth2, API keys",
  "consequences": "Must implement token refresh endpoint, store refresh tokens securely"
}
```

### Saving Code Patterns

When you create a reusable code snippet:

```bash
POST /patterns
{
  "project_id": 3,
  "session_id": 1,
  "name": "JWT Auth Middleware",
  "code_snippet": "[Authorize(AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]",
  "language": "csharp",
  "description": "Controller attribute for JWT-protected endpoints",
  "tags": "auth,middleware,security"
}
```

---

## 2.1 When to Save — No Need to Be Asked

Save to Brain automatically after these events:

- Bug fixed → POST /errors (log) + PATCH /errors/{id} (resolve with solution)
- Feature completed → PATCH /tasks/{id} (done) + POST /memory (what you learned)
- Architecture decision made → POST /decisions immediately, do not wait
- Problem discovered → POST /memory with type "warning" and relevance 0.9+
- Every 10 messages → POST /memory with a progress summary
- Reusable code written → POST /patterns

DO NOT wait for the user to say "save to Brain" or "update your memory".
DO NOT wait until the end of the session.
Save as you go — the Brain is only useful if it has current data.

---

## 3. Session End (Required)

When you're done for the session:

### Step 1: Mark Tasks Complete

```bash
# For each task you worked on
PATCH /tasks/{task_id}
{
  "status": "done",
  "notes": "What you accomplished"
}
```

### Step 2: Close Session

```bash
PATCH /sessions/{session_id}
{
  "summary": "Implemented JWT auth with refresh tokens. User entity, Register/Login endpoints, PasswordHasher, JWT config, [Authorize] on controllers"
}
```

This saves your work summary so future sessions know what was done.

---

## 3.1 After Context Reset or Compaction

If your context was reset, compacted, or you lost track of 
what was happening — do this before anything else:

1. Load current project state:
   GET http://localhost:7842/context/{project_id}

2. Check last session summary:
   The field "last_session.summary" tells you exactly 
   what was done before. Read it completely.

3. Check active tasks:
   The field "active_tasks" shows what was in progress.
   Continue from where it was left off.

4. Do NOT ask the user to repeat context.
   Do NOT start fresh as if nothing was done before.
   The Brain has everything — query it first.

---

## 4. Retrieving Information

### Get Tasks

```bash
GET /tasks/{project_id}
GET /tasks/{project_id}?status=pending
GET /tasks/{project_id}?priority=8
```

### Get Memory

```bash
# All memories
GET /memory/{project_id}

# Filter by type
GET /memory/{project_id}?type=insight

# Filter by tag
GET /memory/{project_id}?tag=auth

# Search by text
GET /memory/{project_id}?search=jwt

# Limit results
GET /memory/{project_id}?limit=20
```

### Get Decisions

```bash
GET /decisions/{project_id}
```

### Get Patterns

```bash
GET /patterns/{project_id}
GET /patterns/{project_id}?language=csharp
GET /patterns/{project_id}?tag=auth
```

---

## 5. Complete Example Workflow

### Session Start

```bash
# 1. Get context
curl http://localhost:7842/context/3

# 2. Start session
curl -X POST http://localhost:7842/sessions \
  -H "Content-Type: application/json" \
  -d '{"project_id": 3, "agent_id": "claude", "goal": "Add password reset feature"}'

# 3. Get rules
curl http://localhost:7842/rules/3
```

### During Work

```bash
# Save an insight
curl -X POST http://localhost:7842/memory \
  -H "Content-Type: application/json" \
  -d '{"project_id":3,"session_id":1,"type":"insight","key":"smtp_config","value":"Use SendGrid for emails","relevance":0.8,"tags":"email"}'

# Create a task
curl -X POST http://localhost:7842/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_id":3,"session_id":1,"title":"Add password reset endpoint","priority":8}'

# Start working on task
curl -X PATCH http://localhost:7842/tasks/5 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Log an error you can't fix now
curl -X POST http://localhost:7842/errors \
  -H "Content-Type: application/json" \
  -d '{"project_id":3,"session_id":1,"error":"SMTP not configured","context":"Need SendGrid API key"}'

# Record a decision
curl -X POST http://localhost:7842/decisions \
  -H "Content-Type: application/json" \
  -d '{"project_id":3,"session_id":1,"title":"Email provider","context":"Need password reset","chosen":"SendGrid","alternatives":"AWS SES, MailGun","consequences":"Need API key in config"}'
```

### Session End

```bash
# Mark task done
curl -X PATCH http://localhost:7842/tasks/5 \
  -H "Content-Type: application/json" \
  -d '{"status": "done", "notes": "Reset email sent with token"}'

# Close session
curl -X PATCH http://localhost:7842/sessions/1 \
  -H "Content-Type: application/json" \
  -d '{"summary": "Added password reset: forgot password endpoint, reset email with token, token validation"}'
```

---

## 6. Common Mistakes to Avoid

### ❌ Don't Skip Session Start
Always call `/sessions` first. Without it:
- No session_id for tasks/memories
- No history in `last_session`

### ❌ Don't Use "completed" for Status
Use `done`, not `completed`:
```bash
# Wrong - will fail!
PATCH /tasks/1 {"status": "completed"}

# Correct
PATCH /tasks/1 {"status": "done"}
```

Valid values: `pending`, `in_progress`, `done`, `cancelled`

### ❌ Don't Forget to Close Sessions
Always close the session with a summary. This is how future agents know what was done.

### ❌ Don't Save Everything
Save only important things:
- ✅ Solutions to problems
- ✅ Architectural decisions
- ✅ Code patterns you'll reuse
- ✅ Security findings
- ❌ Every minor thought

### ❌ Don't Ignore Open Errors
Check `open_errors` from context. Solve them or add context if you can't.

---

## 7. Python Code Example

```python
import requests

BASE_URL = "http://localhost:7842"
PROJECT_ID = 3

class ProjectBrain:
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.session_id = None
    
    def start_session(self, agent_id: str, goal: str):
        resp = requests.post(f"{BASE_URL}/sessions", json={
            "project_id": self.project_id,
            "agent_id": agent_id,
            "goal": goal
        })
        self.session_id = resp.json()["id"]
        return resp.json()
    
    def get_context(self):
        return requests.get(f"{BASE_URL}/context/{self.project_id}").json()
    
    def remember(self, key: str, value: str, type: str = "insight", 
                 relevance: float = 0.7, tags: str = None):
        return requests.post(f"{BASE_URL}/memory", json={
            "project_id": self.project_id,
            "session_id": self.session_id,
            "type": type,
            "key": key,
            "value": value,
            "relevance": relevance,
            "tags": tags
        }).json()
    
    def add_task(self, title: str, description: str = None, priority: int = 5):
        return requests.post(f"{BASE_URL}/tasks", json={
            "project_id": self.project_id,
            "session_id": self.session_id,
            "title": title,
            "description": description,
            "priority": priority
        }).json()
    
    def update_task(self, task_id: int, status: str = None, notes: str = None):
        data = {}
        if status: data["status"] = status
        if notes: data["notes"] = notes
        return requests.patch(f"{BASE_URL}/tasks/{task_id}", json=data).json()
    
    def close_session(self, summary: str):
        return requests.patch(f"{BASE_URL}/sessions/{self.session_id}", 
                              json={"summary": summary}).json()


# Usage
brain = ProjectBrain(PROJECT_ID)

# Start
brain.start_session("agent", "Add user profile feature")

# Work
brain.remember("profile_dto", "Use Record type for DTOs", "insight", 0.8, "csharp")
task = brain.add_task("Create Profile DTO", "Create UserProfileDto with validation", 7)
brain.update_task(task["id"], status="in_progress")

# ... do work ...

# End
brain.update_task(task["id"], status="done", notes="Created UserProfileDto")
brain.close_session("Added user profile feature with DTOs and validation")
```

---

## 8. Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 422 Unprocessable Entity | Invalid JSON or missing field | Check payload format |
| 500 Internal Server Error | Server bug | Check server logs |
| Connection refused | Server not running | Run `brain service start` |

---

## Summary Checklist

- [ ] Session start: `/sessions` + `/context/{id}` + `/rules/{id}`
- [ ] Check `open_errors` from context
- [ ] Save important discoveries to `/memory`
- [ ] Create tasks for new work at `/tasks`
- [ ] Update task status as you progress
- [ ] Log errors you can't fix immediately
- [ ] Record architectural decisions at `/decisions`
- [ ] Save reusable patterns at `/patterns`
- [ ] Session end: mark tasks `done` + close session with summary

---

## 9. Using MCP Instead of REST API

If you're using Claude Code, Cursor, Windsurf, or any MCP client, you don't need to make HTTP calls. The tools are available directly.

### MCP Tools Available

| MCP Tool | Equivalent REST | Description |
|----------|-----------------|-------------|
| `brain_get_context` | `GET /context/{id}` | Get full project context |
| `brain_start_session` | `POST /sessions` | Start new session |
| `brain_close_session` | `PATCH /sessions/{id}` | Close session |
| `brain_remember` | `POST /memory` | Save memory |
| `brain_recall` | `GET /memory/{id}` | Retrieve memories |
| `brain_forget` | `DELETE /memory/{id}/{key}` | Delete memory |
| `brain_add_task` | `POST /tasks` | Create task |
| `brain_update_task` | `PATCH /tasks/{id}` | Update task |
| `brain_get_tasks` | `GET /tasks/{id}` | Get tasks |
| `brain_log_error` | `POST /errors` | Log error |
| `brain_resolve_error` | `PATCH /errors/{id}` | Resolve error |
| `brain_add_decision` | `POST /decisions` | Record decision |
| `brain_save_pattern` | `POST /patterns` | Save code pattern |
| `brain_get_rules` | `GET /rules/{id}` | Get project rules |

### Starting MCP Server

```bash
brain mcp
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

### MCP Usage Example

```python
# The MCP client calls these functions directly

# Session start
brain_get_context(project_id=3)
brain_start_session(project_id=3, agent_id="claude", goal="Add feature")

# During work
brain_remember(project_id=3, session_id=1, type="insight", 
               key="config", value="Use appsettings.json", relevance=0.8)
brain_add_task(project_id=3, session_id=1, title="Add feature", priority=8)
brain_update_task(task_id=5, status="in_progress")

# Session end
brain_update_task(task_id=5, status="done", notes="Done!")
brain_close_session(session_id=1, summary="Added feature")
```

### Key Differences: REST vs MCP

| Aspect | REST API | MCP |
|--------|----------|-----|
| Protocol | HTTP | stdio |
| Endpoint | `localhost:7842` | Direct function call |
| Authentication | None | None |
| Project ID | Pass in JSON | Pass as parameter |
| Status | Must run server | Must run `brain mcp` |

### When to Use What

- **REST API**: LangChain, AutoGen, custom agents, any HTTP client
- **MCP**: Claude Code, Cursor, Windsurf, agents with MCP support

Both use the same database - choose based on what your agent supports.
