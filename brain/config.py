import os
import json
from pathlib import Path


def get_db_path() -> str:
    config_path = Path('.skynet-config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get('db_path', 'skynet.db')
    return 'skynet.db'


def get_project_id() -> int:
    config_path = Path('.skynet-config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get('project_id', 1)
    return 1
