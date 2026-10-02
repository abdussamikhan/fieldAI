import os
import sqlite3
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import bcrypt

from core.config import config

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
SEED_PATH = Path(__file__).resolve().parent.parent / "db" / "seed.sql"
DB_FILE = Path(__file__).resolve().parent.parent / "fieldai.db"

class Database:
    def __init__(self):
        self.is_pg = config.is_postgres()
        self._pg_pool = None
        if self.is_pg:
            try:
                from psycopg_pool import ConnectionPool
                self._pg_pool = ConnectionPool(conninfo=config.DATABASE_URL, min_size=1, max_size=10)
            except Exception as e:
                print(f"[DB] PostgreSQL pool initialization failed: {e}. Falling back to SQLite.")
                self.is_pg = False

    def get_connection(self):
        if self.is_pg and self._pg_pool:
            return self._pg_pool.getconn()
        else:
            conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn

    def release_connection(self, conn):
        if self.is_pg and self._pg_pool:
            self._pg_pool.putconn(conn)
        else:
            conn.close()

    def _convert_query_to_sqlite(self, query: str) -> str:
        # Replace %s with ? for sqlite parameter substitution
        # Note: only replace %s not inside quotes
        q = re.sub(r'%s', '?', query)
        # SQLite doesn't support RETURNING in older versions, but Python 3.11+ SQLite 3.35+ does support RETURNING
        return q

    def execute(self, query: str, params: tuple = ()) -> int:
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            if not self.is_pg:
                query = self._convert_query_to_sqlite(query)
            cur.execute(query, params)
            conn.commit()
            rowcount = cur.rowcount
            cur.close()
            return rowcount
        finally:
            self.release_connection(conn)

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            if self.is_pg:
                if "RETURNING" not in query.upper():
                    query = query.rstrip("; \n") + " RETURNING id;"
                cur.execute(query, params)
                res = cur.fetchone()
                last_id = res[0] if res else 0
            else:
                query = self._convert_query_to_sqlite(query)
                cur.execute(query, params)
                last_id = cur.lastrowid
            conn.commit()
            cur.close()
            return last_id
        finally:
            self.release_connection(conn)

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            if not self.is_pg:
                query = self._convert_query_to_sqlite(query)
            cur.execute(query, params)
            if self.is_pg:
                colnames = [desc[0] for desc in cur.description] if cur.description else []
                rows = [dict(zip(colnames, row)) for row in cur.fetchall()]
            else:
                rows = [dict(row) for row in cur.fetchall()]
            cur.close()
            return rows
        finally:
            self.release_connection(conn)

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        rows = self.fetch_all(query, params)
        return rows[0] if rows else None

    def init_db(self):
        """Initializes database schema and seeds reference data if not present."""
        if not self.is_pg:
            # Prepare schema statements for SQLite
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            # Adapt Postgres-specific types for SQLite
            sqlite_schema = schema_sql
            sqlite_schema = re.sub(r'\bSERIAL PRIMARY KEY\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', sqlite_schema, flags=re.IGNORECASE)
            sqlite_schema = re.sub(r'\bBYTEA\b', 'BLOB', sqlite_schema, flags=re.IGNORECASE)

            conn = self.get_connection()
            try:
                conn.executescript(sqlite_schema)
                conn.commit()
            finally:
                self.release_connection(conn)
        else:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn = self.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                conn.commit()
            finally:
                self.release_connection(conn)

        # Check if sampling_table has seed data
        count_res = self.fetch_one("SELECT COUNT(*) as cnt FROM sampling_table;")
        if count_res and count_res.get("cnt", 0) == 0:
            print("[DB] Seeding reference data...")
            with open(SEED_PATH, "r", encoding="utf-8") as f:
                seed_sql = f.read()

            conn = self.get_connection()
            try:
                if not self.is_pg:
                    conn.executescript(seed_sql)
                    conn.commit()
                else:
                    with conn.cursor() as cur:
                        cur.execute(seed_sql)
                    conn.commit()
            finally:
                self.release_connection(conn)

        # Ensure default Admin user exists
        admin = self.fetch_one("SELECT id FROM users WHERE username = %s;", (config.ADMIN_USERNAME,))
        if not admin:
            pw_hash = bcrypt.hashpw(config.ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            self.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (%s, %s, %s, %s);",
                (config.ADMIN_USERNAME, pw_hash, "Admin", True)
            )
            print(f"[DB] Default admin user '{config.ADMIN_USERNAME}' created.")

db = Database()
