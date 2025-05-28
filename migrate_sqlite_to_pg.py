import sqlite3
import psycopg2
from psycopg2 import sql
from datetime import datetime
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Путь к старой SQLite-базе
SQLITE_PATH = "bot_manager.db"


def get_sqlite_connection():
    return sqlite3.connect(SQLITE_PATH)


def get_pg_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def migrate_chats():
    """
    Перенос таблицы chats:
      - если в SQLite есть колонка member_count, берём её;
      - иначе выставляем member_count = 0.
    """
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()

    try:
        cur_sql.execute("SELECT chat_id, name, member_count FROM chats")
        raw_rows = cur_sql.fetchall()
        rows = [(cid, name, mc) for cid, name, mc in raw_rows]
    except sqlite3.OperationalError:
        cur_sql.execute("SELECT chat_id, name FROM chats")
        basic_rows = cur_sql.fetchall()
        rows = [(cid, name, 0) for cid, name in basic_rows]

    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for chat_id, name, member_count in rows:
        cur_pg.execute("""
            INSERT INTO chats (chat_id, name, member_count)
            VALUES (%s, %s, %s)
            ON CONFLICT (chat_id) DO NOTHING
        """, (chat_id, name, member_count))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(rows)} строк из chats")


def migrate_admins():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT user_id FROM admins")
        rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for (user_id,) in rows:
        cur_pg.execute("""
            INSERT INTO admins (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(rows)} строк из admins")


def migrate_user_info():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT user_id, username, first_name, last_name, last_seen FROM user_info")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for user_id, username, first_name, last_name, last_seen_str in raw_rows:
        last_seen = None
        if last_seen_str:
            try:
                last_seen = datetime.fromisoformat(last_seen_str)
            except (TypeError, ValueError):
                last_seen = None
        cur_pg.execute("""
            INSERT INTO user_info (user_id, username, first_name, last_name, last_seen)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, username, first_name, last_name, last_seen))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из user_info")


