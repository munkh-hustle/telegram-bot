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
TOKEN = "7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q"  # From environment variables
VIDEO_DB = "videos.json"
ADMIN_IDS = [7905267896]  # Replace with your admin user IDs

class VideoManager:
    def __init__(self):
        self.videos = self.load_videos()
    
    def load_videos(self) -> dict:
        try:
            if Path(VIDEO_DB).exists():
                with open(VIDEO_DB, "r") as f:
                    return json.load(f)
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
            "added_at": datetime.now().isoformat(),
            "views": 0
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
    user_id = update.effective_user.id
    print(f"DEBUG: Checking admin status for user_id={user_id}")
    print(f"DEBUG: ADMIN_IDS={ADMIN_IDS}")
    return user_id in ADMIN_IDS

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
    if not video:
        await update.message.reply_text("Video not found!")
        return
    
    try:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video["file_id"],
            caption=f"Here's {video_name}!"
        )
        video["views"] += 1
        video_manager.save_videos()
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        await update.message.reply_text("Failed to send video.")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not video_manager.videos:
        await update.message.reply_text("No videos available.")
        return
    
    message = "📁 Available Videos:\n" + "\n".join(
        f"• {name} (Views: {data['views']}) - /{name}"
        for name, data in video_manager.videos.items()
    )
    await update.message.reply_text(message)

async def add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: add_video triggered!")  # Temporary debug line
    if not await is_admin(update):
        print("DEBUG: User is not admin!")
        await update.message.reply_text("Admin only command.")
        return
    
    print("DEBUG: User is admin!")

    if not update.message.reply_to_message or not update.message.reply_to_message.video:
        await update.message.reply_text("Reply to a video with /addvideo <name>")
        return
    
    # Get video name from command arguments or generate default
    video_name = " ".join(context.args) if context.args else f"video{len(video_manager.videos)+1}"
    video_id = update.message.reply_to_message.video.file_id
    
    # Add video to manager
    video_manager.add_video(video_name, video_id)
    
    # Create a proper handler with captured video_name
    async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await send_video(update, context, video_name)
    
    # Remove existing handler if any
    for handler in application.handlers[0]:
        if isinstance(handler, CommandHandler) and handler.commands == {video_name}:
            application.remove_handler(handler)
            break
    
    # Add new handler
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
        # Remove command handler
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

async def handle_video_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when someone replies to a video without using /addvideo"""
    if await is_admin(update):
        await update.message.reply_text("Tip: Use /addvideo <name> to save this video")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working!")

def main():
    global application
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("test", test))

    
    application.add_handler(MessageHandler(filters.VIDEO & filters.REPLY, handle_video_reply))

    # Core commands
    application.add_handler(CommandHandler("start", start))
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
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("Starting bot...")
    application.run_polling()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=context.error)
    if isinstance(update, Update):
        await update.message.reply_text("An error occurred. Please try again.")

if __name__ == "__main__":
    main()
