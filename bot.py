from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging
import os
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q"
# VIDEO_DB = "videos.json"  # File to store video IDs

# Load existing videos or create empty DB
def load_videos() -> dict:
    if Path(VIDEO_DB).exists():
        with open(VIDEO_DB, "r") as f:
            return json.load(f)
    return {}

VIDEOS = load_videos()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start with deep linking."""
    if context.args and (video_id := context.args[0]) in VIDEOS:
        await send_video(update, context, video_id)
    else:
        await update.message.reply_text(
            "Welcome! Use /list to see available videos or /addvideo to add new ones."
        )

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str = None) -> None:
    """Send a video by ID."""
    video_id = video_id or update.message.text[1:]  # For command triggers
    if video_id in VIDEOS:
        try:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=VIDEOS[video_id],
                caption=f"Here's {video_id}!"
            )
        except Exception as e:
            logger.error(f"Failed to send {video_id}: {e}")
            await update.message.reply_text("Video not found. Use /addvideo to add it.")

async def add_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save a video from user's reply."""
    if not update.message.reply_to_message or not update.message.reply_to_message.video:
        await update.message.reply_text("Reply to a video with /addvideo <name>")
        return

    video_name = " ".join(context.args) if context.args else f"video{len(VIDEOS)+1}"
    video_id = update.message.reply_to_message.video.file_id

    VIDEOS[video_name] = video_id
    with open(VIDEO_DB, "w") as f:
        json.dump(VIDEOS, f, indent=2)

    await update.message.reply_text(f"✅ Saved as '{video_name}'!")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available videos."""
    if not VIDEOS:
        await update.message.reply_text("No videos stored yet. Use /addvideo to add one.")
    else:
        message = "📁 Available videos:\n" + "\n".join(
            f"• {name}: /{name}" for name in VIDEOS.keys()
        )
        await update.message.reply_text(message)

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addvideo", add_video))
    application.add_handler(CommandHandler("list", list_videos))
    
    # Handle direct video commands (e.g., /video1)
    for name in VIDEOS.keys():
        application.add_handler(CommandHandler(name, send_video))
    
    application.run_polling()

if __name__ == "__main__":
    main()