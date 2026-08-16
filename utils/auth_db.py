import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "users.db")


def init_db():
    """Create the users and quiz_results tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT,
            score INTEGER,
            feedback TEXT,
            questions TEXT,
            answers TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    """)
    conn.commit()
    conn.close()


def register_user(username, password):
    """Add a new user. Returns (success: bool, message: str)."""
    if not username or not password:
        return False, "Username and password cannot be empty."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists."
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return True, "Account created! You can now log in."


def check_login(username, password):
    """Check credentials. Returns True if valid."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == password:
        return True
    return False


def save_quiz_result(
    username: str,
    topic: str,
    difficulty: str,
    score: Optional[int],
    feedback: str,
    questions: List[str],
    answers: List[str],
) -> bool:
    """
    Save a completed quiz result to the database.

    Args:
        username (str): The logged-in user's username.
        topic (str): The quiz topic.
        difficulty (str): The quiz difficulty.
        score (Optional[int]): The numeric score out of 100 (None if not parsed).
        feedback (str): The full markdown feedback text.
        questions (List[str]): The 10 questions.
        answers (List[str]): The 10 candidate answers.

    Returns:
        bool: True if saved successfully.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        questions_str = "\n---\n".join(questions)
        answers_str = "\n---\n".join(answers)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO quiz_results (username, topic, difficulty, score, feedback, questions, answers, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (username, topic, difficulty, score, feedback, questions_str, answers_str, date_str),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_user_quiz_history(username: str) -> List[Dict]:
    """
    Retrieve all past quiz results for a user, most recent first.

    Args:
        username (str): The logged-in user's username.

    Returns:
        List[Dict]: A list of quiz result records.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, topic, difficulty, score, feedback, date
        FROM quiz_results
        WHERE username = ?
        ORDER BY date DESC
        """,
        (username,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]