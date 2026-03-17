import sqlite3

old_db = 'C:/Users/HANCER MERCEDE/source/repos/BohucoPost/skynet.db'
new_db = 'C:/Users/HANCER MERCEDE/.brain/skynet.db'

old_conn = sqlite3.connect(old_db)
new_conn = sqlite3.connect(new_db)

# 1. Copy project
old_proj = old_conn.execute('SELECT name, description, status, stack, repo_path FROM projects WHERE id=1').fetchone()
new_conn.execute('INSERT INTO projects (name, description, status, stack, repo_path) VALUES (?,?,?,?,?)', 
    (old_proj[0], old_proj[1], old_proj[2], old_proj[3], old_proj[4]))
new_conn.commit()
new_project_id = new_conn.execute('SELECT last_insert_rowid()').fetchone()[0]
print(f'Project copied as ID: {new_project_id}')

# 2. Copy rules
old_rules = old_conn.execute('SELECT category, rule, priority FROM rules').fetchall()
for r in old_rules:
    new_conn.execute('INSERT INTO rules (project_id, category, rule, priority) VALUES (?,?,?,?)', 
        (new_project_id, r[0], r[1], r[2]))
new_conn.commit()
print(f'Rules copied: {len(old_rules)}')

# 3. Copy memory
old_mem = old_conn.execute('SELECT session_id, type, key, value, relevance, tags FROM memory').fetchall()
for m in old_mem:
    new_conn.execute('INSERT INTO memory (project_id, session_id, type, key, value, relevance, tags) VALUES (?,?,?,?,?,?,?)',
        (new_project_id, m[0], m[1], m[2], m[3], m[4], m[5]))
new_conn.commit()
print(f'Memories copied: {len(old_mem)}')

# 4. Copy tasks
old_tasks = old_conn.execute('SELECT session_id, title, description, status, priority, notes FROM tasks').fetchall()
for t in old_tasks:
    new_conn.execute('INSERT INTO tasks (project_id, session_id, title, description, status, priority, notes) VALUES (?,?,?,?,?,?,?)',
        (new_project_id, t[0], t[1], t[2], t[3], t[4], t[5]))
new_conn.commit()
print(f'Tasks copied: {len(old_tasks)}')

# Show results
print('\nNew project:', new_conn.execute('SELECT id, name FROM projects').fetchall())
print('Rules:', new_conn.execute('SELECT category, rule FROM rules').fetchall())
print('Memory:', new_conn.execute('SELECT key, type FROM memory').fetchall())

old_conn.close()
new_conn.close()
print('\nDone!')
