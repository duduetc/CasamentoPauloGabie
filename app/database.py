import sqlite3
import json
import os
import unicodedata
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "wedding.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def normalize_name(s: str) -> str:
    """Normaliza um nome removendo acentos e convertendo para minúsculas para busca flexível."""
    if not s:
        return ""
    # Remove acentos
    s = "".join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    return s.lower().strip()

def init_db():
    """Cria a tabela do banco de dados e adiciona dados iniciais se estiver vazia."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rsvp_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                max_guests INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'confirmed', 'declined'
                confirmed_count INTEGER DEFAULT 0,
                confirmed_names TEXT, -- JSON string de lista de nomes
                declined_reason TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()

        # Verifica se já existem dados
        cursor.execute("SELECT COUNT(*) FROM rsvp_groups")
        if cursor.fetchone()[0] == 0:
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
                "INSERT INTO rsvp_groups (name, max_guests) VALUES (?, ?)",
                seed_data
            )
            conn.commit()

def search_groups(query: str):
    """Busca convites cujo nome seja similar à busca utilizando normalização em Python."""
    normalized_query = normalize_name(query)
    if not normalized_query:
        return []

    results = []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsvp_groups")
        rows = cursor.fetchall()
        for row in rows:
            normalized_db_name = normalize_name(row["name"])
            if normalized_query in normalized_db_name:
                group = dict(row)
                if group["confirmed_names"]:
                    group["confirmed_names"] = json.loads(group["confirmed_names"])
                else:
                    group["confirmed_names"] = []
                results.append(group)
    return results

def get_group_by_id(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsvp_groups WHERE id = ?", (group_id,))
        row = cursor.fetchone()
        if row:
            group = dict(row)
            if group["confirmed_names"]:
                group["confirmed_names"] = json.loads(group["confirmed_names"])
            else:
                group["confirmed_names"] = []
            return group
        return None

def update_group_rsvp(group_id: int, status: str, confirmed_count: int, confirmed_names: list, declined_reason: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        updated_at = datetime.now().isoformat()
        names_json = json.dumps(confirmed_names, ensure_ascii=False)
        cursor.execute(
            """
            UPDATE rsvp_groups
            SET status = ?, confirmed_count = ?, confirmed_names = ?, declined_reason = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, confirmed_count, names_json, declined_reason, updated_at, group_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_all_groups(search_query: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if search_query:
            # Carrega todos e filtra por normalização para a lista do admin também ser robusta
            normalized_query = normalize_name(search_query)
            cursor.execute("SELECT * FROM rsvp_groups ORDER BY name")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                if normalized_query in normalize_name(row["name"]):
                    group = dict(row)
                    group["confirmed_names"] = json.loads(group["confirmed_names"]) if group["confirmed_names"] else []
                    results.append(group)
            return results
        else:
            cursor.execute("SELECT * FROM rsvp_groups ORDER BY name")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                group = dict(row)
                group["confirmed_names"] = json.loads(group["confirmed_names"]) if group["confirmed_names"] else []
                results.append(group)
            return results

def add_group(name: str, max_guests: int):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO rsvp_groups (name, max_guests) VALUES (?, ?)",
                (name.strip(), max_guests)
            )
            conn.commit()
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Este nome de convite já existe."

def update_group(group_id: int, name: str, max_guests: int):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE rsvp_groups SET name = ?, max_guests = ? WHERE id = ?",
                (name.strip(), max_guests, group_id)
            )
            conn.commit()
            return True, "Convite atualizado com sucesso."
        except sqlite3.IntegrityError:
            return False, "Este nome de convite já está em uso."

def reset_group_rsvp(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rsvp_groups
            SET status = 'pending', confirmed_count = 0, confirmed_names = NULL, declined_reason = NULL, updated_at = NULL
            WHERE id = ?
            """,
            (group_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

def delete_group(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rsvp_groups WHERE id = ?", (group_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total de convites cadastrados
        cursor.execute("SELECT COUNT(*) FROM rsvp_groups")
        total_invitations = cursor.fetchone()[0]
        
        # Total de convidados possíveis (capacidade máxima de todos os convites)
        cursor.execute("SELECT SUM(max_guests) FROM rsvp_groups")
        total_max_guests = cursor.fetchone()[0] or 0
        
        # Confirmados
        cursor.execute("SELECT SUM(confirmed_count) FROM rsvp_groups WHERE status = 'confirmed'")
        total_confirmed = cursor.fetchone()[0] or 0
        
        # Recusados (quantidade de convites que recusaram)
        cursor.execute("SELECT COUNT(*) FROM rsvp_groups WHERE status = 'declined'")
        total_declined_invitations = cursor.fetchone()[0]
        
        # Total de pessoas em convites recusados
        cursor.execute("SELECT SUM(max_guests) FROM rsvp_groups WHERE status = 'declined'")
        total_declined_guests = cursor.fetchone()[0] or 0

        # Pendentes (convites sem resposta)
        cursor.execute("SELECT COUNT(*) FROM rsvp_groups WHERE status = 'pending'")
        pending_invitations = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(max_guests) FROM rsvp_groups WHERE status = 'pending'")
        pending_guests = cursor.fetchone()[0] or 0

        return {
            "total_invitations": total_invitations,
            "total_max_guests": total_max_guests,
            "total_confirmed": total_confirmed,
            "total_declined_invitations": total_declined_invitations,
            "total_declined_guests": total_declined_guests,
            "pending_invitations": pending_invitations,
            "pending_guests": pending_guests
        }
