from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import json


@dataclass
class Project:
    id: int
    name: str
    description: Optional[str] = None
    status: str = 'active'
    stack: Optional[str] = None
    repo_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def stack_list(self) -> list:
        if self.stack:
            return json.loads(self.stack)
        return []


@dataclass
class Rule:
    id: int
    project_id: int
    category: str
    rule: str
    priority: int = 5
    created_at: Optional[str] = None


@dataclass
class Session:
    id: int
    project_id: int
    agent_id: str
    goal: str
    summary: Optional[str] = None
    status: str = 'active'
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


@dataclass
class Memory:
    id: int
    project_id: int
    session_id: Optional[int] = None
    type: str = ''
    key: str = ''
    value: str = ''
    relevance: float = 0.5
    tags: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def tags_list(self) -> list:
        if self.tags:
            return json.loads(self.tags)
        return []


@dataclass
class Task:
    id: int
    project_id: int
    session_id: Optional[int] = None
    title: str = ''
    description: Optional[str] = None
    status: str = 'pending'
    priority: int = 5
    notes: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Decision:
    id: int
    project_id: int
    session_id: Optional[int] = None
    title: str = ''
    context: str = ''
    chosen: str = ''
    alternatives: Optional[str] = None
    consequences: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def alternatives_list(self) -> list:
        if self.alternatives:
            return json.loads(self.alternatives)
        return []


@dataclass
class ErrorLog:
    id: int
    project_id: int
    session_id: Optional[int] = None
    error: str = ''
    context: Optional[str] = None
    solution: Optional[str] = None
    file_path: Optional[str] = None
    resolved: bool = False
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None


@dataclass
class Pattern:
    id: int
    project_id: int
    session_id: Optional[int] = None
    name: str = ''
    description: Optional[str] = None
    code_snippet: str = ''
    language: str = ''
    tags: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def tags_list(self) -> list:
        if self.tags:
            return json.loads(self.tags)
        return []


@dataclass
class FullContext:
    project: dict
    active_tasks: list
    pending_tasks: list
    top_memory: list
    open_errors: list
    rules: list
    last_session: Optional[dict] = None
