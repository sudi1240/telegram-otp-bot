import os
import sqlite3
import secrets
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "7613137152:AAHTIPaiCPwJ9QbLI3teX217CA293RoD2EE"  # Replace with your bot token
ADMIN_ID = 6535216093  # Replace with your Telegram numeric ID
CHANNEL_USERNAME = "@WinzoHack_Tips_Tricks"  # Replace with your channel username

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# === DB INIT ===
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
        balance INTEGER DEFAULT 0,
        referred_by INTEGER,
        joined_channel INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS giftcodes (
        code TEXT PRIMARY KEY,
        value INTEGER,
        used_by INTEGER
    )""")
    conn.commit()
    conn.close()

init_db()

# === Helpers ===
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

async def check_channel_join(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# === Commands ===

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_by = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()

    if not user:
        # First signup
        referred_by = ref_by if ref_by != user_id else None
        c.execute("INSERT INTO users (user_id, balance, referred_by) VALUES (?, ?, ?)", (user_id, 5, referred_by))
        if referred_by:
            add_balance(referred_by, 5)
            await bot.send_message(referred_by, f"🎉 You earned 5 coins! Your friend just signed up using your referral link.")
        await message.reply("🎉 Welcome! You received 5 signup coins.")
    conn.commit()
    conn.close()

    # Check channel join
    joined = await check_channel_join(user_id)
    if joined:
        conn = sqlite3.connect("numbers.db")
        c = conn.cursor()
        c.execute("SELECT joined_channel FROM users WHERE user_id=?", (user_id,))
        joined_status = c.fetchone()[0]
        if joined_status == 0:
            c.execute("UPDATE users SET joined_channel=1 WHERE user_id=?", (user_id,))
            add_balance(user_id, 2)
            await message.reply("✅ Thanks for joining our channel. You've earned 2 coins!")
        conn.commit()
        conn.close()
    else:
        join_btn = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")]]
        )
        await message.reply("👋 Please join our channel to earn 2 coins!", reply_markup=join_btn)

    bal = get_balance(user_id)
    await message.reply(
        f"🙏 <b>Jai Shree Ram!</b>\n\n"
        f"/getnumber - Get a 12-digit number (1 coin)\n"
        f"/balance - Check balance\n"
        f"/refer - Share & Earn\n"
        f"/redeem - Redeem gift code\n"
        f"/addbalance - How to add balance\n"
        f"/gengift - (Admin only)\n"
        f"/upload - (Admin only)\n\n"
        f"💰 Your Balance: {bal} coins"
    )

@dp.message(Command("balance"))
async def balance_cmd(message: types.Message):
    bal = get_balance(message.from_user.id)
    await message.reply(f"💰 Your balance: {bal} coins")

@dp.message(Command("addbalance"))
async def addbalance_cmd(message: types.Message):
    await message.reply("💳 Contact admin to add balance: @Ox_Anonymous")

@dp.message(Command("refer"))
async def refer_cmd(message: types.Message):
    user_id = message.from_user.id
    link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    await message.reply(f"📢 Invite friends and earn 5 coins!\n\n🔗 Your link:\n<code>{link}</code>")

@dp.message(Command("getnumber"))
async def getnumber_cmd(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    if bal < 1:
        return await message.reply("⚠️ You need 1 coin to get a number.")
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    c.execute("SELECT id, number FROM numbers WHERE used=0 LIMIT 1")
    row = c.fetchone()
    if row:
        c.execute("UPDATE numbers SET used=1 WHERE id=?", (row[0],))
        c.execute("UPDATE users SET balance = balance - 1 WHERE user_id=?", (user_id,))
        conn.commit()
        await message.reply(f"🎁 Your Number: <code>{row[1]}</code>")
    else:
        await message.reply("❌ No more numbers left.")
    conn.close()

# === Admin Upload ===
@dp.message(Command("upload"))
async def upload_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Only admin can upload.")
    await message.reply("📤 Send .txt file with numbers (12 digits per line)")

@dp.message(F.document)
async def handle_file(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    file = await bot.get_file(message.document.file_id)
    await bot.download_file(file.file_path, "numbers.txt")
    count = 0
    conn = sqlite3.connect("numbers.db")
    c = conn.cursor()
    with open("numbers.txt", "r") as f:
        for line in f:
            num = line.strip()
            if len(num) == 12 and num.isdigit():
                try:
                    c.execute("INSERT INTO numbers (number) VALUES (?)", (num,))
                    count += 1
                except sqlite3.IntegrityError:
                    pass
    conn.commit()
    conn.close()
    await message.reply(f"✅ Uploaded {count} new numbers.")

# === Gift Code ===
gengift_state = {}
redeem_state = {}

def generate_code():
    return secrets.token_hex(4).upper()

@dp.message(Command("gengift"))
async def gengift(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Not authorized.")
    gengift_state[message.from_user.id] = True
    await message.reply("✏️ Enter gift coin amount:")

@dp.message(Command("redeem"))
async def redeem(message: types.Message):
    redeem_state[message.from_user.id] = True
    await message.reply("🎟 Send your gift code:")

@dp.message()
async def text_handler(message: types.Message):
    uid = message.from_user.id

    # Generate Gift
    if gengift_state.get(uid):
        if not message.text.isdigit():
            return await message.reply("❌ Send a valid number.")
        value = int(message.text)
        code = generate_code()
        conn = sqlite3.connect("numbers.db")
        c = conn.cursor()
        c.execute("INSERT INTO giftcodes (code, value, used_by) VALUES (?, ?, NULL)", (code, value))
        conn.commit()
        conn.close()
        gengift_state.pop(uid, None)
        await message.reply(f"🎁 Gift Code Generated:\n\n<code>{code}</code>\n💰 Value: {value} coins\n\n🖱️ Tap to copy.")

    # Redeem Gift
    elif redeem_state.get(uid):
        code = message.text.strip().upper()
        conn = sqlite3.connect("numbers.db")
        c = conn.cursor()
        c.execute("SELECT value, used_by FROM giftcodes WHERE code=?", (code,))
        row = c.fetchone()
        if not row:
            await message.reply("❌ Invalid code.")
        elif row[1]:
            await message.reply("⚠️ Code already used.")
        else:
            value = row[0]
            add_balance(uid, value)
            c.execute("UPDATE giftcodes SET used_by=? WHERE code=?", (uid, code))
            conn.commit()
            await message.reply(f"✅ Redeemed successfully!\n💰 You received {value} coins.")
        conn.close()
        redeem_state.pop(uid, None)

# === Main ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
