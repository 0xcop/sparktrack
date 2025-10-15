import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sparktrack.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        owner_id INTEGER NOT NULL,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS issues(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        assignee_id INTEGER,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(assignee_id) REFERENCES users(id)
    );""")
    conn.commit()
    conn.close()
