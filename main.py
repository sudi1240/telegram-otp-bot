import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "7642739791:AAFcdWANMba8ksRGhqaNanrGJhNKKrf2h5U"

# Function to download video using yt-dlp
def download_video(url):
    # yt-dlp options
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',                # Save file name as video.mp4, video.webm etc.
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
    }

    # If cookies.txt file exists in the container, use it
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'

    # Download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

# Handle incoming messages (links)
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("http"):
        await update.message.reply_text("Downloading video... Please wait ⏳")
        try:
            file_path = download_video(text)

            # Send video
            with open(file_path, 'rb') as video_file:
                await update.message.reply_video(video=video_file)

            os.remove(file_path)  # delete local file after sending

        except Exception as e:
            await update.message.reply_text(
                "Download failed ❌\n"
                "Reason: " + str(e)
            )
    else:
        await update.message.reply_text("Please send a valid video link (must start with http).")

# Build and run the bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

print("Bot is running...")
app.run_polling()
