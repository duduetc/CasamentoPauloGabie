import os
import json
import sqlite3
import unicodedata
from datetime import datetime
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

DB_PATH = os.path.join(os.path.dirname(__file__), "wedding.db")


@contextmanager
def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _p(n=1):
    """Placeholder: %s para Postgres, ? para SQLite."""
    return "%s" if USE_POSTGRES else "?"


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
        if USE_POSTGRES:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rsvp_groups (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    max_guests INTEGER NOT NULL DEFAULT 1,
                    phone TEXT,
                    guest_names TEXT,
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
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rsvp_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    max_guests INTEGER NOT NULL DEFAULT 1,
                    phone TEXT,
                    guest_names TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    confirmed_count INTEGER DEFAULT 0,
                    confirmed_names TEXT,
                    declined_reason TEXT,
                    updated_at TEXT
                )
            """)
            # migrações de colunas novas
            for col_sql in [
                "ALTER TABLE rsvp_groups ADD COLUMN phone TEXT",
                "ALTER TABLE rsvp_groups ADD COLUMN guest_names TEXT",
            ]:
                try:
                    cursor.execute(col_sql)
                    conn.commit()
                except Exception:
                    pass
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gift_id INTEGER NOT NULL,
                    gift_name TEXT NOT NULL,
                    contributor_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    message TEXT,
                    confirmed_at TEXT NOT NULL
                )
            """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM rsvp_groups")
        row = cursor.fetchone()
        count = row["count"] if USE_POSTGRES else row[0]
        if count == 0:
            seed_data = [
                ("Cláudio e família", 4),
                ("Maria Silva", 1),
                ("José Santos e acompanhante", 2),
                ("Ana Souza e família", 3),
                ("Família Oliveira", 5),
                ("Carlos Eduardo", 1),
                ("Mariana e Ricardo", 2),
            ]
            ph = _p()
            cursor.executemany(
                f"INSERT INTO rsvp_groups (name, max_guests) VALUES ({ph}, {ph})",
                seed_data,
            )
            conn.commit()


# ── Contributions ─────────────────────────────────────────────────────────────

def add_contribution(gift_id: int, gift_name: str, contributor_name: str, amount: float, message: str = "") -> int:
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute(
                f"INSERT INTO contributions (gift_id, gift_name, contributor_name, amount, message, confirmed_at) VALUES ({ph},{ph},{ph},{ph},{ph},{ph}) RETURNING id",
                (gift_id, gift_name, contributor_name, amount, message or None, datetime.now().isoformat()),
            )
            row_id = cursor.fetchone()["id"]
        else:
            cursor.execute(
                f"INSERT INTO contributions (gift_id, gift_name, contributor_name, amount, message, confirmed_at) VALUES ({ph},{ph},{ph},{ph},{ph},{ph})",
                (gift_id, gift_name, contributor_name, amount, message or None, datetime.now().isoformat()),
            )
            row_id = cursor.lastrowid
        conn.commit()
        return row_id


def remove_contribution(gift_id: int, amount: float, gift_name: str = "", contributor_name: str = "Ajuste administrativo", message: str = "Remoção administrativa") -> bool:
    amount = float(amount)
    if amount <= 0:
        return False

    totals = get_all_contributions_totals()
    current_total = float(totals.get(gift_id, 0.0))
    if amount > current_total + 1e-9:
        return False

    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute(
                f"INSERT INTO contributions (gift_id, gift_name, contributor_name, amount, message, confirmed_at) VALUES ({ph},{ph},{ph},{ph},{ph},{ph})",
                (gift_id, gift_name or "", contributor_name, -amount, message or None, datetime.now().isoformat()),
            )
        else:
            cursor.execute(
                f"INSERT INTO contributions (gift_id, gift_name, contributor_name, amount, message, confirmed_at) VALUES ({ph},{ph},{ph},{ph},{ph},{ph})",
                (gift_id, gift_name or "", contributor_name, -amount, message or None, datetime.now().isoformat()),
            )
        conn.commit()
    return True


def get_all_contributions_totals() -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT gift_id, COALESCE(SUM(amount), 0) AS total FROM contributions GROUP BY gift_id")
        rows = cursor.fetchall()
    return {(row["gift_id"] if USE_POSTGRES else row[0]): float(row["total"] if USE_POSTGRES else row[1]) for row in rows}


# ── RSVP groups ───────────────────────────────────────────────────────────────

def _parse_group(row) -> dict:
    group = dict(row)
    group["confirmed_names"] = json.loads(group["confirmed_names"]) if group["confirmed_names"] else []
    group["guest_names"] = json.loads(group["guest_names"]) if group.get("guest_names") else []
    group["matched_guest_name"] = None
    return group


