import argparse
import json
import os
import sys
import sqlite3
import subprocess
import signal
from pathlib import Path


DEFAULT_BRAIN_DIR = os.path.join(os.path.expanduser("~"), ".brain")
DEFAULT_DB_PATH = os.path.join(DEFAULT_BRAIN_DIR, "skynet.db")
PID_FILE = os.path.join(DEFAULT_BRAIN_DIR, "brain.pid")
LOG_FILE = os.path.join(DEFAULT_BRAIN_DIR, "brain.log")


def get_schema_path() -> Path:
    return Path(__file__).parent.parent / 'brain' / 'schema.sql'


def init_project(name: str, stack: str, project_path: str = None, git_ignore: bool = False):
    target_path = Path(project_path) if project_path else Path.cwd()
    db_path = target_path / 'skynet.db'
    
    if db_path.exists():
        print(f"Error: skynet.db already exists at {db_path}")
        sys.exit(1)
    
    schema_path = get_schema_path()
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    conn = sqlite3.connect(str(db_path))
    conn.executescript(schema)
    
    stack_json = json.dumps(stack.split(',')) if stack else '[]'
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO projects (name, stack) VALUES (?, ?)',
        (name, stack_json)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    config = {
        'db_path': str(db_path),
        'project_id': project_id,
        'mcp_server_cmd': 'python -m server.mcp_server',
        'rest_api_url': 'http://localhost:7842'
    }
    
    config_path = target_path / '.skynet-config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    if git_ignore:
        gitignore_path = target_path / '.gitignore'
        existing = ''
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing = f.read()
        
        if 'skynet.db' not in existing:
            with open(gitignore_path, 'a') as f:
                if existing and not existing.endswith('\n'):
                    f.write('\n')
                f.write('skynet.db\n')
    
    print(f"Project Brain initialized successfully!")
    print(f"  Database: {db_path}")
    print(f"  Project ID: {project_id}")
    print(f"  Config: {config_path}")
    print()
    print("To use with Claude Code/Cursor, add to your MCP config:")
    print(f'  {{"mcpServers": {{"project-brain": {{"command": "python", "args": ["-m", "server.mcp_server"], "cwd": "{target_path}"}}}}}}')
    print()
    print("To use REST API (for LangChain/AutoGen):")
    print(f"  Start server: python -m server.rest_api")
    print(f"  API URL: http://localhost:7842")


def show_status(project_path: str = None):
    target_path = Path(project_path) if project_path else Path.cwd()
    db_path = target_path / 'skynet.db'
    config_path = target_path / '.skynet-config.json'
    
    if not db_path.exists():
        print(f"Error: skynet.db not found at {db_path}")
        print("Run 'brain_init init' first to initialize Project Brain")
        sys.exit(1)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"Project ID: {config['project_id']}")
        print(f"Database: {config['db_path']}")
        print(f"MCP Server: {config['mcp_server_cmd']}")
        print(f"REST API: {config['rest_api_url']}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "pending"')
    pending = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "in_progress"')
    active = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM memory')
    memories = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM errors_log WHERE resolved = 0')
    open_errors = cursor.fetchone()[0]
    
    conn.close()
    
    print()
    print("Status:")
    print(f"  Pending tasks: {pending}")
    print(f"  Active tasks: {active}")
    print(f"  Memories: {memories}")
    print(f"  Open errors: {open_errors}")


def add_rule(category: str, rule: str, project_path: str = None, priority: int = 5):
    target_path = Path(project_path) if project_path else Path.cwd()
    db_path = target_path / 'skynet.db'
    config_path = target_path / '.skynet-config.json'
    
    if not db_path.exists():
        print(f"Error: skynet.db not found")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    project_id = config['project_id']
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO rules (project_id, category, rule, priority) VALUES (?, ?, ?, ?)',
        (project_id, category, rule, priority)
    )
    conn.commit()
    rule_id = cursor.lastrowid
    conn.close()
    
    print(f"Rule added (ID: {rule_id})")
    print(f"  Category: {category}")
    print(f"  Rule: {rule}")
    print(f"  Priority: {priority}")


