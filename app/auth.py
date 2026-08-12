from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


class AuthError(ValueError):
    pass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    name: str
    email_verified: bool
    workspace_id: int | None


class AuthStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        raw = db_path or os.getenv("NEXUS_AUTH_DB", "data/auth.db")
        self.db_path = Path(raw)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    email_verified INTEGER NOT NULL DEFAULT 0,
                    verification_token TEXT,
                    reset_token TEXT,
                    reset_expires INTEGER
                );
                CREATE TABLE IF NOT EXISTS workspaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    owner_id INTEGER NOT NULL,
                    purpose TEXT,
                    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
                    FOREIGN KEY(owner_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS memberships (
                    user_id INTEGER NOT NULL,
                    workspace_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    PRIMARY KEY(user_id, workspace_id),
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _password_hash(password: str, salt: bytes | None = None) -> str:
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
        return f"{salt.hex()}${digest.hex()}"

    @staticmethod
    def _password_matches(password: str, encoded: str) -> bool:
        salt_hex, digest_hex = encoded.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310_000)
        return hmac.compare_digest(actual.hex(), digest_hex)

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def create_user(self, email: str, name: str, password: str) -> tuple[User, str]:
        email = self._normalize_email(email)
        name = name.strip()
        if len(password) < 8:
            raise AuthError("password must be at least 8 characters")
        if not email or "@" not in email or not name:
            raise AuthError("valid email and name are required")
        token = secrets.token_urlsafe(32)
        conn = self._connect()
        try:
            try:
                cur = conn.execute("INSERT INTO users(email,name,password_hash,verification_token) VALUES(?,?,?,?)", (email, name, self._password_hash(password), token))
            except sqlite3.IntegrityError as exc:
                raise AuthError("email already registered") from exc
            user_id = cur.lastrowid
            conn.commit()
            return User(user_id, email, name, False, None), token
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> User | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE email=?", (self._normalize_email(email),)).fetchone()
            if not row:
                return None
            return User(row["id"], row["email"], row["name"], bool(row["email_verified"]), self._workspace_id(conn, row["id"]))
        finally:
            conn.close()

    def verify_email(self, token: str) -> User:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE verification_token=?", (token,)).fetchone()
            if not row:
                raise AuthError("invalid verification token")
            conn.execute("UPDATE users SET email_verified=1, verification_token=NULL WHERE id=?", (row["id"],))
            conn.commit()
            return User(row["id"], row["email"], row["name"], True, self._workspace_id(conn, row["id"]))
        finally:
            conn.close()

    def authenticate(self, email: str, password: str) -> User:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE email=?", (self._normalize_email(email),)).fetchone()
            if not row or not self._password_matches(password, row["password_hash"]):
                raise AuthError("invalid email or password")
            if not row["email_verified"]:
                raise AuthError("email verification required")
            return User(row["id"], row["email"], row["name"], True, self._workspace_id(conn, row["id"]))
        finally:
            conn.close()

    def request_password_reset(self, email: str) -> str:
        token = secrets.token_urlsafe(32)
        conn = self._connect()
        try:
            conn.execute("UPDATE users SET reset_token=?, reset_expires=? WHERE email=?", (token, int(time.time()) + 3600, self._normalize_email(email)))
            conn.commit()
            return token
        finally:
            conn.close()

    def reset_password(self, token: str, password: str) -> None:
        if len(password) < 8:
            raise AuthError("password must be at least 8 characters")
        conn = self._connect()
        try:
            row = conn.execute("SELECT id FROM users WHERE reset_token=? AND reset_expires>?", (token, int(time.time()))).fetchone()
            if not row:
                raise AuthError("invalid or expired reset token")
            conn.execute("UPDATE users SET password_hash=?, reset_token=NULL, reset_expires=NULL WHERE id=?", (self._password_hash(password), row["id"]))
            conn.execute("DELETE FROM sessions WHERE user_id=?", (row["id"],))
            conn.commit()
        finally:
            conn.close()

    def create_session(self, user_id: int, ttl_seconds: int = 86_400) -> str:
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        conn = self._connect()
        try:
            conn.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,unixepoch()+?)", (digest, user_id, ttl_seconds))
            conn.commit()
        finally:
            conn.close()
        return token

    def get_user_by_session(self, token: str) -> User | None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        conn = self._connect()
        try:
            row = conn.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>unixepoch()", (digest,)).fetchone()
            if not row:
                return None
            return User(row["id"], row["email"], row["name"], bool(row["email_verified"]), self._workspace_id(conn, row["id"]))
        finally:
            conn.close()

    def delete_session(self, token: str) -> None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        conn = self._connect()
        try:
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (digest,))
            conn.commit()
        finally:
            conn.close()

    def create_workspace(self, user_id: int, name: str, purpose: str | None = None) -> int:
        name = name.strip()
        if not name:
            raise AuthError("workspace name is required")
        conn = self._connect()
        try:
            cur = conn.execute("INSERT INTO workspaces(name,owner_id,purpose) VALUES(?,?,?)", (name, user_id, purpose))
            workspace_id = cur.lastrowid
            conn.execute("INSERT INTO memberships(user_id,workspace_id,role) VALUES(?,?,?)", (user_id, workspace_id, "owner"))
            conn.commit()
            return workspace_id
        finally:
            conn.close()

    def update_onboarding(self, user_id: int, workspace_id: int, purpose: str | None) -> None:
        conn = self._connect()
        try:
            allowed = conn.execute("SELECT 1 FROM memberships WHERE user_id=? AND workspace_id=?", (user_id, workspace_id)).fetchone()
            if not allowed:
                raise AuthError("workspace access denied")
            conn.execute("UPDATE workspaces SET purpose=? WHERE id=?", (purpose, workspace_id))
            conn.commit()
        finally:
            conn.close()

    def _workspace_id(self, conn: sqlite3.Connection, user_id: int) -> int | None:
        row = conn.execute("SELECT workspace_id FROM memberships WHERE user_id=? ORDER BY workspace_id LIMIT 1", (user_id,)).fetchone()
        return row["workspace_id"] if row else None
