import asyncio
import aiosqlite
from aiogram import Bot

BOT_TOKEN = "8539494327:AAEs__HILnY3FupG7-M-DfyJdVWOoUT3sxs"
bot = Bot(token=BOT_TOKEN)

DB_NAME = "valentines.db"

async def send_all():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM valentines WHERE delivered=0") as cursor:
            rows = await cursor.fetchall()

        for row in rows:
            receiver_first = row[2]
            receiver_last = row[3]
            receiver_group = row[4]
            text = row[5]
            is_anon = row[6]

            async with db.execute("""
            SELECT telegram_id FROM users
            WHERE first_name=? AND last_name=? AND group_name=?
            """, (receiver_first, receiver_last, receiver_group)) as cur:
                user = await cur.fetchone()

            if user:
                msg = f"💌 Вам валентинка!\n\n{text}\n\n"
                msg += "— Анонім" if is_anon else "— З підписом"

                await bot.send_message(user[0], msg)

        await db.execute("UPDATE valentines SET delivered=1")
        await db.commit()

asyncio.run(send_all())

