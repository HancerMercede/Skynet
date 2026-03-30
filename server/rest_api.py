from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from brain.db import BrainDB
import uvicorn

app = FastAPI(
    title="Project Brain API",
    version="1.0",
    description="""
# Project Brain - Persistent Memory for AI Agents

A REST API that provides persistent memory and context management for AI agents working on software projects.

## Features
- **Sessions**: Track agent work sessions with goals and summaries
- **Memory**: Store key-value memories with relevance scoring and tagging
- **Tasks**: Manage project tasks with status tracking
- **Errors**: Log and resolve errors to avoid repetition
- **Decisions**: Record architectural decisions (ADRs)
- **Patterns**: Save reusable code snippets
- **Rules**: Define project-specific constraints

## Use Case
AI agents (Claude Code, Cursor, LangChain, AutoGen) use this API to maintain context between sessions,
track progress, and avoid repeating mistakes.

## Base URL
`http://localhost:7842`
""",
)
db = BrainDB()


class SessionCreate(BaseModel):
    project_id: int
    agent_id: str
    goal: str


class SessionUpdate(BaseModel):
    summary: str


class MemoryCreate(BaseModel):
    project_id: int
    session_id: Optional[int] = None
    type: str
    key: str
    value: str
    relevance: float = 0.5
    tags: Optional[str] = None


class TaskCreate(BaseModel):
    project_id: int
    session_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: int = 5


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class ErrorCreate(BaseModel):
    project_id: int
    session_id: Optional[int] = None
    error: str
    context: Optional[str] = None
    file_path: Optional[str] = None


class ErrorResolve(BaseModel):
    solution: str


class DecisionCreate(BaseModel):
    project_id: int
    session_id: Optional[int] = None
    title: str
    context: str
    chosen: str
    alternatives: Optional[str] = None
    consequences: Optional[str] = None


class PatternCreate(BaseModel):
    project_id: int
    session_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    code_snippet: str
    language: str
    tags: Optional[str] = None


class RuleCreate(BaseModel):
    project_id: int
    category: str
    rule: str
    priority: int = 5


@app.get(
    "/context/{project_id}",
    summary="Get full project context",
    description="""
Retrieve complete project state including:
- Project metadata (name, stack, status)
- Active tasks (in_progress)
- Pending tasks
- Completed tasks
- Top memories (relevance > 0.6)
- Open errors (unresolved)
- Project rules
- Last session summary

**Use at session start** to understand current project state.
""",
)
def get_context(project_id: int):
    return db.get_full_context(project_id)


@app.post(
    "/sessions",
    summary="Start a new session",
    description="""
Create a new agent session for the project.

**Required at session start** - must be called before other operations.

**Request body:**
- project_id: Project ID
- agent_id: Agent identifier (e.g., "claude", "jarvis")
- goal: What the agent intends to accomplish

**Returns:** Session object with ID and status "active"

**Use case:** Track what each agent is working on and enable session history.
""",
)
def start_session(payload: SessionCreate):
    return db.start_session(payload.project_id, payload.agent_id, payload.goal)


@app.patch(
    "/sessions/{session_id}",
    summary="Close a session",
    description="""
Close an active session with a summary of work done.

**Required at session end** - always call when finishing work.

**Request body:**
- summary: What was accomplished during the session

**Returns:** Updated session with status "completed" and end timestamp

**Use case:** Enables future sessions to understand what was done previously via last_session.summary.
""",
)
def close_session(session_id: int, payload: SessionUpdate):
    return db.close_session(session_id, payload.summary)


