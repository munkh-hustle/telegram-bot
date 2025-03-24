from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q"

# Dictionary with video file_ids
VIDEOS = {
    "video1": "BAACAgUAAxkBAANbZ-G7Jn5y85BrBhyK-nfBOLTFjrIAArsXAAJPfhFX3fpc9xwmtt02BA",
    "video2": "BAACAgUAAxkBAANaZ-G7Gv0e-_say7Enp2R-19p9jL4AAm0aAAJ2HBFX-pw5CVY9I-w2BA",
    "video3": "BAACAgUAAxkBAANLZ-GxahVI_jp-wU5YINkVwjV_ISAAAqEXAAJPfhFXqdmcN96vlk42BA"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with optional deep link parameter."""
    if context.args:
        video_id = context.args[0]
        if video_id in VIDEOS:
            try:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=VIDEOS[video_id],
                    caption=f"Here's your requested video ({video_id})!"
                )
                logger.info(f"Sent video {video_id} to {update.effective_chat.id}")
                return
            except Exception as e:
                logger.error(f"Error sending video: {e}")
                await update.message.reply_text("Failed to send video. Please try again.")
    
    await update.message.reply_text(
        "Hello! Use these commands to get videos:\n"
        "/video1 - Get Video 1\n"
        "/video2 - Get Video 2\n"
        "/video3 - Get Video 3"
    )

async def send_video1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /video1 command."""
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=VIDEOS["video1"],
        caption="Here's Video 1!"
    )

async def send_video2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /video2 command."""
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=VIDEOS["video2"],
        caption="Here's Video 2!"
    )

async def send_video3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /video3 command."""
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=VIDEOS["video3"],
        caption="Here's Video 3!"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("video1", send_video1))
    application.add_handler(CommandHandler("video2", send_video2))
    application.add_handler(CommandHandler("video3", send_video3))
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()