import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram import F

API_TOKEN = "7613137152:AAHTIPaiCPwJ9QbLI3teX217CA293RoD2EE"
ADMIN_ID = 6535216093  # replace with your telegram id

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ------------------- DB INIT --------------------
def init_db():
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    # numbers table
    c.execute("""CREATE TABLE IF NOT EXISTS numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT UNIQUE,
        used INTEGER DEFAULT 0
    )""")
    # users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")
    # gift codes table
    c.execute("""CREATE TABLE IF NOT EXISTS gift_codes (
        code TEXT PRIMARY KEY,
        value INTEGER,
        used_by INTEGER
    )""")
    conn.commit()
    conn.close()

init_db()

# ------------------- Helper --------------------
def add_balance(user_id: int, amount: int):
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_balance(user_id: int) -> int:
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    bal = c.fetchone()[0]
    conn.close()
    return bal

# ------------------- Commands --------------------

# /upload (admin only)
@dp.message(Command("upload"))
async def upload_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Only admin can upload numbers.")
    await message.reply("📤 Please send the .txt file with numbers (one per line).")

# Handle file upload
@dp.message(F.document)
async def file_upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    file = await bot.get_file(message.document.file_id)
    path = file.file_path
    await bot.download_file(path, "numbers.txt")

    count = 0
    with open("numbers.txt", "r") as f:
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
                    pass
        conn.commit()
        conn.close()
    await message.reply(f"✅ Uploaded {count} new numbers successfully.")

# /getnumber
@dp.message(Command("getnumber"))
async def get_number(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    if bal < 1:
        return await message.reply("❌ You don't have enough balance. Use /addbalance or redeem a gift code.")
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("SELECT id, number FROM numbers WHERE used = 0 LIMIT 1")
    row = c.fetchone()
    if row:
        # deduct balance
        c.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
        c.execute("UPDATE numbers SET used = 1 WHERE id = ?", (row[0],))
        conn.commit()
        await message.reply(f"🎁 Your Number: `{row[1]}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("😢 Sorry, no numbers left.")
    conn.close()

# /balance
@dp.message(Command("balance"))
async def balance_cmd(message: types.Message):
    bal = get_balance(message.from_user.id)
    await message.reply(f"💰 Your current balance: {bal} coins")

# /addbalance info
@dp.message(Command("addbalance"))
async def add_balance_info(message: types.Message):
    await message.reply(
        "To add balance, please contact admin:\nTelegram: @Ox_Anonymous",
        parse_mode=ParseMode.MARKDOWN
    )

# /redeem (2-step process)
pending_redeem = {}  # user_id -> waiting state

@dp.message(Command("redeem"))
async def redeem_start(message: types.Message):
    pending_redeem[message.from_user.id] = True
    await message.reply("Please send your gift code in the next message.")

@dp.message(F.text)
async def redeem_code(message: types.Message):
    user_id = message.from_user.id
    if user_id in pending_redeem and pending_redeem[user_id]:
        code = message.text.strip()
        conn = sqlite3.connect("numbers.db")
        c = conn.cursor()
        c.execute("SELECT value, used_by FROM gift_codes WHERE code = ?", (code,))
        row = c.fetchone()
        if row:
            if row[1] is None:
                c.execute("UPDATE gift_codes SET used_by = ? WHERE code = ?", (user_id, code))
                add_balance(user_id, row[0])
                await message.reply(f"✅ Code redeemed! {row[0]} coins added.")
            else:
                await message.reply("❌ This code has already been used.")
        else:
            await message.reply("❌ Invalid gift code.")
        conn.commit()
        conn.close()
        pending_redeem[user_id] = False

# Admin-only: generate gift code (one-time use)
@dp.message(Command("gen_code"))
async def gen_code(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 3:
        return await message.reply("Usage: /gen_code CODE VALUE")
    code, value = parts[1], int(parts[2])
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO gift_codes (code, value) VALUES (?, ?)", (code, value))
        conn.commit()
        await message.reply(f"Gift code '{code}' created for {value} coins.")
    except sqlite3.IntegrityError:
        await message.reply("❌ Code already exists.")
    conn.close()

# /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply("🙏 Welcome! Use /getnumber to get a number (costs 1 coin).")

# ------------------- Run --------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