@app.get(
    "/sessions/{session_id}",
    summary="Get session by ID",
    description="""
Retrieve a specific session by its ID.

**Returns:** Session object with all details including goal, summary, timestamps.

**Use case:** Review past session details or check session status.
""",
)
def get_session(session_id: int):
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post(
    "/memory",
    summary="Store a memory",
    description="""
Save important information to memory.

**Types:**
- insight: Technical discoveries or solutions
- context: Project overview or structure
- security: Security-related findings
- bug: Bug description and fix
- api: API endpoint information
- feature: Feature implementation details

**Request body:**
- project_id: Project ID (required)
- session_id: Session ID (optional)
- type: Memory type (insight, context, security, bug, api, feature)
- key: Unique identifier for this memory
- value: The actual content to remember
- relevance: 0.0-1.0 (1.0 = most important)
- tags: Comma-separated tags

**Use case:** Save important discoveries, solutions, patterns immediately - don't wait until session end.

**Auto-save triggers:**
- Bug fixed → log error + resolve
- Feature completed → mark task done + add memory
- Architecture decision → POST /decisions immediately
- Problem discovered → memory with type "warning" and relevance 0.9+
""",
)
def remember(payload: MemoryCreate):
    return db.remember(
        payload.project_id, payload.session_id, payload.type,
        payload.key, payload.value, payload.relevance, payload.tags
    )


@app.get(
    "/memory/{project_id}",
    summary="Recall memories",
    description="""
Retrieve memories for a project with optional filters.

**Query parameters (all optional):**
- type: Filter by memory type (insight, context, security, bug, api, feature)
- tag: Filter by tag
- search: Search in key and value
- limit: Number of results (default: 10)

**Returns:** List of memories sorted by relevance (highest first)

**Use case:** 
- Get context at session start
- Search for specific information
- Find patterns or solutions to similar problems
""",
)
def recall(project_id: int, type: str = None, tag: str = None, search: str = None, limit: int = 10):
    return db.recall(project_id, type, tag, search, limit)


@app.delete(
    "/memory/{project_id}/{key}",
    summary="Forget a memory",
    description="""
Delete or reduce relevance of an obsolete memory.

**Use case:** Remove outdated information that is no longer relevant.
""",
)
def forget(project_id: int, key: str):
    return db.forget(project_id, key)


@app.post(
    "/tasks",
    summary="Create a task",
    description="""
Create a new task for the project.

**Request body:**
- project_id: Project ID (required)
- session_id: Session ID (optional - links task to session)
- title: Task title (required)
- description: Detailed description
- priority: 1-10 (10 = highest priority, default: 5)

**Status values:** pending, in_progress, done, cancelled

**Use case:** Create tasks when starting new work items. Track progress by updating status.
""",
)
def add_task(payload: TaskCreate):
    return db.add_task(
        payload.project_id, payload.session_id, payload.title,
        payload.description, payload.priority
    )


@app.patch(
    "/tasks/{task_id}",
    summary="Update a task",
    description="""
Update task status or notes.

**Request body (all optional):**
- status: New status (pending, in_progress, done, cancelled)
- notes: Progress notes or completion details

**Partial updates supported** - send only what you want to change.

**Important:** 
- Use status "done" NOT "completed"
- When marking done, add notes about what was accomplished

**Use case:** 
- Start working: status = "in_progress"
- Complete: status = "done" + notes = "what was done"
""",
)
def update_task(task_id: int, payload: TaskUpdate):
    return db.update_task(task_id, payload.status, payload.notes)


@app.get(
    "/tasks/{project_id}",
    summary="Get tasks",
    description="""
Retrieve tasks for a project with optional filters.

**Query parameters (all optional):**
- status: Filter by status (pending, in_progress, done, cancelled)
- priority: Filter by priority (1-10)

**Returns:** List of tasks

**Use case:** Get all tasks, filter by status (e.g., pending only), or filter by priority.
""",
)
def get_tasks(project_id: int, status: str = None, priority: int = None):
    return db.get_tasks(project_id, status, priority)


@app.post(
    "/errors",
    summary="Log an error",
    description="""
Log an error or problem encountered during development.

**Request body:**
- project_id: Project ID (required)
- session_id: Session ID (optional)
- error: Error message/title (required)
- context: What was happening when error occurred
- file_path: File where error was found

**Use case:** Log errors you can't immediately fix so they can be tracked and resolved later.
This prevents repeating the same mistakes.
""",
)
def log_error(payload: ErrorCreate):
    return db.log_error(
        payload.project_id, payload.session_id, payload.error,
        payload.context, payload.file_path
    )


