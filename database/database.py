import sqlite3
import datetime
from pathlib import Path
from typing import Tuple

current_directory = Path(__file__).resolve().parent
file_name = 'database.db'
file_path = current_directory / file_name

connect = sqlite3.connect(file_path)
cursor = connect.cursor()


def create_user_table() -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_table (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id               INTEGER NOT NULL,
            queue_index           INTEGER DEFAULT 0,
            last_activity_time    INTEGER DEFAULT 0,
            notifications1        INTEGER DEFAULT 1,
            notifications2        INTEGER DEFAULT 1,
            queue_visibility      INTEGER DEFAULT 1,
            top_visibility        INTEGER DEFAULT 1,
            target_notifications  INTEGER DEFAULT 1,
            permission_trusting   INTEGER DEFAULT 0,
            permission_private    INTEGER DEFAULT 0,
            permission_admin      INTEGER DEFAULT 0

        )
    '''
    )
    connect.commit()


def create_state_table() -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS state_table (
            name  TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        )
    '''
    )
    cursor.execute('''
        INSERT OR IGNORE INTO state_table (name, value)
        VALUES ('worked_fight', 0)
    '''
    )
    connect.commit()

    
def create_tops_table() -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_top_table (
            user_id                 INTEGER PRIMARY KEY,
            visits                  INTEGER DEFAULT 0,
            wins                    INTEGER DEFAULT 0,
            hits_dealt              INTEGER DEFAULT 0,
            friendly_fire_hits      INTEGER DEFAULT 0,
            blocked_hits            INTEGER DEFAULT 0,
            misses                  INTEGER DEFAULT 0,
            damage_dealt            INTEGER DEFAULT 0,
            pings                   INTEGER DEFAULT 0,
            shields_used            INTEGER DEFAULT 0,
            successful_shield_usage INTEGER DEFAULT 0,
            hits_blocked_by_shield  INTEGER DEFAULT 0,
            players_killed          INTEGER DEFAULT 0,
            visits_strick           INTEGER DEFAULT 0
        )
    '''
    )
    cursor.execute('''
        INSERT OR IGNORE INTO user_top_table (user_id)
        SELECT user_id
        FROM user_table;
    ''')

    connect.commit()


async def new_user(user_id: int) -> None:
    cursor.execute(
        "SELECT user_id FROM user_table WHERE user_id = ?",
        (user_id,)
    )
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute(
            "INSERT INTO user_table (user_id, last_activity_time) VALUES (?, ?)", 
            (user_id, datetime.datetime.now().timestamp())
        )
        
        cursor.execute(
            "INSERT INTO user_top_table (user_id) VALUES (?)",
            (user_id,)
        )
        connect.commit()


async def set_user(user_id: int, field_name: str, new_value: int) -> None:
    cursor.execute(
        "SELECT user_id FROM user_table WHERE user_id = ?", 
        (user_id,)
    )
    existing_user = cursor.fetchone()

    if not existing_user:
        await new_user(user_id)
    
    cursor.execute(
        "UPDATE user_table SET {} = ? WHERE user_id = ?".format(field_name), 
        (new_value, user_id)
    )
    connect.commit()


def set_state(field_name: str, new_value: int) -> None:
    cursor.execute(
        "UPDATE state_table SET value = ? WHERE name = ?",
        (new_value, field_name)
    )
    connect.commit()


async def get_state(field_name: str) -> int:
    stat_info = cursor.execute(
        "SELECT value FROM state_table WHERE name = ?",
        (field_name,)
    ).fetchone()

    if stat_info is None:
        return 0
    else:
        return stat_info[0]


async def get_user(user_id: int, *field_name: str) -> Tuple[int, ...]:
    cursor.execute(
        "SELECT user_id FROM user_table WHERE user_id = ?", 
        (user_id,)
    )
    existing_user = cursor.fetchone()

    if not existing_user:
        await new_user(user_id)
    
    field_name = ", ".join(field_name)
    user_info = cursor.execute(
        "SELECT {} FROM user_table WHERE user_id = ?".format(field_name), 
        (user_id,)
    ).fetchone()
    
    return user_info


def update_time(func):
    async def wrapper(client, message):
        await set_user(
            message.from_user.id, 
            "last_activity_time", 
            datetime.datetime.now().timestamp()
        )
        await func(client, message)
    return wrapper

# Tops
async def increment_user_field(user_id: int, field_name: str,  increment_value: int) -> None:
    cursor.execute(
        "UPDATE user_top_table SET {field} = {field} + ? WHERE user_id = ?".format(field=field_name), 
        (increment_value, user_id)
    )
    connect.commit()


def create_tables():
    create_user_table()
    create_state_table()
    create_tops_table()


create_tables()
