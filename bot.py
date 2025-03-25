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

TOKEN = "YOUR_BOT_TOKEN"
VIDEO_DB = "videos.json"

def load_videos() -> dict:
    """Load videos from JSON file."""
    if Path(VIDEO_DB).exists():
        with open(VIDEO_DB, "r") as f:
            return json.load(f)
    return {}

def save_videos(videos: dict):
    """Save videos to JSON file."""
    with open(VIDEO_DB, "w") as f:
        json.dump(videos, f, indent=2)

VIDEOS = load_videos()

async def rename_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Rename a video (/rename old_name new_name)"""
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /rename <old_name> <new_name>")
        return
    
    old_name, new_name = context.args[0], context.args[1]
    
    if old_name not in VIDEOS:
        await update.message.reply_text(f"❌ Video '{old_name}' not found!")
        return
    
    if new_name in VIDEOS:
        await update.message.reply_text(f"❌ Video '{new_name}' already exists!")
        return
    
    # Rename the video
    VIDEOS[new_name] = VIDEOS.pop(old_name)
    save_videos(VIDEOS)
    
    # Update command handlers
    for handler in application.handlers[0]:
        if isinstance(handler, CommandHandler) and old_name in handler.commands:
            application.remove_handler(handler)
    
    application.add_handler(CommandHandler(new_name, send_video))
    application.add_handler(CommandHandler(f"delete_{new_name}", delete_video))
    
    await update.message.reply_text(f"✅ Video renamed from '{old_name}' to '{new_name}'!")

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a video when its command is used."""
    video_name = update.message.text[1:]  # Remove '/'
    if video_name in VIDEOS:
        await update.message.reply_video(VIDEOS[video_name])
    else:
        await update.message.reply_text("Video not found!")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all videos with their commands."""
    if not VIDEOS:
        await update.message.reply_text("No videos available.")
    else:
        message = "📁 Available videos:\n" + "\n".join(
            f"• {name} - /{name}\n  (Rename: /rename {name} new_name)" 
            for name in VIDEOS.keys()
        )
        await update.message.reply_text(message)
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

def main() -> None:
    global application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rename", rename_video))
    application.add_handler(CommandHandler("list", list_videos))
    
    # Add dynamic video commands
    for name in VIDEOS.keys():
        application.add_handler(CommandHandler(name, send_video))
    
    application.run_polling()

if __name__ == "__main__":
    main()