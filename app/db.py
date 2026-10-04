"""Usage logging in SQL (SQLite here; swap for PostgreSQL/Azure SQL in production).
The JD asks for logging, usage tracking and session management - this is the seed of that."""
import sqlite3

from app.config import settings


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT, question TEXT, answer TEXT,
            top_score REAL, tokens INTEGER, latency_ms INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
    )
    return conn


def log_query(session_id: str, question: str, answer: str, top_score: float,
              tokens: int, latency_ms: int) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO queries (session_id, question, answer, top_score, tokens, latency_ms)"
            " VALUES (?,?,?,?,?,?)",
            (session_id, question, answer, top_score, tokens, latency_ms),
        )


def usage_summary() -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(tokens),0), COALESCE(AVG(latency_ms),0) FROM queries"
        ).fetchone()
    return {"queries": row[0], "total_tokens": row[1], "avg_latency_ms": round(row[2])}
