import pytest
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain.db import BrainDB


@pytest.fixture(scope="session", autouse=True)
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    database = BrainDB(db_path=path)
    
    import server.rest_api
    server.rest_api.db = database
    
    import server.mcp_server
    server.mcp_server.db = database
    
    yield database
    
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient
    import server.rest_api
    return TestClient(server.rest_api.app)


@pytest.fixture
def project_id(db):
    result = db.create_project('Test Project')
    return result['id']
