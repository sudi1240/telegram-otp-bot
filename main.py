import os
import sqlite3
import secrets
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram import F

API_TOKEN = "7613137152:AAHTIPaiCPwJ9QbLI3teX217CA293RoD2EE"  # <-- এখানে Bot token দাও
ADMIN_ID = 6535216093  # <-- তোমার Telegram numeric ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ===================== DB INIT =====================
def init_db():
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT UNIQUE,
        used INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS giftcodes (
        code TEXT PRIMARY KEY,
        value INTEGER,
        used_by INTEGER
    )""")
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_balance(user_id: int) -> int:
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    bal = c.fetchone()[0]
    conn.close()
    return bal

def add_balance(user_id: int, amount: int):
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# ===================== HANDLERS =====================

# START
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    bal = get_balance(message.from_user.id)
    await message.reply(
        f"🙏 Jai Shree Ram!\n\n"
        f"Commands:\n"
        f"/getnumber - Get a 12-digit number (1 coin)\n"
        f"/balance - Check balance\n"
        f"/redeem - Redeem gift code\n"
        f"/addbalance - How to add balance\n\n"
        f"Your current balance: {bal} coins"
    )

# BALANCE
@dp.message(Command("balance"))
async def balance_cmd(message: types.Message):
    bal = get_balance(message.from_user.id)
    await message.reply(f"💰 Your balance: {bal} coins")

# ADD BALANCE INFO
@dp.message(Command("addbalance"))
async def addbalance_cmd(message: types.Message):
    await message.reply("For add balance contact admin (admin telegram id: @Ox_Anonymous)")

# GET NUMBER
@dp.message(Command("getnumber"))
async def get_number(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    if bal < 1:
        return await message.reply("⚠️ You need 1 coin to get a number. Use /redeem to redeem gift code.")
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("SELECT id, number FROM numbers WHERE used=0 LIMIT 1")
    row = c.fetchone()
    if row:
        c.execute("UPDATE numbers SET used=1 WHERE id=?", (row[0],))
        c.execute("UPDATE users SET balance = balance - 1 WHERE user_id=?", (user_id,))
        conn.commit()
        await message.reply(f"🎁 Your Number: {row[1]}")
    else:
        await message.reply("😢 Sorry, no numbers left.")
    conn.close()

# UPLOAD
@dp.message(Command("upload"))
async def upload_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Only admin can upload.")
    await message.reply("📤 Send .txt file with numbers (12 digit, one per line).")

@dp.message(F.document)
async def handle_file_upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    file = await bot.get_file(message.document.file_id)
    file_name = "numbers.txt"
    await bot.download_file(file.file_path, file_name)
    count = 0
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    with open(file_name, "r") as f:
        for line in f:
            number = line.strip()
            if len(number) == 12 and number.isdigit():
                try:
                    c.execute("INSERT INTO numbers (number) VALUES (?)", (number,))
                    count += 1
                except sqlite3.IntegrityError:
                    pass
    conn.commit()
    conn.close()
    await message.reply(f"✅ Uploaded {count} numbers.")

# ========== GIFT CODE ==========

# Track redeem mode
redeem_waiting = {}
gengift_waiting = {}

def generate_code():
    return secrets.token_hex(4).upper()

@dp.message(Command("gengift"))
async def gengift_step1(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("Not authorized!")
    gengift_waiting[message.from_user.id] = "ask_value"
    await message.reply("Please enter gift value (number of coins):")

@dp.message(Command("redeem"))
async def redeem_start(message: types.Message):
    redeem_waiting[message.from_user.id] = True
    await message.reply("Please send your gift code:")

@dp.message()
async def all_messages(message: types.Message):
    user_id = message.from_user.id

    # Handle gift generation flow
    if gengift_waiting.get(user_id) == "ask_value":
        if not message.text.isdigit():
            return await message.reply("Please send a valid number.")
        value = int(message.text)
        code = generate_code()
        conn = sqlite3.connect("numbers.db")
        c = conn.cursor()
        c.execute("INSERT INTO giftcodes (code,value,used_by) VALUES (?, ?, NULL)", (code, value))
        conn.commit()
        conn.close()
        gengift_waiting.pop(user_id, None)
        return await message.reply(f"🎟 Gift code generated:\nCode: {code}\nValue: {value} coins")

    # Handle redeem flow
    if redeem_waiting.get(user_id):
        code = message.text.strip().upper()
        conn = sqlite3.connect("numbers.db")
        c = conn.cursor()
        c.execute("SELECT value, used_by FROM giftcodes WHERE code=?", (code,))
        row = c.fetchone()
        if not row:
            await message.reply("❌ Invalid gift code.")
        elif row[1] is not None:
            await message.reply("❌ This gift code has already been used.")
        else:
            value = row[0]
            add_balance(user_id, value)
            c.execute("UPDATE giftcodes SET used_by=? WHERE code=?", (user_id, code))
            conn.commit()
            await message.reply(f"✅ Gift code redeemed! {value} coin(s) added.")
        conn.close()
        redeem_waiting.pop(user_id, None)

# ===================== RUN =====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
