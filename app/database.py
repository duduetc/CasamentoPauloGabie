import os
import json
import unicodedata
from datetime import datetime
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def normalize_name(s: str) -> str:
    if not s:
        return ""
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    return s.lower().strip()


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rsvp_groups (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                max_guests INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'pending',
                confirmed_count INTEGER DEFAULT 0,
                confirmed_names TEXT,
                declined_reason TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contributions (
                id SERIAL PRIMARY KEY,
                gift_id INTEGER NOT NULL,
                gift_name TEXT NOT NULL,
                contributor_name TEXT NOT NULL,
                amount NUMERIC(10,2) NOT NULL,
                message TEXT,
                confirmed_at TEXT NOT NULL
            )
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM rsvp_groups")
        if cursor.fetchone()["count"] == 0:
            seed_data = [
                ("Cláudio e família", 4),
                ("Maria Silva", 1),
                ("José Santos e acompanhante", 2),
                ("Ana Souza e família", 3),
                ("Família Oliveira", 5),
                ("Carlos Eduardo", 1),
                ("Mariana e Ricardo", 2),
            ]
            cursor.executemany(
                "INSERT INTO rsvp_groups (name, max_guests) VALUES (%s, %s)",
                seed_data,
            )
            conn.commit()


# ── Contributions ─────────────────────────────────────────────────────────────

def add_contribution(gift_id: int, gift_name: str, contributor_name: str, amount: float, message: str = "") -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contributions (gift_id, gift_name, contributor_name, amount, message, confirmed_at)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (gift_id, gift_name, contributor_name, amount, message or None, datetime.now().isoformat()),
        )
        row_id = cursor.fetchone()["id"]
        conn.commit()
        return row_id


def get_all_contributions_totals() -> dict:
    """Retorna {gift_id: total_contribuido} para todos os presentes."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT gift_id, COALESCE(SUM(amount), 0) AS total FROM contributions GROUP BY gift_id")
        return {row["gift_id"]: float(row["total"]) for row in cursor.fetchall()}


# ── RSVP groups ───────────────────────────────────────────────────────────────

def _parse_group(row: dict) -> dict:
    group = dict(row)
    group["confirmed_names"] = json.loads(group["confirmed_names"]) if group["confirmed_names"] else []
    return group


def search_groups(query: str):
    normalized_query = normalize_name(query)
    if not normalized_query:
        return []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsvp_groups")
        rows = cursor.fetchall()
    return [
        _parse_group(row) for row in rows
        if normalized_query in normalize_name(row["name"])
    ]


def get_group_by_id(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsvp_groups WHERE id = %s", (group_id,))
        row = cursor.fetchone()
    return _parse_group(row) if row else None


def update_group_rsvp(group_id: int, status: str, confirmed_count: int, confirmed_names: list, declined_reason: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rsvp_groups
            SET status = %s, confirmed_count = %s, confirmed_names = %s,
                declined_reason = %s, updated_at = %s
            WHERE id = %s
            """,
            (status, confirmed_count, json.dumps(confirmed_names, ensure_ascii=False),
             declined_reason, datetime.now().isoformat(), group_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_all_groups(search_query: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsvp_groups ORDER BY name")
        rows = cursor.fetchall()
    if search_query:
        normalized = normalize_name(search_query)
        rows = [r for r in rows if normalized in normalize_name(r["name"])]
    return [_parse_group(r) for r in rows]


def add_group(name: str, max_guests: int):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO rsvp_groups (name, max_guests) VALUES (%s, %s)",
                (name.strip(), max_guests),
            )
            conn.commit()
            return True, cursor.lastrowid
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return False, "Este nome de convite já existe."


def update_group(group_id: int, name: str, max_guests: int):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE rsvp_groups SET name = %s, max_guests = %s WHERE id = %s",
                (name.strip(), max_guests, group_id),
            )
            conn.commit()
            return True, "Convite atualizado com sucesso."
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return False, "Este nome de convite já está em uso."


def reset_group_rsvp(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rsvp_groups
            SET status = 'pending', confirmed_count = 0, confirmed_names = NULL,
                declined_reason = NULL, updated_at = NULL
            WHERE id = %s
            """,
            (group_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_group(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rsvp_groups WHERE id = %s", (group_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM rsvp_groups")
        total_invitations = cursor.fetchone()["count"]

        cursor.execute("SELECT COALESCE(SUM(max_guests), 0) FROM rsvp_groups")
        total_max_guests = cursor.fetchone()["coalesce"]

        cursor.execute("SELECT COALESCE(SUM(confirmed_count), 0) FROM rsvp_groups WHERE status = 'confirmed'")
        total_confirmed = cursor.fetchone()["coalesce"]

        cursor.execute("SELECT COUNT(*) FROM rsvp_groups WHERE status = 'declined'")
        total_declined_invitations = cursor.fetchone()["count"]

        cursor.execute("SELECT COALESCE(SUM(max_guests), 0) FROM rsvp_groups WHERE status = 'declined'")
        total_declined_guests = cursor.fetchone()["coalesce"]

        cursor.execute("SELECT COUNT(*) FROM rsvp_groups WHERE status = 'pending'")
        pending_invitations = cursor.fetchone()["count"]

        cursor.execute("SELECT COALESCE(SUM(max_guests), 0) FROM rsvp_groups WHERE status = 'pending'")
        pending_guests = cursor.fetchone()["coalesce"]

    return {
        "total_invitations": total_invitations,
        "total_max_guests": total_max_guests,
        "total_confirmed": total_confirmed,
        "total_declined_invitations": total_declined_invitations,
        "total_declined_guests": total_declined_guests,
        "pending_invitations": pending_invitations,
        "pending_guests": pending_guests,
    }