def main():
    parser = argparse.ArgumentParser(description='Project Brain CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Service commands
    service_parser = subparsers.add_parser('service', help='Manage the Brain server process')
    service_subparsers = service_parser.add_subparsers(dest='service_command')
    
    start_parser = service_subparsers.add_parser('start', help='Start REST API server in background')
    stop_parser = service_subparsers.add_parser('stop', help='Stop the Brain server')
    service_status_parser = service_subparsers.add_parser('status', help='Show whether Brain server is running')
    install_parser = service_subparsers.add_parser('install', help='Print setup instructions')
    
    # MCP command
    mcp_parser = subparsers.add_parser('mcp', help='Start MCP server (stdio transport for Claude Code/Cursor)')
    
    # Existing commands
    init_parser = subparsers.add_parser('init', help='Initialize Project Brain')
    init_parser.add_argument('--name', required=True, help='Project name')
    init_parser.add_argument('--stack', help='Comma-separated stack (e.g., python,fastapi,postgres)')
    init_parser.add_argument('--path', help='Project path (default: current directory)')
    init_parser.add_argument('--git-ignore', action='store_true', help='Add skynet.db to .gitignore')
    
    status_parser = subparsers.add_parser('status', help='Show project status')
    status_parser.add_argument('--path', help='Project path')
    
    rule_parser = subparsers.add_parser('rule', help='Manage rules')
    rule_subparsers = rule_parser.add_subparsers(dest='rule_command')
    
    add_rule_parser = rule_subparsers.add_parser('add', help='Add a rule')
    add_rule_parser.add_argument('--category', required=True, help='Rule category')
    add_rule_parser.add_argument('--rule', required=True, help='Rule text')
    add_rule_parser.add_argument('--priority', type=int, default=5, help='Priority (1-10)')
    add_rule_parser.add_argument('--path', help='Project path')
    
    args = parser.parse_args()
    
    # Service commands
    if args.command == 'service':
        if args.service_command == 'start':
            os.makedirs(DEFAULT_BRAIN_DIR, exist_ok=True)
            if os.path.exists(PID_FILE):
                with open(PID_FILE) as f:
                    pid = int(f.read())
                try:
                    os.kill(pid, 0)
                    print(f"Brain already running (PID {pid})")
                    return
                except OSError:
                    pass
            
            log = open(LOG_FILE, "a")
            proc = subprocess.Popen(
                [sys.executable, "-m", "server.rest_api"],
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            with open(PID_FILE, "w") as f:
                f.write(str(proc.pid))
            print(f"Brain started (PID {proc.pid})")
            print(f"REST API -> http://localhost:7842")
            print(f"Logs     -> {LOG_FILE}")
            
        elif args.service_command == 'stop':
            if not os.path.exists(PID_FILE):
                print("Brain is not running.")
                return
            with open(PID_FILE) as f:
                pid = int(f.read())
            try:
                if os.name == "nt":
                    subprocess.call(["taskkill", "/F", "/PID", str(pid)])
                else:
                    os.kill(pid, signal.SIGTERM)
                os.remove(PID_FILE)
                print(f"Brain stopped (PID {pid})")
            except OSError:
                print("Process not found - removing stale PID file.")
                os.remove(PID_FILE)
                
        elif args.service_command == 'status':
            if not os.path.exists(PID_FILE):
                print("Brain is NOT running.")
                return
            with open(PID_FILE) as f:
                pid = int(f.read())
            try:
                if os.name == "nt":
                    result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
                    if str(pid) in result.stdout:
                        print(f"Brain is running (PID {pid})")
                        print(f"REST API -> http://localhost:7842")
                        print(f"MCP      -> brain mcp")
                    else:
                        print("Brain is NOT running (stale PID file).")
                        os.remove(PID_FILE)
                else:
                    os.kill(pid, 0)
                    print(f"Brain is running (PID {pid})")
                    print(f"REST API -> http://localhost:7842")
                    print(f"MCP      -> brain mcp")
            except OSError:
                print("Brain is NOT running (stale PID file).")
                os.remove(PID_FILE)
                
        elif args.service_command == 'install':
            brain_dir = DEFAULT_BRAIN_DIR
            print(f"""
Project Brain - global installation
-------------------------------------
Brain directory : {brain_dir}
Database        : {os.path.join(brain_dir, "skynet.db")}
Logs            : {LOG_FILE}

Add to your shell profile to auto-start:
  brain service start

MCP config for Claude Code (.claude/mcp.json):
{{
  "mcpServers": {{
    "skynet": {{
      "command": "brain",
      "args": ["mcp"]
    }}
  }}
}}
            """)
    
    elif args.command == 'mcp':
        from server.mcp_server import mcp as mcp_server
        mcp_server.run()
    
    if args.command == 'init':
        init_project(args.name, args.stack, args.path, args.git_ignore)
    elif args.command == 'status':
        show_status(args.path)
    elif args.command == 'rule' and args.rule_command == 'add':
        add_rule(args.category, args.rule, args.path, args.priority)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
