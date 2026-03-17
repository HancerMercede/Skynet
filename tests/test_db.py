import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_create_schema(db):
    conn = db._get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['projects', 'rules', 'sessions', 'memory', 'tasks', 'decisions', 'errors_log', 'patterns']
    for table in expected_tables:
        assert table in tables


def test_create_project(db):
    result = db.create_project('My Project', 'Description', '["python"]')
    assert result['name'] == 'My Project'


def test_get_project(db, project_id):
    project = db.get_project(project_id)
    assert project is not None
    assert project['name'] == 'Test Project'
    assert project['status'] == 'active'


def test_remember_upsert(db, project_id):
    db.remember(project_id, None, 'insight', 'test_key', 'test_value', 0.8)
    
    memories = db.recall(project_id, type='insight')
    assert len(memories) == 1
    assert memories[0]['key'] == 'test_key'
    assert memories[0]['value'] == 'test_value'
    
    db.remember(project_id, None, 'insight', 'test_key', 'updated_value', 0.9)
    
    memories = db.recall(project_id, type='insight')
    assert len(memories) == 1
    assert memories[0]['value'] == 'updated_value'


def test_recall_with_filters(db, project_id):
    db.remember(project_id, None, 'insight', 'key1', 'value1', 0.9, '["tag1"]')
    db.remember(project_id, None, 'insight', 'key2', 'value2', 0.5, '["tag2"]')
    db.remember(project_id, None, 'config', 'key3', 'value3', 0.7)
    
    results = db.recall(project_id, type='insight')
    assert len(results) == 2
    
    results = db.recall(project_id, tag='tag1')
    assert len(results) == 1
    assert results[0]['key'] == 'key1'
    
    results = db.recall(project_id, search='value2')
    assert len(results) == 1
    assert results[0]['key'] == 'key2'


def test_forget(db, project_id):
    db.remember(project_id, None, 'insight', 'to_delete', 'value', 0.5)
    
    result = db.forget(project_id, 'to_delete')
    assert result['deleted'] == True
    
    memories = db.recall(project_id, search='to_delete')
    assert len(memories) == 0


def test_session_lifecycle(db, project_id):
    session = db.start_session(project_id, 'test-agent', 'Complete the task')
    session_id = session['id']
    assert session['status'] == 'active'
    assert session['goal'] == 'Complete the task'
    
    retrieved = db.get_session(session_id)
    assert retrieved is not None
    
    closed = db.close_session(session_id, 'Task completed successfully')
    assert closed['status'] == 'completed'
    assert closed['summary'] == 'Task completed successfully'


def test_task_operations(db, project_id):
    session = db.start_session(project_id, 'agent', 'test')
    session_id = session['id']
    
    task = db.add_task(project_id, session_id, 'Test task', 'Description', 8)
    task_id = task['id']
    assert task['title'] == 'Test task'
    assert task['priority'] == 8
    assert task['status'] == 'pending'
    
    tasks = db.get_tasks(project_id, status='pending')
    assert len(tasks) == 1
    
    updated = db.update_task(task_id, status='in_progress')
    assert updated['status'] == 'in_progress'
    
    tasks = db.get_tasks(project_id, status='pending')
    assert len(tasks) == 0
    
    done = db.update_task(task_id, status='done')
    assert done['status'] == 'done'
    assert done['completed_at'] is not None


def test_error_logging(db, project_id):
    session = db.start_session(project_id, 'agent', 'test')
    session_id = session['id']
    
    error = db.log_error(project_id, session_id, 'Division by zero', 'In calculate function', 'main.py')
    error_id = error['id']
    assert error['resolved'] == False
    
    resolved = db.resolve_error(error_id, 'Added zero check')
    assert resolved['resolved'] == True
    assert resolved['solution'] == 'Added zero check'
    
    errors = db.get_errors(project_id, resolved=False)
    assert len(errors) == 0
    
    errors = db.get_errors(project_id, resolved=True)
    assert len(errors) == 1


def test_decisions(db, project_id):
    session = db.start_session(project_id, 'agent', 'test')
    session_id = session['id']
    
    decision = db.add_decision(
        project_id, session_id,
        'Use SQLite',
        'Need a portable database',
        'SQLite',
        '["PostgreSQL", "MongoDB"]',
        'Single file, no setup'
    )
    assert decision['chosen'] == 'SQLite'
    
    decisions = db.get_decisions(project_id)
    assert len(decisions) == 1


def test_patterns(db, project_id):
    session = db.start_session(project_id, 'agent', 'test')
    session_id = session['id']
    
    pattern = db.save_pattern(
        project_id, session_id,
        'JWT Auth',
        'def authenticate(): pass',
        'python',
        'Auth pattern',
        '["auth", "jwt"]'
    )
    assert pattern['language'] == 'python'
    
    patterns = db.get_patterns(project_id)
    assert len(patterns) == 1
    
    patterns = db.get_patterns(project_id, language='python')
    assert len(patterns) == 1


def test_rules(db, project_id):
    rule1 = db.add_rule(project_id, 'code', 'Use type hints', 8)
    rule2 = db.add_rule(project_id, 'style', '4 spaces indent', 6)
    
    rules = db.get_rules(project_id)
    assert len(rules) == 2
    assert rules[0]['priority'] == 8
    assert rules[0]['category'] == 'code'


def test_get_full_context(db, project_id):
    db.add_rule(project_id, 'code', 'Use type hints', 7)
    
    session = db.start_session(project_id, 'agent', 'test goal')
    session_id = session['id']
    
    task1 = db.add_task(project_id, session_id, 'Task 1', priority=9)
    task2 = db.add_task(project_id, session_id, 'Task 2', priority=5)
    
    updated = db.update_task(task1['id'], status='in_progress')
    
    db.remember(project_id, session_id, 'insight', 'important', 'value', 0.9)
    db.remember(project_id, session_id, 'config', 'setting', 'value', 0.3)
    
    db.log_error(project_id, session_id, 'Error', 'context')
    
    context = db.get_full_context(project_id)
    
    assert context['project']['name'] == 'Test Project'
    assert len(context['active_tasks']) == 1
    assert len(context['pending_tasks']) == 1
    assert len(context['top_memory']) == 1
    assert len(context['rules']) == 1
    assert len(context['open_errors']) == 1
