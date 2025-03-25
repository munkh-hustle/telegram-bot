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
VIDEO_DB = "videos.json"

def load_videos() -> dict:
    if Path(VIDEO_DB).exists():
        with open(VIDEO_DB, "r") as f:
            return json.load(f)
    return {}

def save_videos(videos: dict):
    with open(VIDEO_DB, "w") as f:
        json.dump(videos, f, indent=2)

VIDEOS = load_videos()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hello! I am your bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help message goes here!')

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a video from the stored videos."""
    command = update.message.text[1:]  # Remove the '/' from the command
    if command in VIDEOS:
        await update.message.reply_video(VIDEOS[command])
    else:
        await update.message.reply_text("Video not found!")

async def add_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new video to the storage."""
    if not update.message.reply_to_message or not update.message.reply_to_message.video:
        await update.message.reply_text("Please reply to a video message with /addvideo <name>")
        return
    
    if not context.args:
        await update.message.reply_text("Please specify a name for the video: /addvideo <name>")
        return
    
    video_name = context.args[0]
    video_id = update.message.reply_to_message.video.file_id
    
    VIDEOS[video_name] = video_id
    save_videos(VIDEOS)
    
    # Add new command handler for this video
    application.add_handler(CommandHandler(video_name, send_video))
    application.add_handler(CommandHandler(f"delete_{video_name}", delete_video))
    
    await update.message.reply_text(f"✅ Video '{video_name}' added successfully!")

async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a video from the list (/delete <video_name>)"""
    if not context.args:
        await update.message.reply_text("Usage: /delete <video_name>")
        return
    
    video_name = context.args[0]
    if video_name in VIDEOS:
        del VIDEOS[video_name]
        save_videos(VIDEOS)
        
        # Remove the command handler for this video
        handlers = application.handlers
        for handler_group in handlers.values():
            for handler in handler_group:
                if isinstance(handler, CommandHandler) and handler.commands == {video_name}:
                    application.remove_handler(handler)
        
        await update.message.reply_text(f"✅ Video '{video_name}' deleted!")
    else:
        await update.message.reply_text(f"❌ Video '{video_name}' not found!")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available videos (/list)"""
    if not VIDEOS:
        await update.message.reply_text("No videos available.")
    else:
        message = "📁 Available videos:\n" + "\n".join(
            f"• {name} - {name}" for name in VIDEOS.keys()
        )
        await update.message.reply_text(message)

def main() -> None:
    global application
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addvideo", add_video))
    application.add_handler(CommandHandler("delete", delete_video))
    application.add_handler(CommandHandler("list", list_videos))
    
    # Dynamic command handlers for each video
    for name in VIDEOS.keys():
        application.add_handler(CommandHandler(name, send_video))
        application.add_handler(CommandHandler(f"delete_{name}", delete_video))
    
    application.run_polling()

if __name__ == "__main__":
    main()