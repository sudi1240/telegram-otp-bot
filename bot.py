import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Make sure to set in Railway/Render

# --- SERVER 1: Receive-SMSS ---
def get_server_1_numbers():
    try:
        url = "https://receive-smss.com/"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        blocks = soup.select(".number-boxes-item")
        numbers = []
        for block in blocks[:5]:
            number = block.select_one(".number-boxes-item-number").text.strip()
            numbers.append(number)
        return numbers or ["❌ No numbers found"]
    except Exception as e:
        print("Server 1 error:", e)
        return ["❌ Error fetching numbers"]

# --- SERVER 2: SMS-Online ---
def get_server_2_numbers():
    try:
        url = "https://sms-online.co/receive-free-sms"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        blocks = soup.select(".number-boxes-item")
        numbers = []
        for block in blocks[:5]:
            number = block.select_one(".number-boxes-item-number").text.strip()
            numbers.append(number)
        return numbers or ["❌ No numbers found"]
    except Exception as e:
        print("Server 2 error:", e)
        return ["❌ Error fetching numbers"]

# --- SERVER 3: FreePhoneNum ---
def get_server_3_numbers():
    try:
        url = "https://freephonenum.com/"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        items = soup.select("a.number-box")
        numbers = []
        for a in items[:5]:
            num = a.select_one("span.number-box-text")
            if num:
                numbers.append(num.text.strip())
        return numbers or ["❌ No numbers found"]
    except Exception as e:
        print("Server 3 error:", e)
        return ["❌ Error fetching numbers"]

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 Server 1", callback_data="server_1")],
        [InlineKeyboardButton("🔵 Server 2", callback_data="server_2")],
        [InlineKeyboardButton("🟣 Server 3", callback_data="server_3")],
    ]
    await update.message.reply_text("Choose a server to view available numbers:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("server_"):
        server_func = {
            "server_1": get_server_1_numbers,
            "server_2": get_server_2_numbers,
            "server_3": get_server_3_numbers,
        }[data]
        numbers = server_func()
        keyboard = [
            [InlineKeyboardButton(num, callback_data=f"num_{data}_{num}")] for num in numbers
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
        await query.edit_message_text("Select a number:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "back":
        await start(update, context)
        return

    if data.startswith("num_"):
        _, server, *num_parts = data.split("_")
        number = "_".join(num_parts)
        inbox_func = {
            "server": get_server_1_inbox if server == "server" else None,
            "1": get_server_1_inbox,
            "2": get_server_2_inbox,
            "3": get_server_3_inbox,
        }.get(server.split("_")[-1], lambda x: ["❌ Invalid server"])
        inbox = inbox_func(number)
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=f"server_{server}")]]
        await query.edit_message_text(f"Inbox for {number}:\n\n" + "\n\n".join(inbox), reply_markup=InlineKeyboardMarkup(keyboard))

# --- MAIN ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Bot running...")
    app.run_polling()
