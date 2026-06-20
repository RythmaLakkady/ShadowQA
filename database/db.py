import sqlite3
import hashlib

DB_FILE = "shadowqa.db"

def get_connection():
    """Helper to prevent Streamlit cross-thread crashing."""
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    """Initializes the SQLite database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Test Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            vulnerability_rate REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Test Results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            test_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status_code INTEGER,
            response_time_ms REAL,
            result_status TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES test_sessions(id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    """Simple, clean SHA-256 password hashing to avoid heavy external binary dependencies."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def save_test_session(user_id, target_url, timestamp_str, vulnerability_rate, executed_results):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO test_sessions (user_id, target_url, timestamp, vulnerability_rate) VALUES (?, ?, ?, ?)",
        (user_id, target_url, timestamp_str, vulnerability_rate)
    )
    session_id = cursor.lastrowid
    
    for res in executed_results:
        cursor.execute("""
            INSERT INTO test_results (session_id, test_type, payload, status_code, response_time_ms, result_status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, res['test_type'], res['payload'], res['status_code'], res['response_time_ms'], res['result_status']))
        
    conn.commit()
    conn.close()

def get_test_sessions(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, target_url, timestamp, vulnerability_rate FROM test_sessions WHERE user_id = ? ORDER BY id DESC", (user_id,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def get_test_results(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT test_type, payload, status_code, response_time_ms, result_status FROM test_results WHERE session_id = ?", (session_id,))
    details = cursor.fetchall()
    conn.close()
    return details