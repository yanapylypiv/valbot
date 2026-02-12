import aiosqlite

DB_NAME = "valentines.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            group_name TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS valentines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_telegram_id INTEGER,
            receiver_first_name TEXT,
            receiver_last_name TEXT,
            receiver_group TEXT,
            text TEXT,
            is_anonymous INTEGER,
            delivered INTEGER DEFAULT 0
        )
        """)

        await db.commit()
