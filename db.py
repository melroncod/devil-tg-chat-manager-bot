import psycopg2
from psycopg2 import sql
from datetime import datetime
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    """
    Возвращает новое соединение с PostgreSQL.
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def create_tables():
    """
    Создаёт все необходимые таблицы в PostgreSQL (если их ещё нет).
    """
    conn = get_connection()
    c = conn.cursor()

    # 1) Таблица chats
    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        chat_id       BIGINT PRIMARY KEY,
        name          TEXT NOT NULL,
        member_count  INTEGER DEFAULT 0
    );
    """)

    # 2) Таблица admins
    c.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id BIGINT PRIMARY KEY
    );
    """)

    # 3) Таблица user_info
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_info (
        user_id    BIGINT PRIMARY KEY,
        username   TEXT,
        first_name TEXT,
        last_name  TEXT,
        last_seen  TIMESTAMP
    );
    """)

    # 4) Таблица user_chats
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_chats (
        user_id       BIGINT    NOT NULL,
        chat_id       BIGINT    NOT NULL,
        first_seen    TIMESTAMP NOT NULL,
        last_seen     TIMESTAMP NOT NULL,
        message_count INTEGER  NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, chat_id),
        FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE,
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
    );
    """)

    # 5) Таблица filters
    c.execute("""
    CREATE TABLE IF NOT EXISTS filters (
        chat_id             BIGINT PRIMARY KEY,
        links_enabled       BOOLEAN NOT NULL DEFAULT TRUE,
        caps_enabled        BOOLEAN NOT NULL DEFAULT FALSE,
        spam_enabled        BOOLEAN NOT NULL DEFAULT FALSE,
        swear_enabled       BOOLEAN NOT NULL DEFAULT FALSE,
        keywords_enabled    BOOLEAN NOT NULL DEFAULT FALSE,
        stickers_enabled    BOOLEAN NOT NULL DEFAULT FALSE,
        join_delete_enabled BOOLEAN NOT NULL DEFAULT FALSE
    );
    """)

    # 6) Таблица warnings
    c.execute("""
    CREATE TABLE IF NOT EXISTS warnings (
        user_id    BIGINT NOT NULL,
        chat_id    BIGINT NOT NULL,
        warn_count INTEGER NOT NULL DEFAULT 0,
        last_warn  TIMESTAMP,
        username   TEXT,
        PRIMARY KEY (user_id, chat_id),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
    );
    """)

    # 7) Таблица mutes
    c.execute("""
    CREATE TABLE IF NOT EXISTS mutes (
        user_id    BIGINT NOT NULL,
        chat_id    BIGINT NOT NULL,
        mute_count INTEGER NOT NULL DEFAULT 0,
        last_mute  TIMESTAMP,
        username   TEXT,
        PRIMARY KEY (user_id, chat_id),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
    );
    """)

    # 8) Таблица keywords
    c.execute("""
    CREATE TABLE IF NOT EXISTS keywords (
        chat_id BIGINT NOT NULL,
        keyword TEXT NOT NULL,
        PRIMARY KEY (chat_id, keyword),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
    );
    """)

    # 9) Таблица user_aliases
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_aliases (
        chat_id  BIGINT NOT NULL,
        username TEXT  NOT NULL,
        user_id  BIGINT NOT NULL,
        PRIMARY KEY (chat_id, username),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
    );
    """)

    # 10) Таблица welcome_messages
    c.execute("""
    CREATE TABLE IF NOT EXISTS welcome_messages (
        chat_id BIGINT PRIMARY KEY,
        message TEXT NOT NULL
    );
    """)

    # 11) Таблица chat_rules
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_rules (
        chat_id BIGINT PRIMARY KEY,
        rules   TEXT NOT NULL
    );
    """)

    # 12) Таблица log_settings
    c.execute("""
    CREATE TABLE IF NOT EXISTS log_settings (
        chat_id            BIGINT PRIMARY KEY,
        log_chat_id        BIGINT,
        is_logging_enabled BOOLEAN NOT NULL DEFAULT FALSE,
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
    );
    """)

    # 13) Таблица welcome_settings
    c.execute("""
    CREATE TABLE IF NOT EXISTS welcome_settings (
        chat_id        BIGINT PRIMARY KEY,
        delete_timeout INTEGER NOT NULL
    );
    """)

    # 14) Таблица bans
    c.execute("""
    CREATE TABLE IF NOT EXISTS bans (
        user_id   BIGINT NOT NULL,
        chat_id   BIGINT NOT NULL,
        ban_count INTEGER NOT NULL DEFAULT 0,
        last_ban  TIMESTAMP,
        username  TEXT,
        PRIMARY KEY (user_id, chat_id),
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    c.close()
    conn.close()


# ——— Bans CRUD ———

def get_ban_info(user_id: int, chat_id: int) -> tuple[int, datetime | None]:
    """Получает информацию о банах пользователя в чате"""
    conn = get_connection()
    c = conn.cursor()
    # Убеждаемся, что таблица bans существует
    c.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id   BIGINT NOT NULL,
            chat_id   BIGINT NOT NULL,
            ban_count INTEGER NOT NULL DEFAULT 0,
            last_ban  TIMESTAMP,
            username  TEXT,
            PRIMARY KEY (user_id, chat_id),
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    c.execute("SELECT ban_count, last_ban FROM bans WHERE user_id=%s AND chat_id=%s", (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    if not row:
        return 0, None
    count, last = row
    return count, last


def add_ban(user_id: int, chat_id: int, username: str):
    """Добавляет запись о бане пользователя"""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.utcnow()
    # Убеждаемся, что таблица bans существует
    c.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id   BIGINT NOT NULL,
            chat_id   BIGINT NOT NULL,
            ban_count INTEGER NOT NULL DEFAULT 0,
            last_ban  TIMESTAMP,
            username  TEXT,
            PRIMARY KEY (user_id, chat_id),
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    c.execute("""
        INSERT INTO bans (user_id, chat_id, username, last_ban)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, chat_id) DO UPDATE SET
            username  = EXCLUDED.username,
            ban_count = bans.ban_count + 1,
            last_ban  = EXCLUDED.last_ban
    """, (user_id, chat_id, username, now))
    conn.commit()
    conn.close()


def reset_bans(user_id: int, chat_id: int):
    """Сбрасывает счетчик банов для пользователя в чате"""
    conn = get_connection()
    c = conn.cursor()
    # Убеждаемся, что таблица bans существует
    c.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id   BIGINT NOT NULL,
            chat_id   BIGINT NOT NULL,
            ban_count INTEGER NOT NULL DEFAULT 0,
            last_ban  TIMESTAMP,
            username  TEXT,
            PRIMARY KEY (user_id, chat_id),
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    c.execute("UPDATE bans SET ban_count = 0, last_ban = NULL WHERE user_id=%s AND chat_id=%s", (user_id, chat_id))
    conn.commit()
    conn.close()


# ——— Filters CRUD ———

def _set_filter_field(chat_id: int, field: str, enabled: bool):
    """
    Утилита: вставляет запись в filters, если её нет, и выставляет нужное булево поле.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO filters (chat_id) VALUES (%s) ON CONFLICT (chat_id) DO NOTHING", (chat_id,))
    c.execute(
        sql.SQL("UPDATE filters SET {} = %s WHERE chat_id = %s").format(sql.Identifier(field)),
        (enabled, chat_id)
    )
    conn.commit()
    conn.close()


def _get_filter_field(chat_id: int, field: str, default: bool = False) -> bool:
    """
    Утилита: возвращает значение булевого поля из filters или default, если записи нет.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        sql.SQL("SELECT {} FROM filters WHERE chat_id = %s").format(sql.Identifier(field)),
        (chat_id,)
    )
    row = c.fetchone()
    conn.close()
    return bool(row[0]) if row else default


def set_link_filter(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "links_enabled", enabled)


def get_link_filter(chat_id: int) -> bool:
    return _get_filter_field(chat_id, "links_enabled", default=True)


def set_sticker_filter(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "stickers_enabled", enabled)


def get_sticker_filter(chat_id: int) -> bool:
    return _get_filter_field(chat_id, "stickers_enabled", default=False)


def set_caps_filter(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "caps_enabled", enabled)


def get_caps_filter(chat_id: int) -> bool:
    return _get_filter_field(chat_id, "caps_enabled", default=False)


def set_spam_filter(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "spam_enabled", enabled)


def get_spam_filter(chat_id: int) -> bool:
    return _get_filter_field(chat_id, "spam_enabled", default=False)


def set_swear_filter(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "swear_enabled", enabled)


def get_swear_filter(chat_id: int) -> bool:
    return _get_filter_field(chat_id, "swear_enabled", default=False)


def set_keywords_filter(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "keywords_enabled", enabled)


def get_keywords_filter(chat_id: int) -> bool:
    return _get_filter_field(chat_id, "keywords_enabled", default=False)


# ——— Join/Delete CRUD ———

def set_join_delete(chat_id: int, enabled: bool):
    _set_filter_field(chat_id, "join_delete_enabled", enabled)


def get_join_delete(chat_id: int) -> bool:
    return _get_filter_field(chat_id, "join_delete_enabled", default=False)


# ——— Keywords CRUD ———

def add_keyword(chat_id: int, keyword: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO keywords (chat_id, keyword) VALUES (%s, %s) ON CONFLICT (chat_id, keyword) DO NOTHING",
        (chat_id, keyword.strip().lower())
    )
    conn.commit()
    conn.close()


def remove_keyword(chat_id: int, keyword: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM keywords WHERE chat_id = %s AND keyword = %s", (chat_id, keyword.strip().lower()))
    conn.commit()
    conn.close()


def get_keywords(chat_id: int) -> list[str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT keyword FROM keywords WHERE chat_id = %s", (chat_id,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


# ——— Chats, Admins & User-Chats ———

def add_chat(chat_id: int, name: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO chats (chat_id, name) VALUES (%s, %s) ON CONFLICT (chat_id) DO NOTHING",
        (chat_id, name)
    )
    conn.commit()
    conn.close()


def get_chats() -> dict[int, str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT chat_id, name FROM chats")
    rows = c.fetchall()
    conn.close()
    return {chat_id: name for chat_id, name in rows}


def add_admin(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO admins (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
        (user_id,)
    )
    conn.commit()
    conn.close()


def get_admins() -> list[int]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def remove_admin(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()


def add_user_chat(user_id: int, chat_id: int, chat_name: str, is_message: bool = False):
    """
    Добавляет или обновляет запись о том, что пользователь является участником чата.
    Обновляет название чата в таблице chats и сохраняет метки первого/последнего появления.
    """
    now = datetime.utcnow()
    conn = get_connection()
    c = conn.cursor()
    # Обновляем или вставляем название чата
    c.execute(
        "INSERT INTO chats (chat_id, name) VALUES (%s, %s) ON CONFLICT (chat_id) DO UPDATE SET name = EXCLUDED.name",
        (chat_id, chat_name)
    )
    # Upsert в user_chats, сохраняем существующий message_count
    c.execute("""
        INSERT INTO user_chats (user_id, chat_id, first_seen, last_seen, message_count)
        VALUES (%s, %s, %s, %s,
                COALESCE((SELECT message_count FROM user_chats WHERE user_id=%s AND chat_id=%s), 0) + %s)
        ON CONFLICT (user_id, chat_id) DO UPDATE SET
            last_seen = EXCLUDED.last_seen,
            message_count = user_chats.message_count + %s
    """, (user_id, chat_id, now, now, user_id, chat_id, 1 if is_message else 0, 1 if is_message else 0))
    conn.commit()
    conn.close()


def remove_user_chat(user_id: int, chat_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_chats WHERE user_id = %s AND chat_id = %s", (user_id, chat_id))
    conn.commit()
    conn.close()


def get_user_chats(user_id: int) -> dict[int, str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT uc.chat_id, ch.name 
        FROM user_chats uc
        JOIN chats ch ON uc.chat_id = ch.chat_id
        WHERE uc.user_id = %s
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return {chat_id: name for chat_id, name in rows}


# ——— Warnings CRUD ———

def get_warn_count(user_id: int, chat_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT warn_count FROM warnings WHERE user_id=%s AND chat_id=%s", (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def add_warn(user_id: int, chat_id: int, username: str):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.utcnow()
    c.execute("""
        INSERT INTO warnings (user_id, chat_id, username, warn_count, last_warn)
        VALUES (%s, %s, %s, 1, %s)
        ON CONFLICT (user_id, chat_id) DO UPDATE SET
            username   = EXCLUDED.username,
            warn_count = warnings.warn_count + 1,
            last_warn  = EXCLUDED.last_warn
    """, (user_id, chat_id, username, now))
    conn.commit()
    conn.close()


def reset_warns(user_id: int, chat_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE warnings SET warn_count = 0, last_warn = NULL WHERE user_id=%s AND chat_id=%s",
              (user_id, chat_id))
    conn.commit()
    conn.close()


# ——— Mutes CRUD ———

def get_mute_info(user_id: int, chat_id: int) -> tuple[int, datetime | None]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT mute_count, last_mute FROM mutes WHERE user_id=%s AND chat_id=%s", (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    if not row:
        return 0, None
    count, last = row
    return count, last


def add_mute(user_id: int, chat_id: int, username: str):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.utcnow()
    c.execute("""
        INSERT INTO mutes (user_id, chat_id, username, last_mute)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, chat_id) DO UPDATE SET
            username   = EXCLUDED.username,
            mute_count = mutes.mute_count + 1,
            last_mute  = EXCLUDED.last_mute
    """, (user_id, chat_id, username, now))
    conn.commit()
    conn.close()


def reset_mutes(user_id: int, chat_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE mutes SET mute_count = 0, last_mute = NULL WHERE user_id=%s AND chat_id=%s", (user_id, chat_id))
    conn.commit()
    conn.close()


def reset_all_warns(chat_id: int) -> None:
    """
    Удаляет все варны (записи) из таблицы warnings для данного chat_id.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM warnings WHERE chat_id = %s", (chat_id,))
    conn.commit()
    cur.close()
    conn.close()


# ——— Aliases CRUD ———

def upsert_alias(chat_id: int, username: str, user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_aliases (chat_id, username, user_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (chat_id, username) DO UPDATE SET
            user_id = EXCLUDED.user_id
    """, (chat_id, username.lstrip('@').lower(), user_id))
    conn.commit()
    conn.close()


def resolve_username(chat_id: int, username: str) -> int | None:
    """
    Ищет в user_aliases по chat_id и username (без @), возвращает user_id или None.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user_id FROM user_aliases
        WHERE chat_id = %s AND username = %s
    """, (chat_id, username.lstrip('@').lower()))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


# ——— Welcome Messages CRUD ———

def set_welcome_message(chat_id: int, message: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO welcome_messages (chat_id, message)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET message = EXCLUDED.message
    """, (chat_id, message))
    conn.commit()
    conn.close()


def get_welcome_message(chat_id: int) -> str | None:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT message FROM welcome_messages WHERE chat_id = %s", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def set_welcome_delete_timeout(chat_id: int, timeout: int):
    """
    timeout: количество секунд (0 — отключить авто-удаление приветствия)
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO welcome_settings (chat_id, delete_timeout)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET delete_timeout = EXCLUDED.delete_timeout
    """, (chat_id, timeout))
    conn.commit()
    conn.close()


def get_welcome_delete_timeout(chat_id: int) -> int | None:
    """
    Возвращает:
      - число секунд,
      - None — если ещё не задано.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT delete_timeout FROM welcome_settings WHERE chat_id = %s", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


# ——— Chat Rules CRUD ———

def set_rules(chat_id: int, rules: str):
    """Устанавливает или обновляет правила для чата"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO chat_rules (chat_id, rules)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET rules = EXCLUDED.rules
    """, (chat_id, rules))
    conn.commit()
    conn.close()


def get_rules(chat_id: int) -> str | None:
    """Получает правила чата (или None, если не заданы)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT rules FROM chat_rules WHERE chat_id = %s", (chat_id,))
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
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT log_chat_id, is_logging_enabled
        FROM log_settings
        WHERE chat_id = %s
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
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO log_settings (chat_id, log_chat_id)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET log_chat_id = EXCLUDED.log_chat_id
    """, (chat_id, log_chat_id))
    conn.commit()
    conn.close()


def update_log_status(chat_id: int, enabled: bool) -> None:
    """
    Включает/выключает логирование для заданного chat_id.
    Если записи ещё не было, создаст её с log_chat_id = NULL.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO log_settings (chat_id, is_logging_enabled)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET is_logging_enabled = EXCLUDED.is_logging_enabled
    """, (chat_id, enabled))
    conn.commit()
    conn.close()
