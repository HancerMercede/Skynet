import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_get_context_endpoint(client, project_id):
    response = client.get(f"/context/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert 'project' in data
    assert 'active_tasks' in data


def test_start_session_endpoint(client, project_id):
    response = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "test-agent",
        "goal": "Complete task"
    })
    assert response.status_code == 200
    data = response.json()
    assert data['project_id'] == project_id
    assert data['goal'] == 'Complete task'


def test_close_session_endpoint(client, project_id):
    start_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = start_resp.json()['id']
    
    response = client.patch(f"/sessions/{session_id}", json={
        "summary": "Done"
    })
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'completed'
    assert data['summary'] == 'Done'


def test_remember_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    response = client.post("/memory", json={
        "project_id": project_id,
        "session_id": session_id,
        "type": "insight",
        "key": "test_key",
        "value": "test_value",
        "relevance": 0.8
    })
    assert response.status_code == 200
    data = response.json()
    assert data['key'] == 'test_key'


def test_recall_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    client.post("/memory", json={
        "project_id": project_id,
        "session_id": session_id,
        "type": "insight",
        "key": "key1",
        "value": "value1",
        "relevance": 0.9
    })
    
    response = client.get(f"/memory/{project_id}?type=insight")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_forget_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    client.post("/memory", json={
        "project_id": project_id,
        "session_id": session_id,
        "type": "test",
        "key": "to_delete",
        "value": "value"
    })
    
    response = client.delete(f"/memory/{project_id}/to_delete")
    assert response.status_code == 200
    data = response.json()
    assert data['deleted'] == True


def test_add_task_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    response = client.post("/tasks", json={
        "project_id": project_id,
        "session_id": session_id,
        "title": "New Task",
        "description": "Description",
        "priority": 8
    })
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'New Task'
    assert data['priority'] == 8


def test_update_task_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    task_resp = client.post("/tasks", json={
        "project_id": project_id,
        "session_id": session_id,
        "title": "Task"
    })
    task_id = task_resp.json()['id']
    
    response = client.patch(f"/tasks/{task_id}", json={
        "status": "in_progress",
        "notes": "Working"
    })
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'in_progress'
    assert data['notes'] == 'Working'


def test_get_tasks_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    client.post("/tasks", json={
        "project_id": project_id,
        "session_id": session_id,
        "title": "Task1",
        "priority": 8
    })
    client.post("/tasks", json={
        "project_id": project_id,
        "session_id": session_id,
        "title": "Task2",
        "priority": 5
    })
    
    response = client.get(f"/tasks/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_log_error_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    response = client.post("/errors", json={
        "project_id": project_id,
        "session_id": session_id,
        "error": "Error message",
        "context": "context",
        "file_path": "file.py"
    })
    assert response.status_code == 200
    data = response.json()
    assert data['error'] == 'Error message'


def test_resolve_error_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    error_resp = client.post("/errors", json={
        "project_id": project_id,
        "session_id": session_id,
        "error": "Error"
    })
    error_id = error_resp.json()['id']
    
    response = client.patch(f"/errors/{error_id}", json={
        "solution": "Fixed"
    })
    assert response.status_code == 200
    data = response.json()
    assert data['resolved'] == True
    assert data['solution'] == 'Fixed'


def test_add_decision_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    response = client.post("/decisions", json={
        "project_id": project_id,
        "session_id": session_id,
        "title": "Decision",
        "context": "Context",
        "chosen": "Chosen option"
    })
    assert response.status_code == 200
    data = response.json()
    assert data['chosen'] == 'Chosen option'


def test_save_pattern_endpoint(client, project_id):
    session_resp = client.post("/sessions", json={
        "project_id": project_id,
        "agent_id": "agent",
        "goal": "goal"
    })
    session_id = session_resp.json()['id']
    
    response = client.post("/patterns", json={
        "project_id": project_id,
        "session_id": session_id,
        "name": "Pattern",
        "code_snippet": "code",
        "language": "python"
    })
    assert response.status_code == 200
    data = response.json()
    assert data['language'] == 'python'


def test_get_rules_endpoint(client, project_id):
    response = client.get(f"/rules/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_add_rule_endpoint(client, project_id):
    response = client.post("/rules", json={
        "project_id": project_id,
        "category": "code",
        "rule": "Use type hints",
        "priority": 8
    })
    assert response.status_code == 200
    data = response.json()
    assert data['category'] == 'code'
    assert data['priority'] == 8
