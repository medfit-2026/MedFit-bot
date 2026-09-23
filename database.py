import sqlite3
from datetime import date, timedelta

DB_NAME = "data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT,
            full_name     TEXT,
            group_name    TEXT,
            points        INTEGER DEFAULT 0,
            streak        INTEGER DEFAULT 0,
            last_date     TEXT,
            total_steps   INTEGER DEFAULT 0,
            total_run_km  REAL DEFAULT 0,
            test_score    INTEGER DEFAULT 0
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


def set_group(user_id, group_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE users SET group_name = ? WHERE user_id = ?", (group_name, user_id))
    conn.commit()
    conn.close()


def get_top_by_group(group_name, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT full_name, points, streak FROM users WHERE group_name = ? ORDER BY points DESC LIMIT ?",
        (group_name, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


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


def add_run(user_id, km):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT points, total_run_km, streak, last_date FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    points, total_run, streak, last_date = row
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if last_date == today:
        pass
    elif last_date == yesterday:
        streak += 1
    else:
        streak = 1

    earned = int(km * 20)
    points += earned
    total_run += km

    cur.execute(
        "UPDATE users SET points = ?, total_run_km = ?, streak = ?, last_date = ? WHERE user_id = ?",
        (points, total_run, streak, today, user_id),
    )
    conn.commit()
    conn.close()
    return earned, points, total_run


def add_test(user_id, test_name, score):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    points = row[0]
    bonus = score * 50
    points += bonus

    cur.execute(
        "UPDATE users SET points = ?, test_score = test_score + ? WHERE user_id = ?",
        (points, score, user_id),
    )
    conn.commit()
    conn.close()
    return bonus, points


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
