import os
import json
import logging
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = "7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q"
VIDEO_DB = "videos.json"
ADMIN_IDS = [7905267896]

class VideoManager:
    def __init__(self):
        self.videos = self.load_videos()
    
    def load_videos(self) -> dict:
        try:
            if Path(VIDEO_DB).exists():
                with open(VIDEO_DB, "r") as f:
                    data = json.load(f)
                    # Convert old format to new format if needed
                    return {
                        name: {
                            "file_id": vid.get("file_id", ""),
                            "title": vid.get("title", name),
                            "description": vid.get("description", ""),
                            "views": vid.get("views", 0),
                            "thumbnail": vid.get("thumbnail", ""),
                            "added_at": vid.get("added_at", datetime.now().isoformat())
                        }
                        for name, vid in data.items()
                    }
        except Exception as e:
            logger.error(f"Error loading videos: {e}")
        return {}
    
    def save_videos(self):
        try:
            with open(VIDEO_DB, "w") as f:
                json.dump(self.videos, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving videos: {e}")
    
    def video_exists(self, name: str) -> bool:
        return name in self.videos
    
    def add_video(self, name: str, file_id: str):
        self.videos[name] = {
            "file_id": file_id,
            "title": name,
            "description": "",
            "views": 0,
            "thumbnail": "",
            "added_at": datetime.now().isoformat()
        }
        self.save_videos()
    
    def remove_video(self, name: str) -> bool:
        if name in self.videos:
            del self.videos[name]
            self.save_videos()
            return True
        return False
    
    def get_video(self, name: str) -> dict:
        return self.videos.get(name)

video_manager = VideoManager()

async def is_admin(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        video_name = context.args[0]
        if video_manager.video_exists(video_name):
            await send_video(update, context, video_name)
            return
    
    await update.message.reply_text(
        "Welcome to Video Bot!\n"
        "Use /list to see available videos\n"
        "Admins: /addvideo, /delete, /cleanup"
    )

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, video_name: str):
    video = video_manager.get_video(video_name)
    if not video or not video.get("file_id"):
        await update.message.reply_text("Video not found!")
        return
    
    try:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video["file_id"],
            caption=f"Here's {video_name}!"
        )
        video["views"] = video.get("views", 0) + 1
        video_manager.save_videos()
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        await update.message.reply_text("Failed to send video.")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not video_manager.videos:
        await update.message.reply_text("No videos available.")
        return
    
    message = "📁 Available Videos:\n" + "\n".join(
        f"• {name} (Views: {data.get('views', 0)}) - /{name}"
        for name, data in video_manager.videos.items()
    )
    await update.message.reply_text(message)

async def add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("Admin only command.")
        return
    
    if not update.message.reply_to_message or not update.message.reply_to_message.video:
        await update.message.reply_text("Reply to a video with /addvideo <name>")
        return
    
    video_name = " ".join(context.args) if context.args else f"video{len(video_manager.videos)+1}"
    video_id = update.message.reply_to_message.video.file_id
    
    video_manager.add_video(video_name, video_id)
    
    async def video_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await send_video(u, c, video_name)
    
    # Update handlers
    for handler in application.handlers[0]:
        if isinstance(handler, CommandHandler) and handler.commands == {video_name}:
            application.remove_handler(handler)
            break
    
    application.add_handler(CommandHandler(video_name, video_handler))
    await update.message.reply_text(f"✅ Added '{video_name}'!")

async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("Admin only command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /delete <video_name>")
        return
    
    video_name = context.args[0]
    if video_manager.remove_video(video_name):
        for handler in application.handlers[0]:
            if isinstance(handler, CommandHandler) and handler.commands == {video_name}:
                application.remove_handler(handler)
                break
        
        await update.message.reply_text(f"✅ Deleted '{video_name}'!")
    else:
        await update.message.reply_text(f"❌ Video '{video_name}' not found!")

async def cleanup_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("Admin only command.")
        return
    
    deleted = []
    for name in list(video_manager.videos.keys()):
        try:
            await context.bot.get_file(video_manager.videos[name]["file_id"])
        except:
            video_manager.remove_video(name)
            deleted.append(name)
    
    await update.message.reply_text(
        f"🧹 Cleanup complete!\n"
        f"Deleted {len(deleted)} unavailable videos\n"
        f"{', '.join(deleted) if deleted else 'None'}"
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working!")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command not recognized")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=context.error)
    if isinstance(update, Update):
        await update.message.reply_text("An error occurred. Please try again.")

def setup_handlers(application):
    # Core commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test))
    application.add_handler(CommandHandler("list", list_videos))
    
    # Admin commands
    application.add_handler(CommandHandler("addvideo", add_video))
    application.add_handler(CommandHandler("delete", delete_video))
    application.add_handler(CommandHandler("cleanup", cleanup_videos))
    
    # Dynamic video commands
    for name in video_manager.videos:
        application.add_handler(
            CommandHandler(name, lambda u, c, n=name: send_video(u, c, n))
        )
    
    # Fallback
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

def main():
    global application
    application = Application.builder().token(TOKEN).build()
    setup_handlers(application)
    logger.info("Starting bot...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()