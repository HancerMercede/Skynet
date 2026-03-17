import json
from mcp.server.fastmcp import FastMCP
from brain.db import BrainDB
import os

mcp = FastMCP("project-brain")

db = BrainDB()


@mcp.tool()
def brain_get_context(project_id: int) -> dict:
    """Retorna el contexto completo del proyecto: estado, tasks activas, memoria de alta relevancia, reglas y último error sin resolver. Llamar SIEMPRE al inicio de cada sesión."""
    return db.get_full_context(project_id)


@mcp.tool()
def brain_start_session(project_id: int, agent_id: str, goal: str) -> dict:
    """Inicia nueva sesión con goal declarado. Retorna session_id."""
    return db.start_session(project_id, agent_id, goal)


@mcp.tool()
def brain_close_session(session_id: int, summary: str) -> dict:
    """Cierra sesión con summary. Llamar siempre al terminar."""
    return db.close_session(session_id, summary)


@mcp.tool()
def brain_remember(project_id: int, session_id: int, type: str, key: str, value: str, relevance: float = 0.5, tags: str = None) -> dict:
    """Guarda memoria clave-valor con tipo y relevancia."""
    return db.remember(project_id, session_id, type, key, value, relevance, tags)


@mcp.tool()
def brain_recall(project_id: int, type: str = None, tag: str = None, search: str = None, limit: int = 10) -> list:
    """Busca memorias por tipo, tag o texto. Retorna top N por relevancia."""
    return db.recall(project_id, type, tag, search, limit)


@mcp.tool()
def brain_forget(project_id: int, key: str) -> dict:
    """Elimina o reduce relevancia de una memoria obsoleta."""
    return db.forget(project_id, key)


@mcp.tool()
def brain_add_task(project_id: int, session_id: int, title: str, description: str = None, priority: int = 5) -> dict:
    """Crea tarea con título, descripción y prioridad."""
    return db.add_task(project_id, session_id, title, description, priority)


@mcp.tool()
def brain_update_task(task_id: int, status: str = None, notes: str = None) -> dict:
    """Actualiza status o notes de una tarea existente."""
    return db.update_task(task_id, status, notes)


@mcp.tool()
def brain_get_tasks(project_id: int, status: str = None, priority: int = None) -> list:
    """Retorna tasks filtradas por status y/o prioridad."""
    return db.get_tasks(project_id, status, priority)


@mcp.tool()
def brain_log_error(project_id: int, session_id: int, error: str, context: str = None, file_path: str = None) -> dict:
    """Registra error con contexto. Evita repetir errores ya conocidos."""
    return db.log_error(project_id, session_id, error, context, file_path)


@mcp.tool()
def brain_resolve_error(error_id: int, solution: str) -> dict:
    """Marca error como resuelto y guarda la solución."""
    return db.resolve_error(error_id, solution)


@mcp.tool()
def brain_add_decision(project_id: int, session_id: int, title: str, context: str, chosen: str, alternatives: str = None, consequences: str = None) -> dict:
    """Registra ADR: qué se decidió y por qué."""
    return db.add_decision(project_id, session_id, title, context, chosen, alternatives, consequences)


@mcp.tool()
def brain_save_pattern(project_id: int, session_id: int, name: str, code_snippet: str, language: str, description: str = None, tags: str = None) -> dict:
    """Guarda snippet reutilizable con nombre y tags."""
    return db.save_pattern(project_id, session_id, name, code_snippet, language, description, tags)


@mcp.tool()
def brain_get_rules(project_id: int) -> list:
    """Retorna reglas del proyecto ordenadas por prioridad."""
    return db.get_rules(project_id)


if __name__ == '__main__':
    mcp.run()
