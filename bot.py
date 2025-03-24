from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = "7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q"

# Dictionary with video file_ids
VIDEOS = {
    "video1": "BAACAgUAAxkBAANbZ-G7Jn5y85BrBhyK-nfBOLTFjrIAArsXAAJPfhFX3fpc9xwmtt02BA",
    "video2": "BAACAgUAAxkBAANaZ-G7Gv0e-_say7Enp2R-19p9jL4AAm0aAAJ2HBFX-pw5CVY9I-w2BA",
    "video3": "BAACAgUAAxkBAANLZ-GxahVI_jp-wU5YINkVwjV_ISAAAqEXAAJPfhFXqdmcN96vlk42BA"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with optional deep link parameter."""
    # Check if command has arguments (deep link)
    if context.args:
        video_id = context.args[0]  # Get the video ID from deep link
        if video_id in VIDEOS:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=VIDEOS[video_id],
                caption=f"Here's your requested video ({video_id})!"
            )
            return
    
    # Normal start command without video parameter
    await update.message.reply_text(
        "Hello! You can get videos by clicking links on our website.\n\n"
        "Or use these commands:\n"
        "/video1 - Get Video 1\n"
        "/video2 - Get Video 2\n"
        "/video3 - Get Video 3"
    )

async def handle_video_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle direct video commands (/video1, /video2, etc.)"""
    command = update.message.text[1:]  # Remove the leading '/'
    if command in VIDEOS:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=VIDEOS[command],
            caption=f"Here's your {command}!"
        )

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()
    
    # Add ALL handlers
    application.add_handler(CommandHandler("start", start))  # THIS WAS MISSING
    application.add_handler(MessageHandler(filters.COMMAND, handle_video_commands))

    print("Bot is running... Press Ctrl+C to stop")
    application.run_polling()

if __name__ == "__main__":
    main()