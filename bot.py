import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# =====================
# SCRAPING FUNCTIONS
# =====================

def get_numbers(server):
    try:
        if server == "server_1":
            url = "https://receive-smss.com/"
            base = "https://receive-smss.com"
            selector = ".number-boxes-item > a"
        elif server == "server_2":
            url = "https://sms-online.co/receive-free-sms"
            base = "https://sms-online.co"
            selector = ".number-boxes-item > a"
        elif server == "server_3":
            url = "https://freephonenum.com/"
            base = "https://freephonenum.com"
            selector = "ul.list-unstyled li a"
        else:
            return []

        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        elements = soup.select(selector)
        numbers = []
        for el in elements[:5]:
            text = el.text.strip().replace("\n", "").replace("\r", "")
            href = el.get("href", "")
            full_url = f"{base}{href}"
            numbers.append((text, full_url))
        return numbers
    except Exception as e:
        print(f"[get_numbers] {server}: {e}")
        return []

def get_inbox(server, number_url):
    try:
        r = requests.get(number_url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        msgs = soup.select(".sms-item") or soup.select(".table tbody tr")
        if not msgs:
            return ["No messages yet. Try again later."]
        
        inbox = []
        for msg in msgs[:10]:
            sender = msg.select_one(".sms-sender") or msg.select_one("td:nth-child(2)")
            text = msg.select_one(".sms-text") or msg.select_one("td:nth-child(3)")
            time = msg.select_one(".sms-date") or msg.select_one("td:nth-child(1)")
            sender_txt = sender.text.strip() if sender else "Unknown"
            text_txt = text.text.strip() if text else ""
            time_txt = time.text.strip() if time else ""
            inbox.append(f"🕒 {time_txt}\n📩 {sender_txt}: {text_txt}")
        return inbox
    except Exception as e:
        print(f"[get_inbox] {server}: {e}")
        return ["Error fetching inbox"]

# =====================
# TELEGRAM HANDLERS
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 Server 1", callback_data="server_server_1")],
        [InlineKeyboardButton("🔵 Server 2", callback_data="server_server_2")],
        [InlineKeyboardButton("🟣 Server 3", callback_data="server_server_3")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔐 Select a server to get temporary numbers:", reply_markup=markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("server_"):
        server = data.split("_")[1]
        numbers = get_numbers(server)

        if not numbers:
            await query.edit_message_text("❌ Failed to load numbers.")
            return

        buttons = [
            [InlineKeyboardButton(num[0], callback_data=f"num_{server}_{num[1]}")]
            for num in numbers
        ]
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
        markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_text(f"📱 Choose a number (from {server.replace('server_', 'Server ')}):", reply_markup=markup)

    elif data.startswith("num_"):
        _, server, number_url = data.split("_", 2)
        inbox = get_inbox(server, number_url)
        text = "\n\n".join(inbox)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"server_{server}")]])
        await query.edit_message_text(f"📥 Messages:\n\n{text}", reply_markup=markup)

    elif data == "back":
        await start(update, context)

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Bot running...")
    app.run_polling()
