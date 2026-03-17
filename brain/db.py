import sqlite3
from typing import Optional, List, Dict, Any
import os

DEFAULT_BRAIN_DIR = os.path.join(os.path.expanduser("~"), ".brain")
DEFAULT_DB_PATH = os.path.join(DEFAULT_BRAIN_DIR, "skynet.db")


class BrainDB:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_conn(self):
        return self._connect()

    def _init_db(self):
        import os
        from pathlib import Path
        conn = self._connect()
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        table_exists = cursor.fetchone() is not None
        conn.close()
        
        if not table_exists:
            schema_path = Path(__file__).parent / 'schema.sql'
            with open(schema_path, 'r') as f:
                schema = f.read()
            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema)
            conn.close()

    def create_project(self, name: str, description: str = None, stack: str = None, repo_path: str = None) -> dict:
        conn = self._connect()
        cursor = conn.execute(
            '''INSERT INTO projects (name, description, stack, repo_path) VALUES (?, ?, ?, ?)''',
            (name, description, stack, repo_path)
        )
        conn.commit()
        conn.close()
        return {'id': cursor.lastrowid, 'name': name}

    def get_project(self, project_id: int) -> Optional[dict]:
        conn = self._connect()
        cursor = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_full_context(self, project_id: int) -> dict:
        conn = self._connect()
        
        cursor = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        project = cursor.fetchone()
        
        cursor = conn.execute(
            '''SELECT * FROM tasks WHERE project_id = ? AND status = 'in_progress' ORDER BY priority DESC''',
            (project_id,)
        )
        active_tasks = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute(
            '''SELECT * FROM tasks WHERE project_id = ? AND status = 'pending' ORDER BY priority DESC''',
            (project_id,)
        )
        pending_tasks = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute(
            '''SELECT * FROM tasks WHERE project_id = ? AND status = 'done' ORDER BY updated_at DESC''',
            (project_id,)
        )
        completed_tasks = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute(
            '''SELECT * FROM memory WHERE project_id = ? AND relevance > 0.6 ORDER BY relevance DESC''',
            (project_id,)
        )
        top_memory = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute(
            '''SELECT * FROM errors_log WHERE project_id = ? AND resolved = 0 ORDER BY created_at DESC''',
            (project_id,)
        )
        open_errors = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute(
            '''SELECT * FROM rules WHERE project_id = ? ORDER BY priority DESC''',
            (project_id,)
        )
        rules = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute(
            '''SELECT * FROM sessions WHERE project_id = ? ORDER BY started_at DESC LIMIT 1''',
            (project_id,)
        )
        last_session = cursor.fetchone()
        
        conn.close()
        
        return {
            'project': dict(project) if project else None,
            'active_tasks': active_tasks,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'top_memory': top_memory,
            'open_errors': open_errors,
            'rules': rules,
            'last_session': dict(last_session) if last_session else None
        }

    def start_session(self, project_id: int, agent_id: str, goal: str) -> dict:
        conn = self._connect()
        cursor = conn.execute(
            '''INSERT INTO sessions (project_id, agent_id, goal) VALUES (?, ?, ?)''',
            (project_id, agent_id, goal)
        )
        conn.commit()
        conn.close()
        return {'id': cursor.lastrowid, 'project_id': project_id, 'agent_id': agent_id, 'goal': goal, 'status': 'active'}

    def close_session(self, session_id: int, summary: str) -> dict:
        conn = self._connect()
        conn.execute(
            '''UPDATE sessions SET status = 'completed', summary = ?, ended_at = CURRENT_TIMESTAMP WHERE id = ?''',
            (summary, session_id)
        )
        conn.commit()
        cursor = conn.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_session(self, session_id: int) -> Optional[dict]:
        conn = self._connect()
        cursor = conn.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def remember(self, project_id: int, session_id: Optional[int], type: str, key: str, value: str, relevance: float = 0.5, tags: str = None) -> dict:
        conn = self._connect()
        conn.execute(
            '''INSERT OR REPLACE INTO memory (project_id, session_id, type, key, value, relevance, tags, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
            (project_id, session_id, type, key, value, relevance, tags)
        )
        conn.commit()
        conn.close()
        return {'key': key, 'type': type, 'relevance': relevance}

    def recall(self, project_id: int, type: str = None, tag: str = None, search: str = None, limit: int = 10) -> List[dict]:
        conn = self._connect()
        query = 'SELECT * FROM memory WHERE project_id = ?'
        params = [project_id]
        
        if type:
            query += ' AND type = ?'
            params.append(type)
        
        if search:
            query += ' AND (key LIKE ? OR value LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if tag and tag != '':
            query += ' AND tags LIKE ?'
            params.append(f'%{tag}%')
        
        query += ' ORDER BY relevance DESC LIMIT ?'
        params.append(limit)
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def forget(self, project_id: int, key: str) -> dict:
        conn = self._connect()
        cursor = conn.execute('DELETE FROM memory WHERE project_id = ? AND key = ?', (project_id, key))
        conn.commit()
        conn.close()
        return {'key': key, 'deleted': cursor.rowcount > 0}

    def add_task(self, project_id: int, session_id: Optional[int], title: str, description: str = None, priority: int = 5) -> dict:
        conn = self._connect()
        cursor = conn.execute(
            '''INSERT INTO tasks (project_id, session_id, title, description, priority) VALUES (?, ?, ?, ?, ?)''',
            (project_id, session_id, title, description, priority)
        )
        conn.commit()
        conn.close()
        return {'id': cursor.lastrowid, 'title': title, 'priority': priority, 'status': 'pending'}

    def update_task(self, task_id: int, status: str = None, notes: str = None) -> dict:
        conn = self._connect()
        updates = []
        params = []
        
        if status:
            updates.append('status = ?')
            params.append(status)
            if status == 'done':
                updates.append('completed_at = CURRENT_TIMESTAMP')
        
        if notes:
            updates.append('notes = ?')
            params.append(notes)
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(task_id)
            conn.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
        
        cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_tasks(self, project_id: int, status: str = None, priority: int = None) -> List[dict]:
        conn = self._connect()
        query = 'SELECT * FROM tasks WHERE project_id = ?'
        params = [project_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        query += ' ORDER BY priority DESC, created_at DESC'
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def log_error(self, project_id: int, session_id: Optional[int], error: str, context: str = None, file_path: str = None) -> dict:
        conn = self._connect()
        cursor = conn.execute(
            '''INSERT INTO errors_log (project_id, session_id, error, context, file_path) VALUES (?, ?, ?, ?, ?)''',
            (project_id, session_id, error, context, file_path)
        )
        conn.commit()
        conn.close()
        return {'id': cursor.lastrowid, 'error': error, 'resolved': False}

    def resolve_error(self, error_id: int, solution: str) -> dict:
        conn = self._connect()
        conn.execute(
            '''UPDATE errors_log SET resolved = 1, solution = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?''',
            (solution, error_id)
        )
        conn.commit()
        cursor = conn.execute('SELECT * FROM errors_log WHERE id = ?', (error_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_errors(self, project_id: int, resolved: bool = None) -> List[dict]:
        conn = self._connect()
        query = 'SELECT * FROM errors_log WHERE project_id = ?'
        params = [project_id]
        
        if resolved is not None:
            query += ' AND resolved = ?'
            params.append(1 if resolved else 0)
        
        query += ' ORDER BY created_at DESC'
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_decision(self, project_id: int, session_id: Optional[int], title: str, context: str, chosen: str, alternatives: str = None, consequences: str = None) -> dict:
        conn = self._connect()
        cursor = conn.execute(
            '''INSERT INTO decisions (project_id, session_id, title, context, chosen, alternatives, consequences) VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (project_id, session_id, title, context, chosen, alternatives, consequences)
        )
        conn.commit()
        conn.close()
        return {'id': cursor.lastrowid, 'title': title, 'chosen': chosen}

    def get_decisions(self, project_id: int) -> List[dict]:
        conn = self._connect()
        cursor = conn.execute('SELECT * FROM decisions WHERE project_id = ? ORDER BY created_at DESC', (project_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def save_pattern(self, project_id: int, session_id: Optional[int], name: str, code_snippet: str, language: str, description: str = None, tags: str = None) -> dict:
        conn = self._connect()
        cursor = conn.execute(
            '''INSERT INTO patterns (project_id, session_id, name, description, code_snippet, language, tags) VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (project_id, session_id, name, description, code_snippet, language, tags)
        )
        conn.commit()
        conn.close()
        return {'id': cursor.lastrowid, 'name': name, 'language': language}

    def get_patterns(self, project_id: int, language: str = None, tag: str = None) -> List[dict]:
        conn = self._connect()
        query = 'SELECT * FROM patterns WHERE project_id = ?'
        params = [project_id]
        
        if language:
            query += ' AND language = ?'
            params.append(language)
        
        if tag and tag != '':
            query += ' AND tags LIKE ?'
            params.append(f'%{tag}%')
        
        query += ' ORDER BY created_at DESC'
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_rules(self, project_id: int) -> List[dict]:
        conn = self._connect()
        cursor = conn.execute('SELECT * FROM rules WHERE project_id = ? ORDER BY priority DESC', (project_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_rule(self, project_id: int, category: str, rule: str, priority: int = 5) -> dict:
        conn = self._connect()
        cursor = conn.execute(
            '''INSERT INTO rules (project_id, category, rule, priority) VALUES (?, ?, ?, ?)''',
            (project_id, category, rule, priority)
        )
        conn.commit()
        conn.close()
        return {'id': cursor.lastrowid, 'category': category, 'rule': rule, 'priority': priority}
