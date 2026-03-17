from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from brain.db import BrainDB
import uvicorn

app = FastAPI(title="Project Brain API", version="1.0")
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


@app.get("/context/{project_id}")
def get_context(project_id: int):
    return db.get_full_context(project_id)


@app.post("/sessions")
def start_session(payload: SessionCreate):
    return db.start_session(payload.project_id, payload.agent_id, payload.goal)


@app.patch("/sessions/{session_id}")
def close_session(session_id: int, payload: SessionUpdate):
    return db.close_session(session_id, payload.summary)


@app.get("/sessions/{session_id}")
def get_session(session_id: int):
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/memory")
def remember(payload: MemoryCreate):
    return db.remember(
        payload.project_id, payload.session_id, payload.type,
        payload.key, payload.value, payload.relevance, payload.tags
    )


@app.get("/memory/{project_id}")
def recall(project_id: int, type: str = None, tag: str = None, search: str = None, limit: int = 10):
    return db.recall(project_id, type, tag, search, limit)


@app.delete("/memory/{project_id}/{key}")
def forget(project_id: int, key: str):
    return db.forget(project_id, key)


@app.post("/tasks")
def add_task(payload: TaskCreate):
    return db.add_task(
        payload.project_id, payload.session_id, payload.title,
        payload.description, payload.priority
    )


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    return db.update_task(task_id, payload.status, payload.notes)


@app.get("/tasks/{project_id}")
def get_tasks(project_id: int, status: str = None, priority: int = None):
    return db.get_tasks(project_id, status, priority)


@app.post("/errors")
def log_error(payload: ErrorCreate):
    return db.log_error(
        payload.project_id, payload.session_id, payload.error,
        payload.context, payload.file_path
    )


@app.patch("/errors/{error_id}")
def resolve_error(error_id: int, payload: ErrorResolve):
    return db.resolve_error(error_id, payload.solution)


@app.get("/errors/{project_id}")
def get_errors(project_id: int, resolved: bool = None):
    return db.get_errors(project_id, resolved)


@app.post("/decisions")
def add_decision(payload: DecisionCreate):
    return db.add_decision(
        payload.project_id, payload.session_id, payload.title,
        payload.context, payload.chosen, payload.alternatives, payload.consequences
    )


@app.get("/decisions/{project_id}")
def get_decisions(project_id: int):
    return db.get_decisions(project_id)


@app.post("/patterns")
def save_pattern(payload: PatternCreate):
    return db.save_pattern(
        payload.project_id, payload.session_id, payload.name,
        payload.code_snippet, payload.language, payload.description, payload.tags
    )


@app.get("/patterns/{project_id}")
def get_patterns(project_id: int, language: str = None, tag: str = None):
    return db.get_patterns(project_id, language, tag)


@app.get("/rules/{project_id}")
def get_rules(project_id: int):
    return db.get_rules(project_id)


@app.post("/rules")
def add_rule(payload: RuleCreate):
    return db.add_rule(payload.project_id, payload.category, payload.rule, payload.priority)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=7842)
