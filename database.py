import sqlite3
from datetime import date, timedelta, datetime

DB_NAME = "data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY,
            username        TEXT,
            full_name       TEXT,
            group_name      TEXT,
            points          INTEGER DEFAULT 0,
            coins           INTEGER DEFAULT 0,
            streak          INTEGER DEFAULT 0,
            daily_streak    INTEGER DEFAULT 0,
            last_date       TEXT,
            last_daily_test TEXT,
            total_steps     INTEGER DEFAULT 0,
            total_run_km    REAL DEFAULT 0,
            test_score      INTEGER DEFAULT 0
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS run_points (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            lat         REAL,
            lon         REAL,
            created_at  TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            question     TEXT,
            option_a     TEXT,
            option_b     TEXT,
            option_c     TEXT,
            correct      TEXT,
            category     TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            correct      INTEGER,
            total        INTEGER,
            date         TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            item_code   TEXT,
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


def add_run_point(user_id, lat, lon):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO run_points (user_id, lat, lon, created_at) VALUES (?, ?, ?, ?)",
        (user_id, lat, lon, date.today().isoformat()),
    )
    conn.commit()
    conn.close()


def get_run_points(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT lat, lon, created_at FROM run_points WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def add_question(question, a, b, c, correct, category="Общее"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO questions (question, option_a, option_b, option_c, correct, category) VALUES (?, ?, ?, ?, ?, ?)",
        (question, a, b, c, correct, category),
    )
    conn.commit()
    conn.close()


def get_questions(limit=5):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, question, option_a, option_b, option_c, correct FROM questions ORDER BY RANDOM() LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def save_quiz_result(user_id, correct, total):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO quiz_results (user_id, correct, total, date) VALUES (?, ?, ?, ?)",
        (user_id, correct, total, date.today().isoformat()),
    )
    conn.commit()
    conn.close()


def get_last_quiz_results(user_id, limit=5):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT correct, total, date FROM quiz_results WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def count_questions():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    count = cur.fetchone()[0]
    conn.close()
    return count


# ===== ВАЛЮТА =====
def add_coins(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def get_coins(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def spend_coins(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row or row[0] < amount:
        conn.close()
        return False
    cur.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return True


def can_do_daily_test(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT last_daily_test FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return True, 0

    last = datetime.fromisoformat(row[0])
    now = datetime.now()
    diff = now - last
    if diff.total_seconds() >= 86400:
        return True, 0
    hours_left = 24 - int(diff.total_seconds() / 3600)
    return False, hours_left


def mark_daily_test_done(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT daily_streak, last_daily_test FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return

    daily_streak, last = row

    if last:
        last_date = datetime.fromisoformat(last).date()
        today = date.today()
        diff = (today - last_date).days

        if diff == 1:
            daily_streak += 1
        elif diff > 1:
            daily_streak = 1
    else:
        daily_streak = 1

    cur.execute(
        "UPDATE users SET daily_streak = ?, last_daily_test = ? WHERE user_id = ?",
        (daily_streak, date.today().isoformat(), user_id),
    )
    conn.commit()
    conn.close()


def get_daily_streak(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT daily_streak FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def add_purchase(user_id, item_code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO purchases (user_id, item_code, date) VALUES (?, ?, ?)",
        (user_id, item_code, date.today().isoformat()),
    )
    conn.commit()
    conn.close()


def get_purchases(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT item_code FROM purchases WHERE user_id = ?", (user_id,))
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows
