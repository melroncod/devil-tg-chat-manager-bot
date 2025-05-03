import sqlite3
from aiogram import types
from datetime import datetime
from config import ENABLE_LINK_FILTER_DEFAULT

DB_NAME = "bot_manager.db"


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1) Chats, Admins, User_info, User_chats
    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        member_count INTEGER DEFAULT 0
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_info (
        user_id INTEGER NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        last_seen TEXT,
        PRIMARY KEY (user_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_chats (
        user_id       INTEGER NOT NULL,
        chat_id       INTEGER NOT NULL,
        first_seen    TEXT NOT NULL,
        last_seen     TEXT NOT NULL,
        message_count INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, chat_id),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
        FOREIGN KEY (user_id) REFERENCES user_info(user_id)
    )""")

    # Миграция под старые версии user_chats — добавляем отсутствующие колонки
    c.execute("PRAGMA table_info(user_chats)")
    existing_cols = {row[1] for row in c.fetchall()}
    extras = {
        "first_seen":    "TEXT NOT NULL DEFAULT ''",
        "last_seen":     "TEXT NOT NULL DEFAULT ''",
        "message_count": "INTEGER NOT NULL DEFAULT 0"
    }
    for col, definition in extras.items():
        if col not in existing_cols:
            c.execute(f"ALTER TABLE user_chats ADD COLUMN {col} {definition}")


    # 2) Filters
    c.execute("""
    CREATE TABLE IF NOT EXISTS filters (
        chat_id INTEGER PRIMARY KEY,
        links_enabled BOOLEAN NOT NULL DEFAULT 1
    )""")
    c.execute("PRAGMA table_info(filters)")
    existing = {row[1] for row in c.fetchall()}
    extras = {
        "caps_enabled":     "BOOLEAN NOT NULL DEFAULT 0",
        "spam_enabled":     "BOOLEAN NOT NULL DEFAULT 0",
        "swear_enabled":    "BOOLEAN NOT NULL DEFAULT 0",
        "keywords_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        "stickers_enabled": "BOOLEAN NOT NULL DEFAULT 0"
    }

    for col, definition in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE filters ADD COLUMN {col} {definition}")

    # 3) Warnings
    c.execute("""
    CREATE TABLE IF NOT EXISTS warnings (
        user_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        warn_count INTEGER NOT NULL DEFAULT 0,
        last_warn TEXT,
        username TEXT,
        PRIMARY KEY (user_id, chat_id),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
    )""")

    # 4) Mutes
    c.execute("""
    CREATE TABLE IF NOT EXISTS mutes (
        user_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        mute_count INTEGER NOT NULL DEFAULT 0,
        last_mute TEXT,
        username TEXT,
        PRIMARY KEY (user_id, chat_id),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
    )""")

    # 5) Keywords
    c.execute("""
    CREATE TABLE IF NOT EXISTS keywords (
        chat_id INTEGER NOT NULL,
        keyword TEXT NOT NULL,
        PRIMARY KEY (chat_id, keyword),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
    )""")

    # 6) User aliases
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_aliases (
        chat_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY (chat_id, username),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
    )""")

    # 7) Welcome messages
    c.execute("""
    CREATE TABLE IF NOT EXISTS welcome_messages (
        chat_id INTEGER PRIMARY KEY,
        message TEXT NOT NULL
    )""")

    # 8) Chat rules
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_rules (
        chat_id INTEGER PRIMARY KEY,
        rules TEXT NOT NULL
    )""")

    c.execute("PRAGMA foreign_keys = ON")

    # 9) Логи
    c.execute("""
    CREATE TABLE IF NOT EXISTS log_settings (
        chat_id               INTEGER PRIMARY KEY,
        log_chat_id           INTEGER,
        is_logging_enabled    BOOLEAN NOT NULL DEFAULT 0,
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
    )
    """)

    # 9) Welcome settings
    c.execute("""
    CREATE TABLE IF NOT EXISTS welcome_settings (
        chat_id      INTEGER PRIMARY KEY,
        delete_timeout INTEGER NOT NULL
    )""")

    conn.commit()
    conn.close()


# ——— Bans CRUD ———

def get_ban_info(user_id: int, chat_id: int) -> tuple[int, datetime | None]:
    """Получает информацию о банах пользователя в чате"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id    INTEGER NOT NULL,
            chat_id    INTEGER NOT NULL,
            ban_count  INTEGER NOT NULL DEFAULT 0,
            last_ban   TEXT,
            username   TEXT,
            PRIMARY KEY (user_id, chat_id),
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        )
    """)
    c.execute("SELECT ban_count, last_ban FROM bans WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    if not row:
        return 0, None
    count, last_str = row
    last = datetime.fromisoformat(last_str) if last_str else None
    return count, last


def add_ban(user_id: int, chat_id: int, username: str):
    """Добавляет запись о бане пользователя"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()

    # Создаем таблицу, если ее нет
    c.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id    INTEGER NOT NULL,
            chat_id    INTEGER NOT NULL,
            ban_count  INTEGER NOT NULL DEFAULT 0,
            last_ban   TEXT,
            username   TEXT,
            PRIMARY KEY (user_id, chat_id),
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        )
    """)

    c.execute("""
        INSERT INTO bans (user_id, chat_id, username, last_ban)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            username   = excluded.username,
            ban_count  = bans.ban_count + 1,
            last_ban   = excluded.last_ban
    """, (user_id, chat_id, username, now))
    conn.commit()
    conn.close()


def reset_bans(user_id: int, chat_id: int):
    """Сбрасывает счетчик банов для пользователя в чате"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Создаем таблицу, если ее нет
    c.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id    INTEGER NOT NULL,
            chat_id    INTEGER NOT NULL,
            ban_count  INTEGER NOT NULL DEFAULT 0,
            last_ban   TEXT,
            username   TEXT,
            PRIMARY KEY (user_id, chat_id),
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        )
    """)

    c.execute("UPDATE bans SET ban_count = 0, last_ban = NULL WHERE user_id=? AND chat_id=?",
              (user_id, chat_id))
    conn.commit()
    conn.close()


# ——— Filters CRUD ———

# Новые функции для работы с пользователями и чатами
def update_user_info(user: types.User):
    """Обновляет информацию о пользователе"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()

    c.execute("""
        INSERT INTO user_info (user_id, username, first_name, last_name, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = COALESCE(excluded.username, username),
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            last_seen = excluded.last_seen
    """, (user.id, user.username, user.first_name, user.last_name, now))

    conn.commit()
    conn.close()


