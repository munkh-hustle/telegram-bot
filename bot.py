import os
import logging
from flask import Flask, jsonify
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    filters
)

app = Flask(__name__)

@app.route('/api/videos')
def get_videos():
    return jsonify(list(video_db.keys()))

def run_flask():
    app.run(port=5000)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin ID - replace with your actual admin ID
ADMIN_ID = 7905267896

# Directory to store videos
VIDEO_DIR = 'videos'
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

# Dictionary to store video IDs and names
video_db = {}

def load_video_db():
    """Load video database from file"""
    global video_db
    try:
        with open('video_db.txt', 'r') as f:
            for line in f:
                name, file_id = line.strip().split(',')
                video_db[name] = file_id
    except FileNotFoundError:
        video_db = {}

def save_video_db():
    """Save video database to file"""
    with open('video_db.txt', 'w') as f:
        for name, file_id in video_db.items():
            f.write(f"{name},{file_id}\n")

async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    # Check if this is a video request
    if context.args and context.args[0].startswith('video_'):
        video_name = context.args[0][6:]
        if video_name in video_db:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_db[video_name],
                caption=f"Here's your requested video: {video_name}"
            )
            return
    
    await update.message.reply_text(f'Hi {user.first_name}! Use /list to see available videos.')

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')

def is_admin(update: Update):
    """Check if user is admin"""
    return update.effective_user.id == ADMIN_ID

async def addvideo(update: Update, context: CallbackContext) -> None:
    """Add video to database (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /addvideo <name> (reply to a video)")
        return
    
    if update.message.reply_to_message and update.message.reply_to_message.video:
        video_name = ' '.join(context.args)
        video_file_id = update.message.reply_to_message.video.file_id
        
        video_db[video_name] = video_file_id
        save_video_db()
        
        await update.message.reply_text(f"Video '{video_name}' added successfully!")
    else:
        await update.message.reply_text("Please reply to a video message with this command.")

async def rename(update: Update, context: CallbackContext) -> None:
    """Rename video in database (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /rename <old_name> <new_name>")
        return
    
    old_name = ' '.join(context.args[:-1])
    new_name = context.args[-1]
    
    if old_name in video_db:
        video_db[new_name] = video_db.pop(old_name)
        save_video_db()
        await update.message.reply_text(f"Video renamed from '{old_name}' to '{new_name}'")
    else:
        await update.message.reply_text(f"Video '{old_name}' not found.")

async def delete(update: Update, context: CallbackContext) -> None:
    """Delete video from database (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /delete <name>")
        return
    
    video_name = ' '.join(context.args)
    
    if video_name in video_db:
        del video_db[video_name]
        save_video_db()
        await update.message.reply_text(f"Video '{video_name}' deleted successfully!")
    else:
        await update.message.reply_text(f"Video '{video_name}' not found.")

async def list_videos(update: Update, context: CallbackContext) -> None:
    """List all available videos"""
    if not video_db:
        await update.message.reply_text("No videos available.")
        return
    
    keyboard = []
    for name in sorted(video_db.keys()):
        keyboard.append([InlineKeyboardButton(name, callback_data=f"video_{name}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Available videos:', reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('video_'):
        video_name = query.data[6:]
        if video_name in video_db:
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=video_db[video_name],
                caption=video_name
            )
        else:
            await query.edit_message_text(text=f"Video '{video_name}' not found.")

async def handle_video(update: Update, context: CallbackContext) -> None:
    """Handle video messages"""
    if is_admin(update):
        await update.message.reply_text("To add this video, reply to it with /addvideo <name>")

def main() -> None:
    """Start the bot."""
    # Load video database
    load_video_db()

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addvideo", addvideo))
    application.add_handler(CommandHandler("rename", rename))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("list", list_videos))
    
    # Handle button presses
    application.add_handler(CallbackQueryHandler(button))
    
    # on non command i.e video messages
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()