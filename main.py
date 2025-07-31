import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold
from aiogram import F
import asyncio

API_TOKEN = "7613137152:AAHjWxkkepX75vawapTDl7bwnY60--TvA3E"
ADMIN_ID = 6535216093  # 🔐 Replace with your Telegram user ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 📁 DB init
def init_db():
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT UNIQUE,
        used INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

init_db()

# ✅ Upload handler
@dp.message(Command("upload"))
async def handle_upload_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Only admin can upload numbers.")
    
    await message.reply("📤 Please send the .txt file with numbers (one per line).")

@dp.message(F.document)
async def handle_file_upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    file = await bot.get_file(message.document.file_id)
    file_path = file.file_path
    file_name = "numbers.txt"
    await bot.download_file(file_path, file_name)

    count = 0
    with open(file_name, "r") as f:
        lines = f.readlines()
        conn = sqlite3.connect("numbers.db")
        c = conn.cursor()
        for line in lines:
            number = line.strip()
            if len(number) == 12 and number.isdigit():
                try:
                    c.execute("INSERT INTO numbers (number) VALUES (?)", (number,))
                    count += 1
                except sqlite3.IntegrityError:
                    pass  # already exists
        conn.commit()
        conn.close()
    await message.reply(f"✅ Uploaded {count} new numbers successfully.")

# 🚀 User gets number
@dp.message(Command("getnumber"))
async def get_number(message: types.Message):
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("SELECT id, number FROM numbers WHERE used = 0 LIMIT 1")
    row = c.fetchone()
    if row:
        c.execute("UPDATE numbers SET used = 1 WHERE id = ?", (row[0],))
        conn.commit()
        await message.reply(f"🎁 Your Number: {row[1]}", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("😢 Sorry, no numbers left.")
    conn.close()

# 🏁 Start command
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply("🙏 Jai Shree Ram! Type /getnumber to get your 12-digit Aadhar number.")

# 🔁 Run the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