def update_user_chat_activity(user_id: int, chat_id: int, chat_name: str, is_message: bool = False):
    """Обновляет информацию о активности пользователя в чате"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()

    # Добавляем чат, если его нет
    c.execute("INSERT OR IGNORE INTO chats (chat_id, name) VALUES (?, ?)", (chat_id, chat_name))

    # Обновляем информацию о пользователе в чате
    c.execute("""
        INSERT INTO user_chats (user_id, chat_id, first_seen, last_seen, message_count)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            last_seen = excluded.last_seen,
            message_count = message_count + ?
    """, (user_id, chat_id, now, now, 1 if is_message else 0, 1 if is_message else 0))

    # Обновляем счетчик участников чата
    if not is_message:  # Только для новых участников
        c.execute("""
            UPDATE chats SET member_count = (
                SELECT COUNT(*) FROM user_chats WHERE chat_id = ?
            ) WHERE chat_id = ?
        """, (chat_id, chat_id))

    conn.commit()
    conn.close()


def get_user_chat_info(user_id: int, chat_id: int) -> dict | None:
    """Возвращает информацию о пользователе в конкретном чате"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT ui.user_id, ui.username, ui.first_name, ui.last_name,
               uc.first_seen, uc.last_seen, uc.message_count
        FROM user_info ui
        JOIN user_chats uc ON ui.user_id = uc.user_id
        WHERE ui.user_id = ? AND uc.chat_id = ?
    """, (user_id, chat_id))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        'user_id': row[0],
        'username': row[1],
        'first_name': row[2],
        'last_name': row[3],
        'first_seen': row[4],
        'last_seen': row[5],
        'message_count': row[6]
    }

def _set_filter_field(chat_id: int, field: str, enabled: bool):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO filters (chat_id) VALUES (?)", (chat_id,))
    c.execute(f"UPDATE filters SET {field} = ? WHERE chat_id = ?", (int(enabled), chat_id))
    conn.commit()
    conn.close()

def _get_filter_field(chat_id: int, field: str, default: bool = False) -> bool:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"SELECT {field} FROM filters WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return bool(row[0]) if row else default

def set_link_filter(chat_id: int, enabled: bool):      _set_filter_field(chat_id, "links_enabled", enabled)

def get_link_filter(chat_id: int) -> bool:             return _get_filter_field(chat_id, "links_enabled", ENABLE_LINK_FILTER_DEFAULT)

def set_sticker_filter(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "stickers_enabled", enabled)

def get_sticker_filter(chat_id: int) -> bool:
    # по умолчанию выключен
    return _get_filter_field(chat_id, "stickers_enabled", default=False)


def set_caps_filter(chat_id: int, enabled: bool):      _set_filter_field(chat_id, "caps_enabled", enabled)

def get_caps_filter(chat_id: int) -> bool:             return _get_filter_field(chat_id, "caps_enabled")

def set_spam_filter(chat_id: int, enabled: bool):      _set_filter_field(chat_id, "spam_enabled", enabled)

def get_spam_filter(chat_id: int) -> bool:             return _get_filter_field(chat_id, "spam_enabled")

def set_swear_filter(chat_id: int, enabled: bool):     _set_filter_field(chat_id, "swear_enabled", enabled)

def get_swear_filter(chat_id: int) -> bool:            return _get_filter_field(chat_id, "swear_enabled")

def set_keywords_filter(chat_id: int, enabled: bool):  _set_filter_field(chat_id, "keywords_enabled", enabled)

def get_keywords_filter(chat_id: int) -> bool:         return _get_filter_field(chat_id, "keywords_enabled")


# ——— Keywords CRUD ———

def add_keyword(chat_id: int, keyword: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO keywords (chat_id, keyword) VALUES (?, ?)",
              (chat_id, keyword.strip().lower()))
    conn.commit()
    conn.close()

def remove_keyword(chat_id: int, keyword: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM keywords WHERE chat_id = ? AND keyword = ?",
              (chat_id, keyword.strip().lower()))
    conn.commit()
    conn.close()

def get_keywords(chat_id: int) -> list[str]:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT keyword FROM keywords WHERE chat_id = ?", (chat_id,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


# ——— Chats, Admins & User‑Chats ———

def add_chat(chat_id: int, name: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO chats (chat_id, name) VALUES (?, ?)", (chat_id, name))
    conn.commit()
    conn.close()

def get_chats() -> dict[int, str]:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT chat_id, name FROM chats")
    rows = c.fetchall()
    conn.close()
    return {chat_id: name for chat_id, name in rows}

def add_admin(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_admins() -> list[int]:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def remove_admin(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_user_chat(user_id: int, chat_id: int, chat_name: str):
    """
    Добавляет или обновляет запись о том, что пользователь является участником чата.
    Обновляет название чата в таблице chats и сохраняет метки первого/последнего появления.
    """
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Обновляем или вставляем название чата
    c.execute(
        "INSERT OR REPLACE INTO chats (chat_id, name) VALUES (?, ?)",
        (chat_id, chat_name)
    )
    # Upsert в user_chats, сохраняем существующий message_count
    c.execute(
        "INSERT INTO user_chats (user_id, chat_id, first_seen, last_seen, message_count)"
        " VALUES (?, ?, ?, ?, COALESCE((SELECT message_count FROM user_chats WHERE user_id=? AND chat_id=?), 0))"
        " ON CONFLICT(user_id, chat_id) DO UPDATE SET last_seen=excluded.last_seen",
        (user_id, chat_id, now, now, user_id, chat_id)
    )
    conn.commit()
    conn.close()

def remove_user_chat(user_id: int, chat_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM user_chats WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    conn.commit()
    conn.close()

def get_user_chats(user_id: int) -> dict[int, str]:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT uc.chat_id, ch.name 
        FROM user_chats uc
        JOIN chats ch ON uc.chat_id = ch.chat_id
        WHERE uc.user_id = ?
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return {chat_id: name for chat_id, name in rows}


# ——— Warnings CRUD ———

def get_warn_count(user_id: int, chat_id: int) -> int:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT warn_count FROM warnings WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_warn(user_id: int, chat_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO warnings (user_id, chat_id, username, warn_count, last_warn)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            username   = excluded.username,
            warn_count = warnings.warn_count + 1,
            last_warn  = excluded.last_warn
    """, (user_id, chat_id, username, now))
    conn.commit()
    conn.close()