def _group_matches_query(group: dict, query: str) -> tuple[bool, str | None]:
    normalized_query = normalize_name(query)
    if not normalized_query:
        return False, None

    stop_words = {"e", "de", "da", "do", "dos", "das", "com", "na", "no", "nas", "nos"}
    tokens = [token for token in normalized_query.split() if token and token not in stop_words]
    if not tokens:
        return False, None

    candidate_text = normalize_name(" ".join([group.get("name", ""), *group.get("guest_names", [])]))
    if not candidate_text:
        return False, None

    if normalized_query in candidate_text:
        for guest_name in group.get("guest_names", []):
            guest_normalized = normalize_name(guest_name)
            if guest_normalized and normalized_query in guest_normalized:
                return True, guest_name
        return True, None

    if all(token in candidate_text for token in tokens):
        for guest_name in group.get("guest_names", []):
            guest_normalized = normalize_name(guest_name)
            if not guest_normalized:
                continue

            if normalized_query in guest_normalized:
                return True, guest_name

            group_name = normalize_name(group.get("name", ""))
            combined_name_text = normalize_name(f"{group_name} {guest_normalized}")
            if len(tokens) > 1 and all(token in combined_name_text for token in tokens):
                return True, guest_name

        return True, None

    return False, None


def search_groups(query: str):
    normalized_query = normalize_name(query)
    if not normalized_query:
        return []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsvp_groups")
        rows = cursor.fetchall()

    results = []
    for row in rows:
        group = _parse_group(row)
        matches, matched_guest_name = _group_matches_query(group, query)
        if matches:
            group["matched_guest_name"] = matched_guest_name
            results.append(group)

    return results


def get_group_by_id(group_id: int):
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM rsvp_groups WHERE id = {ph}", (group_id,))
        row = cursor.fetchone()
    return _parse_group(row) if row else None


def update_group_rsvp(group_id: int, status: str, confirmed_count: int, confirmed_names: list, declined_reason: str = None):
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE rsvp_groups SET status={ph}, confirmed_count={ph}, confirmed_names={ph}, declined_reason={ph}, updated_at={ph} WHERE id={ph}",
            (status, confirmed_count, json.dumps(confirmed_names, ensure_ascii=False), declined_reason, datetime.now().isoformat(), group_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_all_groups(search_query: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsvp_groups ORDER BY name")
        rows = cursor.fetchall()

    parsed_groups = [_parse_group(r) for r in rows]
    if search_query:
        parsed_groups = [g for g in parsed_groups if _group_matches_query(g, search_query)[0]]
    return parsed_groups


def add_group(name: str, max_guests: int, phone: str = None, guest_names: list = None):
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"INSERT INTO rsvp_groups (name, max_guests, phone, guest_names) VALUES ({ph}, {ph}, {ph}, {ph})",
                (name.strip(), max_guests, phone or None, json.dumps(guest_names, ensure_ascii=False) if guest_names else None),
            )
            conn.commit()
            return True, cursor.lastrowid
        except Exception:
            conn.rollback()
            return False, "Este nome de convite já existe."


def add_groups_bulk(rows: list[dict]) -> tuple[int, int]:
    """Importa uma lista de {name, max_guests, phone, guest_names}. Retorna (inseridos, duplicados)."""
    inserted = 0
    duplicates = 0
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        for row in rows:
            try:
                gnames = row.get("guest_names") or []
                cursor.execute(
                    f"INSERT INTO rsvp_groups (name, max_guests, phone, guest_names) VALUES ({ph}, {ph}, {ph}, {ph})",
                    (row["name"].strip(), row["max_guests"], row.get("phone") or None,
                     json.dumps(gnames, ensure_ascii=False) if gnames else None),
                )
                conn.commit()
                inserted += 1
            except Exception:
                conn.rollback()
                duplicates += 1
    return inserted, duplicates


def update_group(group_id: int, name: str, max_guests: int, phone: str = None, guest_names: list = None):
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE rsvp_groups SET name={ph}, max_guests={ph}, phone={ph}, guest_names={ph} WHERE id={ph}",
                (name.strip(), max_guests, phone or None, json.dumps(guest_names, ensure_ascii=False) if guest_names else None, group_id),
            )
            conn.commit()
            return True, "Convite atualizado com sucesso."
        except Exception:
            conn.rollback()
            return False, "Este nome de convite já está em uso."


def reset_group_rsvp(group_id: int):
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE rsvp_groups SET status='pending', confirmed_count=0, confirmed_names=NULL, declined_reason=NULL, updated_at=NULL WHERE id={ph}",
            (group_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_group(group_id: int):
    ph = _p()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM rsvp_groups WHERE id={ph}", (group_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()

        def scalar(q):
            cursor.execute(q)
            row = cursor.fetchone()
            return list(row.values())[0] if USE_POSTGRES else row[0]

        return {
            "total_invitations":          scalar("SELECT COUNT(*) FROM rsvp_groups"),
            "total_max_guests":           scalar("SELECT COALESCE(SUM(max_guests),0) FROM rsvp_groups"),
            "total_confirmed":            scalar("SELECT COALESCE(SUM(confirmed_count),0) FROM rsvp_groups WHERE status='confirmed'"),
            "total_declined_invitations": scalar("SELECT COUNT(*) FROM rsvp_groups WHERE status='declined'"),
            "total_declined_guests":      scalar("SELECT COALESCE(SUM(max_guests),0) FROM rsvp_groups WHERE status='declined'"),
            "pending_invitations":        scalar("SELECT COUNT(*) FROM rsvp_groups WHERE status='pending'"),
            "pending_guests":             scalar("SELECT COALESCE(SUM(max_guests),0) FROM rsvp_groups WHERE status='pending'"),
        }
