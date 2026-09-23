import sqlite3
from datetime import date, timedelta

DB_NAME = "data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            points      INTEGER DEFAULT 0,
            streak      INTEGER DEFAULT 0,
            last_date   TEXT,
            total_steps INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            code        TEXT,
            date        TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def create_user(user_id, username, full_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
        (user_id, username, full_name),
    )
    conn.commit()
    conn.close()


def add_steps(user_id, steps):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT points, streak, last_date, total_steps FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    points, streak, last_date, total_steps = row
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if last_date == today:
        pass
    elif last_date == yesterday:
        streak += 1
    else:
        streak = 1

    earned = max(steps // 100, 5)
    points += earned
    total_steps += steps

    cur.execute(
        "UPDATE users SET points = ?, streak = ?, last_date = ?, total_steps = ? WHERE user_id = ?",
        (points, streak, today, total_steps, user_id),
    )
    conn.commit()
    conn.close()
    return earned, points, streak


def get_top(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT full_name, points, streak FROM users ORDER BY points DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def add_achievement(user_id, code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO achievements (user_id, code, date) VALUES (?, ?, ?)",
        (user_id, code, date.today().isoformat()),
    )
    conn.commit()
    conn.close()


def get_achievements(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT code FROM achievements WHERE user_id = ?", (user_id,))
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows
