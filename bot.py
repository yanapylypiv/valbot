import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
import aiosqlite
from database import init_db

BOT_TOKEN = "8539494327:AAEs__HILnY3FupG7-M-DfyJdVWOoUT3sxs"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "valentines.db"

# ------------------ СТАНИ ------------------

class Register(StatesGroup):
    first_name = State()
    last_name = State()
    group_name = State()

class Valentine(StatesGroup):
    receiver_name = State()
    receiver_group = State()
    text = State()
    anonymous = State()

# ------------------ СТАРТ ------------------

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await message.answer("Введіть ваше імʼя:")
    await state.set_state(Register.first_name)

@dp.message(Register.first_name)
async def reg_first(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await message.answer("Введіть ваше прізвище:")
    await state.set_state(Register.last_name)

@dp.message(Register.last_name)
async def reg_last(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await message.answer("Введіть вашу групу:")
    await state.set_state(Register.group_name)

@dp.message(Register.group_name)
async def reg_group(message: Message, state: FSMContext):
    data = await state.get_data()

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT OR REPLACE INTO users (telegram_id, first_name, last_name, group_name)
        VALUES (?, ?, ?, ?)
        """, (
            message.from_user.id,
            data["first_name"],
            data["last_name"],
            message.text.strip()
        ))
        await db.commit()

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="💌 Надіслати валентинку")]],
        resize_keyboard=True
    )

    await message.answer("Реєстрація завершена ✅", reply_markup=kb)
    await state.clear()

# ------------------ НАДСИЛАННЯ ------------------

@dp.message(F.text == "💌 Надіслати валентинку")
async def new_valentine(message: Message, state: FSMContext):
    await message.answer("Введіть імʼя та прізвище отримувача:")
    await state.set_state(Valentine.receiver_name)

@dp.message(Valentine.receiver_name)
async def receiver_name(message: Message, state: FSMContext):
    parts = message.text.strip().split(" ")
    if len(parts) < 2:
        await message.answer("Введіть імʼя та прізвище через пробіл.")
        return

    await state.update_data(
        receiver_first_name=parts[0],
        receiver_last_name=parts[1]
    )

    await message.answer("Введіть групу отримувача:")
    await state.set_state(Valentine.receiver_group)

@dp.message(Valentine.receiver_group)
async def receiver_group(message: Message, state: FSMContext):
    await state.update_data(receiver_group=message.text.strip())

    data = await state.get_data()

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
        SELECT * FROM users
        WHERE first_name=? AND last_name=? AND group_name=?
        """, (
            data["receiver_first_name"],
            data["receiver_last_name"],
            data["receiver_group"]
        )) as cursor:
            user = await cursor.fetchone()

    if not user:
        await message.answer(
            "Цей користувач ще не активував бот таємної валентинки, "
            "але ти можеш написати її. Можливо скоро він зʼявиться тут "
            "та отримає твоє повідомлення 14 лютого 💌"
        )

    await message.answer("Напишіть текст валентинки:")
    await state.set_state(Valentine.text)

@dp.message(Valentine.text)
async def valentine_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Анонімно")],
            [KeyboardButton(text="З підписом")]
        ],
        resize_keyboard=True
    )

    await message.answer("Як надіслати?", reply_markup=kb)
    await state.set_state(Valentine.anonymous)

@dp.message(Valentine.anonymous)
async def save_valentine(message: Message, state: FSMContext):
    data = await state.get_data()

    is_anon = 1 if message.text == "Анонімно" else 0

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO valentines
        (sender_telegram_id, receiver_first_name, receiver_last_name,
         receiver_group, text, is_anonymous)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message.from_user.id,
            data["receiver_first_name"],
            data["receiver_last_name"],
            data["receiver_group"],
            data["text"],
            is_anon
        ))
        await db.commit()

    await message.answer("Валентинку збережено 💌", reply_markup=ReplyKeyboardRemove())
    await state.clear()

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
