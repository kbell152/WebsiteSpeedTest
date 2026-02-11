import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_DB_PATH = Path("data/webperf.sqlite3")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            label TEXT,
            platform TEXT,
            host TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            strategy TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            run_note TEXT,
            performance_score REAL,
            fcp_ms REAL,
            lcp_ms REAL,
            tbt_ms REAL,
            cls REAL,
            speed_index_ms REAL,
            ttfb_ms REAL,
            warning_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            host_notes_json TEXT,
            cache_litespeed TEXT,
            cache_control TEXT,
            lcp_element_snippet TEXT,
            lcp_resource_url TEXT,
            lcp_ttfb_ms REAL,
            lcp_load_delay_ms REAL,
            lcp_load_time_ms REAL,
            lcp_render_delay_ms REAL,
            raw_json TEXT NOT NULL,
            FOREIGN KEY(site_id) REFERENCES sites(id)
        );

        CREATE TABLE IF NOT EXISTS run_todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            audit_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            score REAL,
            impact_ms REAL,
            priority REAL,
            FOREIGN KEY(run_id) REFERENCES audit_runs(id)
        );
        """
    )
    _ensure_column(conn, "audit_runs", "run_note", "TEXT")
    _ensure_column(conn, "audit_runs", "cache_litespeed", "TEXT")
    _ensure_column(conn, "audit_runs", "cache_control", "TEXT")
    _ensure_column(conn, "audit_runs", "lcp_element_snippet", "TEXT")
    _ensure_column(conn, "audit_runs", "lcp_resource_url", "TEXT")
    _ensure_column(conn, "audit_runs", "lcp_ttfb_ms", "REAL")
    _ensure_column(conn, "audit_runs", "lcp_load_delay_ms", "REAL")
    _ensure_column(conn, "audit_runs", "lcp_load_time_ms", "REAL")
    _ensure_column(conn, "audit_runs", "lcp_render_delay_ms", "REAL")
    conn.commit()


def _ensure_column(
    conn: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    columns = {row["name"] for row in rows}
    if column in columns:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    return value.rstrip("/")


def upsert_site(conn: sqlite3.Connection, url: str, label: Optional[str] = None) -> int:
    normalized = normalize_url(url)
    if not normalized:
        raise ValueError("Site URL cannot be empty")

    row = conn.execute("SELECT id FROM sites WHERE url = ?", (normalized,)).fetchone()
    if row:
        return int(row["id"])

    cur = conn.execute(
        """
        INSERT INTO sites (url, label, platform, host, active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """,
        (normalized, label, "wordpress/divi", None, utc_now_iso()),
    )
    conn.commit()
    return int(cur.lastrowid)


def import_sites(conn: sqlite3.Connection, lines: Iterable[str]) -> int:
    created = 0
    for raw in lines:
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        before = conn.total_changes
        upsert_site(conn, raw)
        if conn.total_changes > before:
            created += 1
    return created


def list_sites(conn: sqlite3.Connection, active_only: bool = True) -> List[sqlite3.Row]:
    if active_only:
        return conn.execute(
            "SELECT id, url, label, active, created_at FROM sites WHERE active = 1 ORDER BY url"
        ).fetchall()
    return conn.execute(
        "SELECT id, url, label, active, created_at FROM sites ORDER BY url"
    ).fetchall()


def get_site(conn: sqlite3.Connection, url: str) -> sqlite3.Row:
    normalized = normalize_url(url)
    row = conn.execute("SELECT * FROM sites WHERE url = ?", (normalized,)).fetchone()
    if not row:
        raise ValueError(f"Site not found: {normalized}")
    return row


def insert_run(
    conn: sqlite3.Connection,
    *,
    site_id: int,
    strategy: str,
    run_note: Optional[str],
    metrics: Dict[str, Any],
    warning_count: int,
    error_count: int,
    host_notes: Dict[str, Any],
    raw_payload: Dict[str, Any],
    cache_litespeed: Optional[str] = None,
    cache_control: Optional[str] = None,
    lcp_element_snippet: Optional[str] = None,
    lcp_resource_url: Optional[str] = None,
    lcp_ttfb_ms: Optional[float] = None,
    lcp_load_delay_ms: Optional[float] = None,
    lcp_load_time_ms: Optional[float] = None,
    lcp_render_delay_ms: Optional[float] = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO audit_runs (
            site_id, strategy, fetched_at, run_note, performance_score,
            fcp_ms, lcp_ms, tbt_ms, cls, speed_index_ms, ttfb_ms,
            warning_count, error_count, host_notes_json, raw_json, cache_litespeed, cache_control,
            lcp_element_snippet, lcp_resource_url,
            lcp_ttfb_ms, lcp_load_delay_ms, lcp_load_time_ms, lcp_render_delay_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            site_id,
            strategy,
            utc_now_iso(),
            run_note,
            metrics.get("performance_score"),
            metrics.get("fcp_ms"),
            metrics.get("lcp_ms"),
            metrics.get("tbt_ms"),
            metrics.get("cls"),
            metrics.get("speed_index_ms"),
            metrics.get("ttfb_ms"),
            warning_count,
            error_count,
            json.dumps(host_notes),
            json.dumps(raw_payload),
            cache_litespeed,
            cache_control,
            lcp_element_snippet,
            lcp_resource_url,
            lcp_ttfb_ms,
            lcp_load_delay_ms,
            lcp_load_time_ms,
            lcp_render_delay_ms,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def replace_run_todos(
    conn: sqlite3.Connection, run_id: int, todos: List[Dict[str, Any]]
) -> None:
    conn.execute("DELETE FROM run_todos WHERE run_id = ?", (run_id,))
    conn.executemany(
        """
        INSERT INTO run_todos (run_id, audit_id, title, description, category, score, impact_ms, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                run_id,
                t["audit_id"],
                t["title"],
                t.get("description"),
                t.get("category"),
                t.get("score"),
                t.get("impact_ms"),
                t.get("priority"),
            )
            for t in todos
        ],
    )
    conn.commit()


def get_latest_run(
    conn: sqlite3.Connection, site_id: int, strategy: str = "mobile"
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM audit_runs
        WHERE site_id = ? AND strategy = ?
        ORDER BY fetched_at DESC
        LIMIT 1
        """,
        (site_id, strategy),
    ).fetchone()


def get_previous_run(
    conn: sqlite3.Connection,
    site_id: int,
    strategy: str = "mobile",
    before_fetched_at: str = "",
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM audit_runs
        WHERE site_id = ? AND strategy = ? AND fetched_at < ?
        ORDER BY fetched_at DESC
        LIMIT 1
        """,
        (site_id, strategy, before_fetched_at),
    ).fetchone()


def get_run_todos(
    conn: sqlite3.Connection, run_id: int, limit: int = 20
) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT audit_id, title, description, category, score, impact_ms, priority
        FROM run_todos
        WHERE run_id = ?
        ORDER BY priority DESC
        LIMIT ?
        """,
        (run_id, limit),
    ).fetchall()


def get_recent_runs(
    conn: sqlite3.Connection, site_id: int, strategy: str, limit: int = 10
) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM audit_runs
        WHERE site_id = ? AND strategy = ?
        ORDER BY fetched_at DESC
        LIMIT ?
        """,
        (site_id, strategy, limit),
    ).fetchall()
