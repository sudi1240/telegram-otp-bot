import os
import requests
from bs4 import BeautifulSoup
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

BOT_TOKEN = os.getenv("7895337093:AAEF7DWDIcRw1cIP-E2HFpPqotsaNE64JEo")  # Set this in your env vars

##############################
# SCRAPING FUNCTIONS
##############################

# Server 1: receive-smss.com

def get_server_1_numbers():
    try:
        url = "https://receive-smss.com/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        numbers = soup.select(".number-boxes-item > a")
        return [n.text.strip() for n in numbers[:5]]
    except Exception as e:
        print("Error in get_server_1_numbers:", e)
        return ["Error fetching numbers"]

def get_server_1_inbox(number):
    try:
        # The URL for inbox is number slug appended to base url like:
        # https://receive-smss.com/phone-number/{number}/
        slug = number.replace("+", "").replace(" ", "")
        url = f"https://receive-smss.com/phone-number/{slug}/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        msgs = soup.select(".sms-item")
        if not msgs:
            return ["No messages found"]

        inbox = []
        for msg in msgs[:10]:
            sender = msg.select_one(".sms-sender")
            text = msg.select_one(".sms-text")
            time = msg.select_one(".sms-date")
            sender_txt = sender.text.strip() if sender else "Unknown"
            text_txt = text.text.strip() if text else ""
            time_txt = time.text.strip() if time else ""
            inbox.append(f"🕒 {time_txt}\n📩 {sender_txt}: {text_txt}")
        return inbox
    except Exception as e:
        print("Error in get_server_1_inbox:", e)
        return ["Error fetching inbox"]

# Server 2: sms-online.co

def get_server_2_numbers():
    try:
        url = "https://sms-online.co/receive-free-sms"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        numbers = soup.select(".number-boxes-item > a")
        return [n.text.strip() for n in numbers[:5]]
    except Exception as e:
        print("Error in get_server_2_numbers:", e)
        return ["Error fetching numbers"]

def get_server_2_inbox(number):
    try:
        # Format: number slug without + and spaces
        slug = number.replace("+", "").replace(" ", "")
        url = f"https://sms-online.co/receive-free-sms/{slug}/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        msgs = soup.select(".sms-item")
        if not msgs:
            return ["No messages found"]

        inbox = []
        for msg in msgs[:10]:
            sender = msg.select_one(".sms-sender")
            text = msg.select_one(".sms-text")
            time = msg.select_one(".sms-date")
            sender_txt = sender.text.strip() if sender else "Unknown"
            text_txt = text.text.strip() if text else ""
            time_txt = time.text.strip() if time else ""
            inbox.append(f"🕒 {time_txt}\n📩 {sender_txt}: {text_txt}")
        return inbox
    except Exception as e:
        print("Error in get_server_2_inbox:", e)
        return ["Error fetching inbox"]

# Server 3: freephonenum.com

def get_server_3_numbers():
    try:
        url = "https://freephonenum.com/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select("ul.list-unstyled li span.number-box-text")
        return [n.text.strip() for n in items[:5]]
    except Exception as e:
        print("Error in get_server_3_numbers:", e)
        return ["Error fetching numbers"]

def get_server_3_inbox(number):
    try:
        slug = number.replace("+", "").replace(" ", "")
        url = f"https://freephonenum.com/{slug}/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        msgs = soup.select(".sms-item")
        if not msgs:
            return ["No messages found"]

        inbox = []
        for msg in msgs[:10]:
            sender = msg.select_one(".sms-sender")
            text = msg.select_one(".sms-text")
            time = msg.select_one(".sms-date")
            sender_txt = sender.text.strip() if sender else "Unknown"
            text_txt = text.text.strip() if text else ""
            time_txt = time.text.strip() if time else ""
            inbox.append(f"🕒 {time_txt}\n📩 {sender_txt}: {text_txt}")
        return inbox
    except Exception as e:
        print("Error in get_server_3_inbox:", e)
        return ["Error fetching inbox"]


##############################
# TELEGRAM HANDLERS
##############################

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 Server 1", callback_data="server_1")],
        [InlineKeyboardButton("🔵 Server 2", callback_data="server_2")],
        [InlineKeyboardButton("🟣 Server 3", callback_data="server_3")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Welcome!\nChoose a server to get temporary numbers:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # When user clicks server button — show numbers inline
    if data in ("server_1", "server_2", "server_3"):
        if data == "server_1":
            numbers = get_server_1_numbers()
        elif data == "server_2":
            numbers = get_server_2_numbers()
        else:
            numbers = get_server_3_numbers()

        keyboard = []
        for num in numbers:
            keyboard.append([InlineKeyboardButton(num, callback_data=f"num_{data}_{num}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Servers", callback_data="back_servers")])

        await query.edit_message_text(
            f"📲 Choose a number from {data.replace('_',' ').title()}:\n(Click to get OTP inbox)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Back to server selection
    if data == "back_servers":
        keyboard = [
            [InlineKeyboardButton("🟢 Server 1", callback_data="server_1")],
            [InlineKeyboardButton("🔵 Server 2", callback_data="server_2")],
            [InlineKeyboardButton("🟣 Server 3", callback_data="server_3")],
        ]
        await query.edit_message_text("👋 Choose a server:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # When user clicks a number button — show OTP inbox
    if data.startswith("num_"):
        # Format: num_server_1_+1234567890
        try:
            _, server, *num_parts = data.split("_")
            number = "_".join(num_parts)
        except Exception:
            await query.edit_message_text("❌ Invalid data format")
            return

        if server == "server_1":
            inbox = get_server_1_inbox(number)
        elif server == "server_2":
            inbox = get_server_2_inbox(number)
        else:
            inbox = get_server_3_inbox(number)

        text = f"📥 Inbox for {number}:\n\n"
        text += "\n\n".join(inbox)

        keyboard = [[InlineKeyboardButton("⬅️ Back to Numbers", callback_data=server)]]

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Unknown callback data
    await query.answer("❌ Unknown command", show_alert=True)

##############################
# MAIN
##############################

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Bot started!")
    app.run_polling()