@app.patch(
    "/errors/{error_id}",
    summary="Resolve an error",
    description="""
Mark an error as resolved with the solution.

**Request body:**
- solution: How the error was fixed

**Use case:** When you fix a logged error, resolve it with the solution.
This creates a record of the fix for future reference.
""",
)
def resolve_error(error_id: int, payload: ErrorResolve):
    return db.resolve_error(error_id, payload.solution)


@app.get(
    "/errors/{project_id}",
    summary="Get errors",
    description="""
Retrieve errors for a project.

**Query parameters (optional):**
- resolved: Filter by resolution status (true/false)

**Use case:** 
- Get all open errors at session start (resolved=false)
- Review resolved errors to understand past problems and solutions
""",
)
def get_errors(project_id: int, resolved: bool = None):
    return db.get_errors(project_id, resolved)


@app.post(
    "/decisions",
    summary="Record a decision",
    description="""
Record an architectural decision (ADR - Architecture Decision Record).

**Request body:**
- project_id: Project ID (required)
- session_id: Session ID (optional)
- title: Decision title (e.g., "Use JWT with refresh tokens")
- context: Why this decision was needed
- chosen: What was chosen
- alternatives: What alternatives were considered
- consequences: Implications of this choice

**Use case:** Document important decisions immediately - don't wait until session end.
This creates a historical record of why certain choices were made.
""",
)
def add_decision(payload: DecisionCreate):
    return db.add_decision(
        payload.project_id, payload.session_id, payload.title,
        payload.context, payload.chosen, payload.alternatives, payload.consequences
    )


@app.get(
    "/decisions/{project_id}",
    summary="Get decisions",
    description="""
Retrieve all architectural decisions for a project.

**Use case:** Understand why certain technical choices were made.
Useful for onboarding new team members or reviewing past decisions.
""",
)
def get_decisions(project_id: int):
    return db.get_decisions(project_id)


@app.post(
    "/patterns",
    summary="Save a code pattern",
    description="""
Save a reusable code snippet or pattern.

**Request body:**
- project_id: Project ID (required)
- session_id: Session ID (optional)
- name: Pattern name (e.g., "JWT Auth Middleware")
- code_snippet: The actual code (required)
- language: Programming language (e.g., csharp, python, javascript)
- description: What this pattern does
- tags: Comma-separated tags (e.g., "auth,middleware,security")

**Use case:** Save reusable code snippets, boilerplate, utilities for future use.
""",
)
def save_pattern(payload: PatternCreate):
    return db.save_pattern(
        payload.project_id, payload.session_id, payload.name,
        payload.code_snippet, payload.language, payload.description, payload.tags
    )


@app.get(
    "/patterns/{project_id}",
    summary="Get code patterns",
    description="""
Retrieve saved code patterns.

**Query parameters (optional):**
- language: Filter by programming language
- tag: Filter by tag

**Use case:** Find reusable code snippets, patterns, utilities.
""",
)
def get_patterns(project_id: int, language: str = None, tag: str = None):
    return db.get_patterns(project_id, language, tag)


@app.get(
    "/rules/{project_id}",
    summary="Get project rules",
    description="""
Retrieve all rules for a project.

**Returns:** List of rules sorted by priority (highest first)

**Use case:** 
- Get rules at session start to understand constraints
- Rules define project-specific guidelines (commit format, code style, etc.)
""",
)
def get_rules(project_id: int):
    return db.get_rules(project_id)


@app.post(
    "/rules",
    summary="Add a rule",
    description="""
Add a new rule to the project.

**Request body:**
- project_id: Project ID (required)
- category: Rule category (e.g., "commits", "code_style", "memory", "security")
- rule: The rule text (required)
- priority: 1-10 (10 = highest priority, default: 5)

**Common categories:**
- commits: Version control rules
- code_style: Coding standards
- memory: When/how to use Project Brain
- security: Security requirements

**Use case:** Define project constraints and guidelines.
""",
)
def add_rule(payload: RuleCreate):
    return db.add_rule(payload.project_id, payload.category, payload.rule, payload.priority)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=7842)
