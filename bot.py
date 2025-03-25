from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Configure logging test
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q"

VIDEOS = {
    "video1": "BAACAgUAAxkBAANbZ-G7Jn5y85BrBhyK-nfBOLTFjrIAArsXAAJPfhFX3fpc9xwmtt02BA",
    "video2": "BAACAgUAAxkBAAMNZ-BVwwuQGbrw7tAlSwZxNTF0XNkAAtoTAAIbd_FWoxDx_THJMrA2BA",
    "video3": "BAACAgUAAxkBAANLZ-GxahVI_jp-wU5YINkVwjV_ISAAAqEXAAJPfhFXqdmcN96vlk42BA"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with deep linking."""
    logger.info(f"New start command from {update.effective_chat.id}")
    
    if context.args:
        video_id = context.args[0]
        if video_id in VIDEOS:
            try:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=VIDEOS[video_id],
                    caption=f"Here's your {video_id}!"
                )
                logger.info(f"Successfully sent {video_id}")
                return
            except Exception as e:
                logger.error(f"Failed to send video: {e}")
                await update.message.reply_text("Failed to send video. Please try /start again.")
    
    await update.message.reply_text(
        "Welcome! Click links on our website to get videos, or use:\n"
        "/video1 /video2 /video3"
    )

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video commands."""
    command = update.message.text[1:]  # Remove '/'
    if command in VIDEOS:
        try:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=VIDEOS[command],
                caption=f"Here's your {command}!"
            )
            logger.info(f"Sent {command} via command")
        except Exception as e:
            logger.error(f"Command error: {e}")
            await update.message.reply_text(f"Failed to send {command}. Please try again.")

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("video1", send_video))
    application.add_handler(CommandHandler("video2", send_video))
    application.add_handler(CommandHandler("video3", send_video))
    
    logger.info("Bot is fully operational")
    application.run_polling()

if __name__ == "__main__":
    main()