def migrate_user_chats():
    """
    Перенос таблицы user_chats:
      (user_id, chat_id, first_seen, last_seen, message_count).
    Если отсутствуют даты, ставим текущее время. Создаём строку в user_info,
    если её нет, чтобы пройти проверку FK.
    """
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("""
            SELECT user_id, chat_id, first_seen, last_seen, message_count
            FROM user_chats
        """)
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    now = datetime.utcnow()
    for user_id, chat_id, first_seen_str, last_seen_str, message_count in raw_rows:
        # Гарантируем, что в user_info есть запись, иначе FK-ошибка
        cur_pg.execute("""
            INSERT INTO user_info (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))

        # Если нет валидных дат, подставляем текущее время
        try:
            first_seen = datetime.fromisoformat(first_seen_str) if first_seen_str else now
        except (TypeError, ValueError):
            first_seen = now
        try:
            last_seen = datetime.fromisoformat(last_seen_str) if last_seen_str else now
        except (TypeError, ValueError):
            last_seen = now

        cur_pg.execute("""
            INSERT INTO user_chats (user_id, chat_id, first_seen, last_seen, message_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                first_seen = EXCLUDED.first_seen,
                last_seen = EXCLUDED.last_seen,
                message_count = EXCLUDED.message_count
        """, (user_id, chat_id, first_seen, last_seen, message_count))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из user_chats")


def migrate_filters():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("""
            SELECT chat_id, links_enabled, caps_enabled, spam_enabled,
                   swear_enabled, keywords_enabled, stickers_enabled, join_delete_enabled
            FROM filters
        """)
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for (chat_id, links_enabled, caps_enabled, spam_enabled,
         swear_enabled, keywords_enabled, stickers_enabled, join_delete_enabled) in raw_rows:
        cur_pg.execute("""
            INSERT INTO filters (
                chat_id, links_enabled, caps_enabled, spam_enabled,
                swear_enabled, keywords_enabled, stickers_enabled, join_delete_enabled
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chat_id) DO UPDATE SET
                links_enabled = EXCLUDED.links_enabled,
                caps_enabled = EXCLUDED.caps_enabled,
                spam_enabled = EXCLUDED.spam_enabled,
                swear_enabled = EXCLUDED.swear_enabled,
                keywords_enabled = EXCLUDED.keywords_enabled,
                stickers_enabled = EXCLUDED.stickers_enabled,
                join_delete_enabled = EXCLUDED.join_delete_enabled
        """, (
            chat_id, bool(links_enabled), bool(caps_enabled), bool(spam_enabled),
            bool(swear_enabled), bool(keywords_enabled), bool(stickers_enabled),
            bool(join_delete_enabled)
        ))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из filters")


def migrate_warnings():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("""
            SELECT user_id, chat_id, warn_count, last_warn, username
            FROM warnings
        """)
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for user_id, chat_id, warn_count, last_warn_str, username in raw_rows:
        # Убедимся, что user_info содержит user_id
        cur_pg.execute("""
            INSERT INTO user_info (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
        last_warn = None
        if last_warn_str:
            try:
                last_warn = datetime.fromisoformat(last_warn_str)
            except (TypeError, ValueError):
                last_warn = None
        cur_pg.execute("""
            INSERT INTO warnings (user_id, chat_id, warn_count, last_warn, username)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                warn_count = EXCLUDED.warn_count,
                last_warn = EXCLUDED.last_warn,
                username = EXCLUDED.username
        """, (user_id, chat_id, warn_count, last_warn, username))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из warnings")


def migrate_mutes():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("""
            SELECT user_id, chat_id, mute_count, last_mute, username
            FROM mutes
        """)
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for user_id, chat_id, mute_count, last_mute_str, username in raw_rows:
        # Убедимся, что user_info содержит user_id
        cur_pg.execute("""
            INSERT INTO user_info (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
        last_mute = None
        if last_mute_str:
            try:
                last_mute = datetime.fromisoformat(last_mute_str)
            except (TypeError, ValueError):
                last_mute = None
        cur_pg.execute("""
            INSERT INTO mutes (user_id, chat_id, mute_count, last_mute, username)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                mute_count = EXCLUDED.mute_count,
                last_mute = EXCLUDED.last_mute,
                username = EXCLUDED.username
        """, (user_id, chat_id, mute_count, last_mute, username))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из mutes")


def migrate_keywords():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT chat_id, keyword FROM keywords")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for chat_id, keyword in raw_rows:
        cur_pg.execute("""
            INSERT INTO keywords (chat_id, keyword)
            VALUES (%s, %s)
            ON CONFLICT (chat_id, keyword) DO NOTHING
        """, (chat_id, keyword))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из keywords")


def migrate_user_aliases():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT chat_id, username, user_id FROM user_aliases")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for chat_id, username, user_id in raw_rows:
        # Убедимся, что user_info содержит user_id
        cur_pg.execute("""
            INSERT INTO user_info (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
        cur_pg.execute("""
            INSERT INTO user_aliases (chat_id, username, user_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (chat_id, username) DO UPDATE SET
                user_id = EXCLUDED.user_id
        """, (chat_id, username, user_id))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из user_aliases")


def migrate_welcome_messages():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT chat_id, message FROM welcome_messages")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for chat_id, message in raw_rows:
        cur_pg.execute("""
            INSERT INTO welcome_messages (chat_id, message)
            VALUES (%s, %s)
            ON CONFLICT (chat_id) DO UPDATE SET
                message = EXCLUDED.message
        """, (chat_id, message))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из welcome_messages")


def migrate_chat_rules():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT chat_id, rules FROM chat_rules")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for chat_id, rules in raw_rows:
        cur_pg.execute("""
            INSERT INTO chat_rules (chat_id, rules)
            VALUES (%s, %s)
            ON CONFLICT (chat_id) DO UPDATE SET
                rules = EXCLUDED.rules
        """, (chat_id, rules))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из chat_rules")


def migrate_log_settings():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT chat_id, log_chat_id, is_logging_enabled FROM log_settings")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for chat_id, log_chat_id, is_logging_enabled in raw_rows:
        cur_pg.execute("""
            INSERT INTO log_settings (chat_id, log_chat_id, is_logging_enabled)
            VALUES (%s, %s, %s)
            ON CONFLICT (chat_id) DO UPDATE SET
                log_chat_id = EXCLUDED.log_chat_id,
                is_logging_enabled = EXCLUDED.is_logging_enabled
        """, (chat_id, log_chat_id, bool(is_logging_enabled)))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из log_settings")


def migrate_welcome_settings():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT chat_id, delete_timeout FROM welcome_settings")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for chat_id, delete_timeout in raw_rows:
        cur_pg.execute("""
            INSERT INTO welcome_settings (chat_id, delete_timeout)
            VALUES (%s, %s)
            ON CONFLICT (chat_id) DO UPDATE SET
                delete_timeout = EXCLUDED.delete_timeout
        """, (chat_id, delete_timeout))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из welcome_settings")


def migrate_bans():
    conn_sql = get_sqlite_connection()
    cur_sql = conn_sql.cursor()
    try:
        cur_sql.execute("SELECT user_id, chat_id, ban_count, last_ban, username FROM bans")
        raw_rows = cur_sql.fetchall()
    except sqlite3.OperationalError:
        raw_rows = []
    conn_sql.close()

    conn_pg = get_pg_connection()
    cur_pg = conn_pg.cursor()
    for user_id, chat_id, ban_count, last_ban_str, username in raw_rows:
        # Убедимся, что user_info содержит user_id
        cur_pg.execute("""
            INSERT INTO user_info (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
        last_ban = None
        if last_ban_str:
            try:
                last_ban = datetime.fromisoformat(last_ban_str)
            except (TypeError, ValueError):
                last_ban = None
        cur_pg.execute("""
            INSERT INTO bans (user_id, chat_id, ban_count, last_ban, username)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                ban_count = EXCLUDED.ban_count,
                last_ban = EXCLUDED.last_ban,
                username = EXCLUDED.username
        """, (user_id, chat_id, ban_count, last_ban, username))
    conn_pg.commit()
    cur_pg.close()
    conn_pg.close()
    print(f"  ✓ Перенесено {len(raw_rows)} строк из bans")


def main():
    print("Запуск миграции из SQLite → PostgreSQL …")
    migrate_chats()
    migrate_admins()
    migrate_user_info()
    migrate_user_chats()
    migrate_filters()
    migrate_warnings()
    migrate_mutes()
    migrate_keywords()
    migrate_user_aliases()
    migrate_welcome_messages()
    migrate_chat_rules()
    migrate_log_settings()
    migrate_welcome_settings()
    migrate_bans()
    print("Миграция завершена.")


if __name__ == "__main__":
    main()
