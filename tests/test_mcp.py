import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_brain_get_context(db, project_id):
    context = db.get_full_context(project_id)
    assert 'project' in context
    assert 'active_tasks' in context
    assert 'pending_tasks' in context
    assert 'top_memory' in context
    assert 'open_errors' in context
    assert 'rules' in context


def test_brain_start_session(db, project_id):
    session = db.start_session(project_id, 'test-agent', 'Complete the task')
    assert 'id' in session
    assert session['project_id'] == project_id
    assert session['agent_id'] == 'test-agent'
    assert session['goal'] == 'Complete the task'


def test_brain_close_session(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    session_id = session['id']
    
    closed = db.close_session(session_id, 'summary')
    assert closed['status'] == 'completed'
    assert closed['summary'] == 'summary'


def test_brain_remember(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    result = db.remember(project_id, session['id'], 'insight', 'key', 'value', 0.8)
    assert result['key'] == 'key'
    assert result['relevance'] == 0.8


def test_brain_recall(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    db.remember(project_id, session['id'], 'insight', 'key', 'value', 0.8)
    
    results = db.recall(project_id)
    assert len(results) >= 1


def test_brain_forget(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    db.remember(project_id, session['id'], 'insight', 'key', 'value')
    
    result = db.forget(project_id, 'key')
    assert result['deleted'] == True


def test_brain_add_task(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    task = db.add_task(project_id, session['id'], 'New task', 'description', 7)
    assert task['title'] == 'New task'
    assert task['priority'] == 7


def test_brain_update_task(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    task = db.add_task(project_id, session['id'], 'Task')
    
    updated = db.update_task(task['id'], status='in_progress', notes='Working on it')
    assert updated['status'] == 'in_progress'
    assert updated['notes'] == 'Working on it'


def test_brain_get_tasks(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    db.add_task(project_id, session['id'], 'Task 1', priority=8)
    db.add_task(project_id, session['id'], 'Task 2', priority=5)
    
    tasks = db.get_tasks(project_id)
    assert len(tasks) == 2
    
    tasks = db.get_tasks(project_id, priority=8)
    assert len(tasks) == 1


def test_brain_log_error(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    error = db.log_error(project_id, session['id'], 'Error message', 'context', 'file.py')
    assert error['error'] == 'Error message'
    assert error['resolved'] == False


def test_brain_resolve_error(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    error = db.log_error(project_id, session['id'], 'Error')
    
    resolved = db.resolve_error(error['id'], 'Solution')
    assert resolved['resolved'] == True
    assert resolved['solution'] == 'Solution'


def test_brain_add_decision(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    decision = db.add_decision(
        project_id, session['id'],
        'Title', 'Context', 'Chosen'
    )
    assert decision['chosen'] == 'Chosen'


def test_brain_save_pattern(db, project_id):
    session = db.start_session(project_id, 'agent', 'goal')
    pattern = db.save_pattern(
        project_id, session['id'],
        'Name', 'code', 'python'
    )
    assert pattern['language'] == 'python'


def test_brain_get_rules(db, project_id):
    db.add_rule(project_id, 'cat1', 'rule1', 5)
    db.add_rule(project_id, 'cat2', 'rule2', 8)
    
    rules = db.get_rules(project_id)
    assert len(rules) == 2
    assert rules[0]['priority'] == 8
