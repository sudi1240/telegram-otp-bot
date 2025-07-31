import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "7642739791:AAFcdWANMba8ksRGhqaNanrGJhNKKrf2h5U"

# Function to download video using yt-dlp
def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',                # Save as video.mp4 or video.webm
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

# Handle incoming messages
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("http"):
        await update.message.reply_text("Downloading video... Please wait ⏳")
        try:
            file_path = download_video(text)
            await update.message.reply_video(video=open(file_path, 'rb'))
            os.remove(file_path)  # delete local file after sending
        except Exception as e:
            await update.message.reply_text(f"Download failed ❌\n{e}")
    else:
        await update.message.reply_text("Please send a valid video link (must start with http).")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

print("Bot is running...")
app.run_polling()