def reset_warns(user_id: int, chat_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE warnings SET warn_count = 0, last_warn = NULL WHERE user_id=? AND chat_id=?",
              (user_id, chat_id))
    conn.commit()
    conn.close()


# ——— Mutes CRUD ———

def get_mute_info(user_id: int, chat_id: int) -> tuple[int, datetime | None]:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT mute_count, last_mute FROM mutes WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    if not row:
        return 0, None
    count, last_str = row
    last = datetime.fromisoformat(last_str) if last_str else None
    return count, last

def add_mute(user_id: int, chat_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO mutes (user_id, chat_id, username, last_mute)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            username   = excluded.username,
            mute_count = mutes.mute_count + 1,
            last_mute  = excluded.last_mute
    """, (user_id, chat_id, username, now))
    conn.commit()
    conn.close()

def reset_mutes(user_id: int, chat_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE mutes SET mute_count = 0, last_mute = NULL WHERE user_id=? AND chat_id=?",
              (user_id, chat_id))
    conn.commit()
    conn.close()


# ——— Aliases CRUD ———

def upsert_alias(chat_id: int, username: str, user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_aliases (chat_id, username, user_id)
        VALUES (?, ?, ?)
        ON CONFLICT(chat_id, username) DO UPDATE SET
            user_id = excluded.user_id
    """, (chat_id, username.lstrip('@').lower(), user_id))
    conn.commit()
    conn.close()

