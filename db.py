import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sent_articles (
    url        TEXT PRIMARY KEY,
    source     TEXT NOT NULL,
    title      TEXT,
    sent_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sent_source ON sent_articles(source);

CREATE TABLE IF NOT EXISTS bot_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(_SCHEMA)


def is_sent(path: str, url: str) -> bool:
    with sqlite3.connect(path) as conn:
        cur = conn.execute("SELECT 1 FROM sent_articles WHERE url = ?", (url,))
        return cur.fetchone() is not None


def mark_sent(path: str, url: str, source: str, title: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_articles (url, source, title) VALUES (?, ?, ?)",
            (url, source, title),
        )


def count(path: str) -> int:
    with sqlite3.connect(path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM sent_articles")
        return cur.fetchone()[0]


def get_state(path: str, key: str) -> str | None:
    with sqlite3.connect(path) as conn:
        cur = conn.execute("SELECT value FROM bot_state WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None


def set_state(path: str, key: str, value: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO bot_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
