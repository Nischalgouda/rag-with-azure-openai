"""Usage logging in SQL (SQLite here; swap for PostgreSQL/Azure SQL in production).
It records every question with its token cost, which also powers the daily budget and per-caller
daily caps used in demo mode."""
import sqlite3
from datetime import datetime, timedelta, timezone

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
    # Lightweight migration for databases created before the `identity` column existed.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(queries)")}
    if "identity" not in columns:
        conn.execute("ALTER TABLE queries ADD COLUMN identity TEXT DEFAULT ''")
    return conn


def log_query(session_id: str, question: str, answer: str, top_score: float,
              tokens: int, latency_ms: int, identity: str = "") -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO queries (session_id, question, answer, top_score, tokens, latency_ms, identity)"
            " VALUES (?,?,?,?,?,?,?)",
            (session_id, question, answer, top_score, tokens, latency_ms, identity),
        )


def usage_summary() -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(tokens),0), COALESCE(AVG(latency_ms),0) FROM queries"
        ).fetchone()
    return {"queries": row[0], "total_tokens": row[1], "avg_latency_ms": round(row[2])}


# created_at is stored in UTC by SQLite's CURRENT_TIMESTAMP, so "today" means the current UTC day.
def questions_today(identity: str) -> int:
    with _conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM queries WHERE identity = ? AND date(created_at) = date('now')",
            (identity,),
        ).fetchone()[0]


def tokens_today() -> int:
    with _conn() as conn:
        return conn.execute(
            "SELECT COALESCE(SUM(tokens), 0) FROM queries WHERE date(created_at) = date('now')"
        ).fetchone()[0]


def seconds_until_utc_midnight(now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((midnight - now).total_seconds()))