def resolve_username(chat_id: int, username: str) -> int | None:
    """
    Ищет в user_aliases по chat_id и username (без @), возвращает user_id или None.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT user_id FROM user_aliases
        WHERE chat_id = ? AND username = ?
    """, (chat_id, username.lstrip('@').lower()))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ——— Welcome Messages CRUD ———

def set_welcome_message(chat_id: int, message: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO welcome_messages (chat_id, message) VALUES (?, ?)",
              (chat_id, message))
    conn.commit()
    conn.close()


def get_welcome_message(chat_id: int) -> str | None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT message FROM welcome_messages WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def set_rules(chat_id: int, rules: str):
    """Устанавливает правила для чата"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO chat_rules (chat_id, rules)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET rules=excluded.rules
    """, (chat_id, rules))

def set_welcome_delete_timeout(chat_id: int, timeout: int):
    """
    timeout: количество секунд (0 — отключить авто‑удаление)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO welcome_settings (chat_id, delete_timeout)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET delete_timeout = excluded.delete_timeout
    """, (chat_id, timeout))
    conn.commit()
    conn.close()


def get_welcome_delete_timeout(chat_id: int) -> int | None:
    """
    Возвращает:
      - число секунд,
      - 0 — если явно отключено,
      - None — если ещё не задано (будем понимать как «по умолчанию»).
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT delete_timeout FROM welcome_settings WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def get_rules(chat_id: int) -> str | None:
    """Получает правила чата"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT rules FROM chat_rules WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ——— Log Settings CRUD ———

def get_log_settings(chat_id: int) -> dict | None:
    """
    Возвращает словарь:
      {
        'chat_id': int,
        'log_chat_id': int | None,
        'is_logging_enabled': bool
      }
    или None, если нет записи.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT log_chat_id, is_logging_enabled
        FROM log_settings
        WHERE chat_id = ?
    """, (chat_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'chat_id': chat_id,
        'log_chat_id': row[0],
        'is_logging_enabled': bool(row[1])
    }

def set_log_chat(chat_id: int, log_chat_id: int) -> None:
    """
    Устанавливает/обновляет chat_id для логирования
    и гарантированно создаёт запись в log_settings.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO log_settings (chat_id, log_chat_id)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            log_chat_id = excluded.log_chat_id
    """, (chat_id, log_chat_id))
    conn.commit()
    conn.close()

def update_log_status(chat_id: int, enabled: bool) -> None:
    """
    Включает/выключает логирование для заданного chat_id.
    Если записи ещё не было, создаст её с log_chat_id = NULL.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO log_settings (chat_id, is_logging_enabled)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            is_logging_enabled = excluded.is_logging_enabled
    """, (chat_id, int(enabled)))
    conn.commit()
    conn.close()
