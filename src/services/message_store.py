import base64
import os
import time
from dataclasses import dataclass
from typing import Any, Iterable, Literal

from kivy.app import App
from kivy.clock import Clock

from src.utils.event_bus import event_bus

try:
    import sqlcipher3 as sqlite_backend  # type: ignore

    _HAS_SQLCIPHER = True
except Exception:  # pragma: no cover
    import sqlite3 as sqlite_backend

    _HAS_SQLCIPHER = False

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    _HAS_CRYPTO = True
except Exception:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore
    PBKDF2HMAC = None  # type: ignore
    hashes = None  # type: ignore
    _HAS_CRYPTO = False


MessageStatus = Literal['queued', 'sent', 'delivered', 'read', 'failed']


SCHEMA_VERSION = 1
KEY_CHECK_PLAINTEXT = b'message_store_key_check_v1'


@dataclass(frozen=True)
class Cursor:
    created_at: float
    message_id: str


class MessageStore:
    def __init__(
        self,
        key: str,
        db_path: str | None = None,
        enable_sqlcipher: bool = True,
        retention_days: int | None = None,
    ):
        if not isinstance(key, str) or not key:
            raise ValueError('MessageStore requires a non-empty key')

        self._key = key
        self._db_path = db_path or self._default_db_path()
        self._con = None
        self._clock_cleanup_event = None
        self._expiration_events: dict[str, Any] = {}

        self._use_sqlcipher = bool(enable_sqlcipher and _HAS_SQLCIPHER)
        self._fts_enabled = False

        self._retention_days: int | None = int(retention_days) if retention_days is not None else None

        self._open()
        self._init_schema_and_crypto()
        self._schedule_cleanup_loop()
        self._schedule_existing_expirations()

    def close(self):
        if self._clock_cleanup_event is not None:
            self._clock_cleanup_event.cancel()
            self._clock_cleanup_event = None
        for ev in list(self._expiration_events.values()):
            try:
                ev.cancel()
            except Exception:
                pass
        self._expiration_events.clear()
        if self._con is not None:
            self._con.close()
            self._con = None

    def _default_db_path(self):
        app = App.get_running_app()
        if app is not None and getattr(app, 'user_data_dir', None):
            base_dir = app.user_data_dir
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.tor_dashboard')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'messages.db')

    def _open(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._con = sqlite_backend.connect(self._db_path, check_same_thread=False)
        row_factory = getattr(sqlite_backend, 'Row', None)
        if row_factory is not None:
            self._con.row_factory = row_factory

        self._con.execute('PRAGMA foreign_keys = ON')
        self._con.execute('PRAGMA secure_delete = ON')

        if self._use_sqlcipher:
            self._exec_pragma_key(self._con, self._key)

            cipher_row = None
            try:
                cipher_row = self._con.execute('PRAGMA cipher_version').fetchone()
            except Exception:
                cipher_row = None

            if not cipher_row or not cipher_row[0]:
                # The module is present but doesn't appear to be backed by SQLCipher.
                # Fall back to application-layer encryption.
                self._use_sqlcipher = False
            else:
                try:
                    self._con.execute('SELECT count(*) FROM sqlite_master').fetchone()
                except Exception as exc:
                    raise ValueError('Invalid encryption key or database is corrupted') from exc

    def _exec_pragma_key(self, con, key: str):
        escaped = key.replace("'", "''")
        con.execute(f"PRAGMA key = '{escaped}'")

    def _init_schema_and_crypto(self):
        if not _HAS_CRYPTO:
            raise RuntimeError('cryptography is required for MessageStore key verification')

        assert self._con is not None

        current_version = int(self._con.execute('PRAGMA user_version').fetchone()[0])
        if current_version == 0:
            self._create_schema_v1()
            self._con.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
            self._con.commit()
        elif current_version < SCHEMA_VERSION:
            self._migrate(current_version)
            self._con.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
            self._con.commit()

        meta = self._con.execute(
            'SELECT encryption_salt, key_check FROM meta WHERE id = 1'
        ).fetchone()
        if meta is None:
            self._init_meta_row()
        else:
            salt = bytes(meta['encryption_salt'])
            self._fernet = self._build_fernet(self._key, salt)
            try:
                check = self._fernet.decrypt(bytes(meta['key_check']))
            except InvalidToken as exc:
                raise ValueError('Invalid encryption key') from exc
            if check != KEY_CHECK_PLAINTEXT:
                raise ValueError('Invalid encryption key')

        self._con.commit()

    def _init_meta_row(self):
        assert self._con is not None
        salt = os.urandom(16)
        self._fernet = self._build_fernet(self._key, salt)
        key_check = self._fernet.encrypt(KEY_CHECK_PLAINTEXT)
        self._con.execute(
            'INSERT OR REPLACE INTO meta (id, schema_version, created_at, encryption_salt, key_check) '
            'VALUES (1, ?, ?, ?, ?)',
            (SCHEMA_VERSION, time.time(), salt, key_check),
        )

    def _build_fernet(self, password: str, salt: bytes) -> Fernet:
        assert PBKDF2HMAC is not None
        assert hashes is not None
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390_000,
        )
        derived = kdf.derive(password.encode('utf-8'))
        return Fernet(base64.urlsafe_b64encode(derived))

    def _create_schema_v1(self):
        assert self._con is not None

        self._con.executescript(
            '''
            CREATE TABLE IF NOT EXISTS meta (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                schema_version INTEGER NOT NULL,
                created_at REAL NOT NULL,
                encryption_salt BLOB NOT NULL,
                key_check BLOB NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                title_enc BLOB,
                archived INTEGER NOT NULL DEFAULT 0,
                muted_until REAL,
                disappearing_timeout INTEGER,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                last_message_at REAL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                sender_id TEXT,
                message_type TEXT NOT NULL DEFAULT 'text',
                body TEXT,
                body_enc BLOB,
                created_at REAL NOT NULL,
                status TEXT NOT NULL,
                is_outgoing INTEGER NOT NULL DEFAULT 0,
                is_forwarded INTEGER NOT NULL DEFAULT 0,
                is_pinned INTEGER NOT NULL DEFAULT 0,
                ttl_seconds INTEGER,
                expires_at REAL,
                retry_count INTEGER NOT NULL DEFAULT 0,
                next_retry_at REAL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation_created_at
                ON messages(conversation_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_messages_expires_at
                ON messages(expires_at);
            CREATE INDEX IF NOT EXISTS idx_messages_status
                ON messages(status, next_retry_at, created_at);

            CREATE TABLE IF NOT EXISTS reactions (
                message_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                emoji TEXT NOT NULL,
                created_at REAL NOT NULL,
                PRIMARY KEY(message_id, actor_id, emoji),
                FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pinned_states (
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                pinned INTEGER NOT NULL,
                pinned_at REAL,
                PRIMARY KEY(target_type, target_id)
            );

            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                filename TEXT,
                mime_type TEXT,
                size_bytes INTEGER,
                uri TEXT,
                FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
            );
            '''
        )

        self._try_enable_fts()

    def _try_enable_fts(self):
        assert self._con is not None
        if not self._use_sqlcipher:
            self._fts_enabled = False
            return
        try:
            self._con.executescript(
                '''
                CREATE VIRTUAL TABLE IF NOT EXISTS message_fts USING fts5(
                    body,
                    conversation_id UNINDEXED,
                    message_id UNINDEXED,
                    created_at UNINDEXED
                );

                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                    INSERT INTO message_fts(rowid, body, conversation_id, message_id, created_at)
                    VALUES(new.rowid, new.body, new.conversation_id, new.id, new.created_at);
                END;

                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                    INSERT INTO message_fts(message_fts, rowid, body, conversation_id, message_id, created_at)
                    VALUES('delete', old.rowid, old.body, old.conversation_id, old.id, old.created_at);
                END;

                CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
                    INSERT INTO message_fts(message_fts, rowid, body, conversation_id, message_id, created_at)
                    VALUES('delete', old.rowid, old.body, old.conversation_id, old.id, old.created_at);
                    INSERT INTO message_fts(rowid, body, conversation_id, message_id, created_at)
                    VALUES(new.rowid, new.body, new.conversation_id, new.id, new.created_at);
                END;
                '''
            )
            self._fts_enabled = True
        except Exception:
            self._fts_enabled = False

    def _migrate(self, from_version: int):
        if from_version >= SCHEMA_VERSION:
            return
        raise RuntimeError(f'Unsupported schema version {from_version}')

    def _schedule_cleanup_loop(self):
        if self._clock_cleanup_event is not None:
            return

        def _loop(dt):
            self.cleanup_expired()
            self.cleanup_retention()

        self._clock_cleanup_event = Clock.schedule_interval(_loop, 5.0)

    def _schedule_existing_expirations(self):
        for msg in self._query(
            'SELECT id, expires_at FROM messages WHERE expires_at IS NOT NULL',
            (),
        ):
            expires_at = msg['expires_at']
            if expires_at is None:
                continue
            self._schedule_expiration(str(msg['id']), float(expires_at))

    def _schedule_expiration(self, message_id: str, expires_at: float):
        if message_id in self._expiration_events:
            return

        delay = max(0.0, float(expires_at) - time.time())

        def _delete(dt):
            self._expiration_events.pop(message_id, None)
            self.delete_message(message_id)

        self._expiration_events[message_id] = Clock.schedule_once(_delete, delay)

    def _encrypt_text(self, value: str | None) -> bytes | None:
        if value is None:
            return None
        if self._use_sqlcipher:
            return None
        return self._fernet.encrypt(value.encode('utf-8'))

    def _decrypt_text(self, value: str | None, enc: bytes | None) -> str | None:
        if self._use_sqlcipher:
            return value
        if enc is None:
            return None
        return self._fernet.decrypt(enc).decode('utf-8')

    def _execute(self, sql: str, params: tuple[Any, ...] = ()):
        assert self._con is not None
        cur = self._con.execute(sql, params)
        self._con.commit()
        return cur

    def _query(self, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
        assert self._con is not None
        cur = self._con.execute(sql, params)
        return cur.fetchall()

    def upsert_conversation(
        self,
        conversation_id: str,
        *,
        title: str | None = None,
        archived: bool | None = None,
        muted_until: float | None = None,
        disappearing_timeout: int | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        if title is not None and self._use_sqlcipher:
            title_plain = title
            title_enc = None
        else:
            title_plain = None
            title_enc = self._encrypt_text(title)

        patch_fields = {
            'title': title_plain,
            'title_enc': title_enc,
            'archived': 1 if archived else 0 if archived is not None else None,
            'muted_until': muted_until,
            'disappearing_timeout': disappearing_timeout,
        }

        existing = self.get_conversation(conversation_id)
        if existing is None:
            self._execute(
                '''
                INSERT INTO conversations (
                    id, title, title_enc, archived, muted_until, disappearing_timeout, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    conversation_id,
                    title_plain,
                    title_enc,
                    1 if archived else 0,
                    muted_until,
                    disappearing_timeout,
                    now,
                    now,
                ),
            )
        else:
            archived_val = patch_fields['archived']
            self._execute(
                '''
                UPDATE conversations
                   SET title = COALESCE(?, title),
                       title_enc = COALESCE(?, title_enc),
                       archived = COALESCE(?, archived),
                       muted_until = COALESCE(?, muted_until),
                       disappearing_timeout = COALESCE(?, disappearing_timeout),
                       updated_at = ?
                 WHERE id = ?
                ''',
                (
                    title_plain,
                    title_enc,
                    archived_val,
                    muted_until,
                    disappearing_timeout,
                    now,
                    conversation_id,
                ),
            )

        convo = self.get_conversation(conversation_id)
        if convo is not None:
            event_bus.emit_conversation_updated(conversation_id, convo)
            return convo
        raise RuntimeError('Failed to create conversation')

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        rows = self._query('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
        if not rows:
            return None
        row = rows[0]
        title = self._decrypt_text(row['title'], row['title_enc'])
        return {
            'id': str(row['id']),
            'title': title or '',
            'archived': bool(row['archived']),
            'muted_until': row['muted_until'],
            'disappearing_timeout': row['disappearing_timeout'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'last_message_at': row['last_message_at'],
        }

    def set_conversation_archived(self, conversation_id: str, archived: bool):
        return self.upsert_conversation(conversation_id, archived=bool(archived))

    def set_conversation_muted_until(self, conversation_id: str, muted_until: float | None):
        return self.upsert_conversation(conversation_id, muted_until=muted_until)

    def set_conversation_disappearing_timeout(self, conversation_id: str, timeout_seconds: int | None):
        return self.upsert_conversation(conversation_id, disappearing_timeout=timeout_seconds)

    def upsert_message(
        self,
        conversation_id: str,
        message_id: str,
        *,
        sender_id: str | None = None,
        body: str | None = None,
        created_at: float | None = None,
        status: MessageStatus = 'sent',
        is_outgoing: bool = False,
        is_forwarded: bool = False,
        is_pinned: bool = False,
        ttl_seconds: int | None = None,
        message_type: str = 'text',
    ) -> dict[str, Any]:
        created_at = float(created_at if created_at is not None else time.time())

        convo = self.get_conversation(conversation_id)
        if convo is None:
            self.upsert_conversation(conversation_id)
            convo = self.get_conversation(conversation_id)

        disappearing_timeout = None
        if convo is not None:
            disappearing_timeout = convo.get('disappearing_timeout')

        effective_ttl = ttl_seconds if ttl_seconds is not None else disappearing_timeout
        expires_at = created_at + float(effective_ttl) if effective_ttl else None

        if body is not None and self._use_sqlcipher:
            body_plain = body
            body_enc = None
        else:
            body_plain = None
            body_enc = self._encrypt_text(body)

        self._execute(
            '''
            INSERT INTO messages (
                id, conversation_id, sender_id, message_type, body, body_enc, created_at, status,
                is_outgoing, is_forwarded, is_pinned, ttl_seconds, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                conversation_id=excluded.conversation_id,
                sender_id=COALESCE(excluded.sender_id, messages.sender_id),
                message_type=COALESCE(excluded.message_type, messages.message_type),
                body=COALESCE(excluded.body, messages.body),
                body_enc=COALESCE(excluded.body_enc, messages.body_enc),
                created_at=MIN(messages.created_at, excluded.created_at),
                status=excluded.status,
                is_outgoing=excluded.is_outgoing,
                is_forwarded=excluded.is_forwarded,
                is_pinned=excluded.is_pinned,
                ttl_seconds=COALESCE(excluded.ttl_seconds, messages.ttl_seconds),
                expires_at=COALESCE(excluded.expires_at, messages.expires_at)
            ''',
            (
                message_id,
                conversation_id,
                sender_id,
                message_type,
                body_plain,
                body_enc,
                created_at,
                status,
                1 if is_outgoing else 0,
                1 if is_forwarded else 0,
                1 if is_pinned else 0,
                effective_ttl,
                expires_at,
            ),
        )

        if expires_at is not None:
            self._schedule_expiration(message_id, expires_at)

        self._execute(
            'UPDATE conversations SET last_message_at = MAX(COALESCE(last_message_at, 0), ?), updated_at = ? WHERE id = ?',
            (created_at, time.time(), conversation_id),
        )

        msg = self.get_message(message_id)
        if msg is not None:
            event_bus.emit_message_batch(conversation_id, [msg])
            return msg
        raise RuntimeError('Failed to upsert message')

    def get_message(self, message_id: str) -> dict[str, Any] | None:
        rows = self._query('SELECT * FROM messages WHERE id = ?', (message_id,))
        if not rows:
            return None
        row = rows[0]
        body = self._decrypt_text(row['body'], row['body_enc'])
        reactions = self.list_reactions(message_id)
        attachments = self.list_attachments(message_id)
        return {
            'id': str(row['id']),
            'conversation_id': str(row['conversation_id']),
            'sender_id': row['sender_id'],
            'message_type': row['message_type'],
            'body': body or '',
            'created_at': float(row['created_at']),
            'status': row['status'],
            'is_outgoing': bool(row['is_outgoing']),
            'is_forwarded': bool(row['is_forwarded']),
            'is_pinned': bool(row['is_pinned']),
            'ttl_seconds': row['ttl_seconds'],
            'expires_at': row['expires_at'],
            'reactions': reactions,
            'attachments': attachments,
        }

    def fetch_history(
        self,
        conversation_id: str,
        *,
        limit: int = 50,
        before: Cursor | dict[str, Any] | None = None,
        after: Cursor | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if before is not None and after is not None:
            raise ValueError('Provide either before or after, not both')

        if isinstance(before, dict):
            before = Cursor(float(before['created_at']), str(before['id']))
        if isinstance(after, dict):
            after = Cursor(float(after['created_at']), str(after['id']))

        params: list[Any] = [conversation_id]

        if before is not None:
            sql = (
                'SELECT * FROM messages WHERE conversation_id = ? '
                'AND (created_at < ? OR (created_at = ? AND id < ?)) '
                'ORDER BY created_at DESC, id DESC LIMIT ?'
            )
            params.extend([before.created_at, before.created_at, before.message_id, int(limit)])
            rows = self._query(sql, tuple(params))
            rows = list(reversed(rows))
        elif after is not None:
            sql = (
                'SELECT * FROM messages WHERE conversation_id = ? '
                'AND (created_at > ? OR (created_at = ? AND id > ?)) '
                'ORDER BY created_at ASC, id ASC LIMIT ?'
            )
            params.extend([after.created_at, after.created_at, after.message_id, int(limit)])
            rows = self._query(sql, tuple(params))
        else:
            rows = self._query(
                'SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC, id DESC LIMIT ?',
                (conversation_id, int(limit)),
            )
            rows = list(reversed(rows))

        ids = [str(r['id']) for r in rows]
        reactions_by = self._get_reactions_by_message(ids)
        attachments_by = self._get_attachments_by_message(ids)

        out: list[dict[str, Any]] = []
        for row in rows:
            mid = str(row['id'])
            body = self._decrypt_text(row['body'], row['body_enc'])
            out.append(
                {
                    'id': mid,
                    'conversation_id': str(row['conversation_id']),
                    'sender_id': row['sender_id'],
                    'message_type': row['message_type'],
                    'body': body or '',
                    'created_at': float(row['created_at']),
                    'status': row['status'],
                    'is_outgoing': bool(row['is_outgoing']),
                    'is_forwarded': bool(row['is_forwarded']),
                    'is_pinned': bool(row['is_pinned']),
                    'ttl_seconds': row['ttl_seconds'],
                    'expires_at': row['expires_at'],
                    'reactions': reactions_by.get(mid, []),
                    'attachments': attachments_by.get(mid, []),
                }
            )

        return out

    def delete_message(self, message_id: str):
        if message_id in self._expiration_events:
            ev = self._expiration_events.pop(message_id)
            try:
                ev.cancel()
            except Exception:
                pass

        msg = self.get_message(message_id)
        self._execute('DELETE FROM messages WHERE id = ?', (message_id,))
        if msg is not None:
            event_bus.emit_message_deleted(str(msg['conversation_id']), message_id)

    def cleanup_expired(self, now: float | None = None) -> int:
        now = float(now if now is not None else time.time())
        expired_ids = [
            str(r['id'])
            for r in self._query(
                'SELECT id FROM messages WHERE expires_at IS NOT NULL AND expires_at <= ?',
                (now,),
            )
        ]
        for mid in expired_ids:
            self.delete_message(mid)
        return len(expired_ids)

    def set_retention_days(self, retention_days: int | None):
        self._retention_days = int(retention_days) if retention_days is not None else None

    def cleanup_retention(self, now: float | None = None) -> int:
        if self._retention_days is None:
            return 0

        now = float(now if now is not None else time.time())
        cutoff = now - (float(self._retention_days) * 86400.0)
        old_ids = [
            str(r['id'])
            for r in self._query(
                'SELECT id FROM messages WHERE created_at < ? ORDER BY created_at ASC',
                (cutoff,),
            )
        ]
        for mid in old_ids:
            self.delete_message(mid)
        return len(old_ids)

    def update_message_status(self, message_id: str, status: MessageStatus):
        self._execute('UPDATE messages SET status = ? WHERE id = ?', (status, message_id))
        msg = self.get_message(message_id)
        if msg is not None:
            event_bus.emit_receipt_update(msg['conversation_id'], message_id, status)
            event_bus.emit_message_batch(msg['conversation_id'], [msg])

    def set_message_pinned(self, message_id: str, pinned: bool):
        pinned = bool(pinned)
        self._execute('UPDATE messages SET is_pinned = ? WHERE id = ?', (1 if pinned else 0, message_id))
        if pinned:
            self._execute(
                'INSERT OR REPLACE INTO pinned_states (target_type, target_id, pinned, pinned_at) VALUES (?, ?, ?, ?)',
                ('message', message_id, 1, time.time()),
            )
        else:
            self._execute(
                'DELETE FROM pinned_states WHERE target_type = ? AND target_id = ?',
                ('message', message_id),
            )

        msg = self.get_message(message_id)
        if msg is not None:
            event_bus.emit_message_batch(msg['conversation_id'], [msg])

    def set_message_forwarded(self, message_id: str, forwarded: bool):
        self._execute(
            'UPDATE messages SET is_forwarded = ? WHERE id = ?',
            (1 if forwarded else 0, message_id),
        )
        msg = self.get_message(message_id)
        if msg is not None:
            event_bus.emit_message_batch(msg['conversation_id'], [msg])

    def add_attachment(
        self,
        message_id: str,
        *,
        filename: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
        uri: str | None = None,
    ):
        self._execute(
            'INSERT INTO attachments (message_id, filename, mime_type, size_bytes, uri) VALUES (?, ?, ?, ?, ?)',
            (message_id, filename, mime_type, size_bytes, uri),
        )
        msg = self.get_message(message_id)
        if msg is not None:
            event_bus.emit_message_batch(msg['conversation_id'], [msg])

    def list_reactions(self, message_id: str) -> list[dict[str, Any]]:
        return [
            {
                'message_id': str(r['message_id']),
                'actor_id': str(r['actor_id']),
                'emoji': str(r['emoji']),
                'created_at': float(r['created_at']),
            }
            for r in self._query(
                'SELECT * FROM reactions WHERE message_id = ? ORDER BY created_at ASC',
                (message_id,),
            )
        ]

    def _get_reactions_by_message(self, message_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
        mids = list(message_ids)
        if not mids:
            return {}
        placeholders = ','.join(['?'] * len(mids))
        rows = self._query(
            f'SELECT * FROM reactions WHERE message_id IN ({placeholders}) ORDER BY created_at ASC',
            tuple(mids),
        )
        out: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            mid = str(r['message_id'])
            out.setdefault(mid, []).append(
                {
                    'message_id': mid,
                    'actor_id': str(r['actor_id']),
                    'emoji': str(r['emoji']),
                    'created_at': float(r['created_at']),
                }
            )
        return out

    def add_reaction(self, message_id: str, actor_id: str, emoji: str):
        self._execute(
            'INSERT OR IGNORE INTO reactions (message_id, actor_id, emoji, created_at) VALUES (?, ?, ?, ?)',
            (message_id, actor_id, emoji, time.time()),
        )
        msg = self.get_message(message_id)
        if msg is not None:
            event_bus.emit_message_batch(msg['conversation_id'], [msg])

    def remove_reaction(self, message_id: str, actor_id: str, emoji: str):
        self._execute(
            'DELETE FROM reactions WHERE message_id = ? AND actor_id = ? AND emoji = ?',
            (message_id, actor_id, emoji),
        )
        msg = self.get_message(message_id)
        if msg is not None:
            event_bus.emit_message_batch(msg['conversation_id'], [msg])

    def list_attachments(self, message_id: str) -> list[dict[str, Any]]:
        return [
            {
                'id': int(r['id']),
                'message_id': str(r['message_id']),
                'filename': r['filename'],
                'mime_type': r['mime_type'],
                'size_bytes': r['size_bytes'],
                'uri': r['uri'],
            }
            for r in self._query(
                'SELECT * FROM attachments WHERE message_id = ? ORDER BY id ASC',
                (message_id,),
            )
        ]

    def _get_attachments_by_message(self, message_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
        mids = list(message_ids)
        if not mids:
            return {}
        placeholders = ','.join(['?'] * len(mids))
        rows = self._query(
            f'SELECT * FROM attachments WHERE message_id IN ({placeholders}) ORDER BY id ASC',
            tuple(mids),
        )
        out: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            mid = str(r['message_id'])
            out.setdefault(mid, []).append(
                {
                    'id': int(r['id']),
                    'message_id': mid,
                    'filename': r['filename'],
                    'mime_type': r['mime_type'],
                    'size_bytes': r['size_bytes'],
                    'uri': r['uri'],
                }
            )
        return out

    def search_messages(
        self,
        *,
        keyword: str,
        conversation_id: str | None = None,
        start_ts: float | None = None,
        end_ts: float | None = None,
        message_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        keyword = (keyword or '').strip()
        if not keyword:
            return []

        if self._fts_enabled:
            where = ['f MATCH ?']
            params: list[Any] = [keyword]
            if conversation_id is not None:
                where.append('m.conversation_id = ?')
                params.append(conversation_id)
            if start_ts is not None:
                where.append('m.created_at >= ?')
                params.append(float(start_ts))
            if end_ts is not None:
                where.append('m.created_at <= ?')
                params.append(float(end_ts))
            if message_type is not None:
                where.append('m.message_type = ?')
                params.append(message_type)

            sql = (
                'SELECT m.* FROM message_fts f '
                'JOIN messages m ON m.rowid = f.rowid '
                f"WHERE {' AND '.join(where)} "
                'ORDER BY m.created_at DESC, m.id DESC LIMIT ? OFFSET ?'
            )
            params.extend([int(limit), int(offset)])
            rows = self._query(sql, tuple(params))
            rows = list(reversed(rows))
            return [self.get_message(str(r['id'])) for r in rows if self.get_message(str(r['id'])) is not None]

        # Fallback: decrypt+scan (used when SQLCipher/FTS isn't available)
        clauses = ['1=1']
        params2: list[Any] = []
        if conversation_id is not None:
            clauses.append('conversation_id = ?')
            params2.append(conversation_id)
        if start_ts is not None:
            clauses.append('created_at >= ?')
            params2.append(float(start_ts))
        if end_ts is not None:
            clauses.append('created_at <= ?')
            params2.append(float(end_ts))
        if message_type is not None:
            clauses.append('message_type = ?')
            params2.append(message_type)

        rows2 = self._query(
            f"SELECT * FROM messages WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id DESC",
            tuple(params2),
        )
        results: list[dict[str, Any]] = []
        keyword_l = keyword.lower()
        for r in rows2:
            body = self._decrypt_text(r['body'], r['body_enc']) or ''
            if keyword_l in body.lower():
                msg = self.get_message(str(r['id']))
                if msg is not None:
                    results.append(msg)
        results = results[::-1]
        return results[offset : offset + limit]

    def get_outgoing_queue(self, *, limit: int = 50) -> list[dict[str, Any]]:
        now = time.time()
        rows = self._query(
            '''
            SELECT * FROM messages
             WHERE is_outgoing = 1
               AND status IN ('queued', 'failed')
               AND (next_retry_at IS NULL OR next_retry_at <= ?)
             ORDER BY created_at ASC, id ASC
             LIMIT ?
            ''',
            (now, int(limit)),
        )
        out: list[dict[str, Any]] = []
        for r in rows:
            msg = self.get_message(str(r['id']))
            if msg is not None:
                out.append(msg)
        return out

    def mark_retry(self, message_id: str, *, delay_seconds: float, retry_count: int | None = None):
        next_retry = time.time() + float(delay_seconds)
        if retry_count is None:
            self._execute(
                'UPDATE messages SET status = ?, retry_count = retry_count + 1, next_retry_at = ? WHERE id = ?',
                ('failed', next_retry, message_id),
            )
        else:
            self._execute(
                'UPDATE messages SET status = ?, retry_count = ?, next_retry_at = ? WHERE id = ?',
                ('failed', int(retry_count), next_retry, message_id),
            )


message_store: MessageStore | None = None


def get_message_store(key: str) -> MessageStore:
    global message_store
    if message_store is None:
        message_store = MessageStore(key=key)
    return message_store
