import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8650148089:AAEBZIxFU1mBgQbpoYuOi8KT37V_GER89Dg"
ADMIN_ID = 8007670371

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DB =================
async def init_db():
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            chust TEXT,
            photo TEXT,
            clicks INTEGER DEFAULT 0
        )
        """)
        await db.commit()

# ================= KEYBOARD =================
async def get_keyboard():
    kb = []
    async with aiosqlite.connect("db.sqlite3") as db:
        async with db.execute("SELECT id, name FROM players") as cursor:
            async for row in cursor:
                kb.append([
                    InlineKeyboardButton(
                        text=row[1],
                        callback_data=f"player_{row[0]}"
                    )
                ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ================= START =================
@dp.message(commands=["start"])
async def start(msg: types.Message):
    kb = await get_keyboard()
    await msg.answer("🎮 O‘yinchini tanla:", reply_markup=kb)

# ================= CLICK =================
@dp.callback_query()
async def click(call: types.CallbackQuery):
    if call.data.startswith("player_"):
        pid = int(call.data.split("_")[1])

        async with aiosqlite.connect("db.sqlite3") as db:
            async with db.execute(
                "SELECT name, chust, photo, clicks FROM players WHERE id=?",
                (pid,)
            ) as cur:
                row = await cur.fetchone()

            if row:
                name, chust, photo, clicks = row

                await db.execute(
                    "UPDATE players SET clicks = clicks + 1 WHERE id=?",
                    (pid,)
                )
                await db.commit()

                text = f"🎮 {name}\n\n📋 Chust:\n{chust}\n\n🔥 Bosilgan: {clicks+1}"

                await call.message.edit_media(
                    media=types.InputMediaPhoto(
                        media=photo,
                        caption=text
                    ),
                    reply_markup=await get_keyboard()
                )

        await call.answer()

# ================= ADMIN ADD =================
user_state = {}

@dp.message(commands=["add"])
async def add(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Ruxsat yo‘q")

    user_state[msg.from_user.id] = {"step": "name"}
    await msg.answer("👤 Ism yubor:")

@dp.message()
async def admin_flow(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return

    if msg.from_user.id not in user_state:
        return

    step = user_state[msg.from_user.id]["step"]

    if step == "name":
        user_state[msg.from_user.id]["name"] = msg.text
        user_state[msg.from_user.id]["step"] = "chust"
        await msg.answer("📋 Chust yubor:")

    elif step == "chust":
        user_state[msg.from_user.id]["chust"] = msg.text
        user_state[msg.from_user.id]["step"] = "photo"
        await msg.answer("🖼 Rasm yubor:")

    elif step == "photo":
        if not msg.photo:
            return await msg.answer("❌ Rasm yubor")

        photo_id = msg.photo[-1].file_id
        data = user_state[msg.from_user.id]

        async with aiosqlite.connect("db.sqlite3") as db:
            await db.execute(
                "INSERT INTO players (name, chust, photo) VALUES (?, ?, ?)",
                (data["name"], data["chust"], photo_id)
            )
            await db.commit()

        await msg.answer("✅ Qo‘shildi!")
        del user_state[msg.from_user.id]

# ================= RUN =================
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())