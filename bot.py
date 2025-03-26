import os
import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    filters
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin ID - replace with your actual admin ID
ADMIN_ID = 7905267896

# User activity log file
USER_ACTIVITY_FILE = 'user_activity.json'

# Directory to store videos
VIDEO_DIR = 'videos'
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

# Dictionary to store video IDs and names
video_db = {}
def load_video_db():
    """Load video database from JSON file"""
    global video_db
    try:
        with open('video_db.json', 'r') as f:
            video_db = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        video_db = {}

def save_video_db():
    """Save video database to JSON file"""
    with open('video_db.json', 'w') as f:
        json.dump(video_db, f, indent=2)

load_video_db()

def load_user_activity():
    """Load user activity data from file"""
    try:
        with open(USER_ACTIVITY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
def save_user_activity(activity_data):
    """Save user activity data to file"""
    with open(USER_ACTIVITY_FILE, 'w') as f:
        json.dump(activity_data, f, indent=2)

def record_user_activity(user_id, username, video_name):
    """Record that a video was sent to a user"""
    activity_data = load_user_activity()
    
    user_id_str = str(user_id)
    timestamp = datetime.now().isoformat()
    
    if user_id_str not in activity_data:
        activity_data[user_id_str] = {
            'username': username,
            'videos': []
        }
    
    activity_data[user_id_str]['videos'].append({
        'video_name': video_name,
        'timestamp': timestamp
    })
    
    save_user_activity(activity_data)

async def start(update: Update, context: CallbackContext) -> None:
    """Handle /start command with video requests"""
    user = update.effective_user
    
    # Check if this is a video request
    if context.args and context.args[0].startswith('video_'):
        video_name = context.args[0][6:]  # Remove 'video_' prefix
        if video_name in video_db:
            await update.message.reply_text("Sending your video...")
            record_user_activity(user.id, user.username, video_name)
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_db[video_name],
                caption=f"Here's your requested video: {video_name}"
            )
            return
    if video_name:  # Only show this if we were actually looking for a video
        await update.message.reply_text(f"Video '{video_name}' not found. Available videos: /list")
    else:
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
        save_video_db()  # Save to JSON file
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
        save_video_db()  # Save to JSON file
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
    
    try:
        if query.data.startswith('video_'):
            video_name = query.data[6:]
            if video_name in video_db:
                user = query.from_user
                record_user_activity(user.id, user.username, video_name)

                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_db[video_name],
                    caption=video_name
                )
            else:
                await query.edit_message_text(text=f"Video '{video_name}' not found.")
    except Exception as e:
        logger.error(f"Error handling button press: {e}")
        await query.edit_message_text(
            text="Sorry, an error occurred while processing your request."
        )

async def handle_video(update: Update, context: CallbackContext) -> None:
    """Handle video messages"""
    if is_admin(update):
        await update.message.reply_text("To add this video, reply to it with /addvideo <name>")
async def user_stats(update: Update, context: CallbackContext) -> None:
    """Show user activity statistics (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    activity_data = load_user_activity()
    
    if not activity_data:
        await update.message.reply_text("No user activity recorded yet.")
        return
    
    message = ["📊 User Activity Report:"]
    total_sends = 0
    
    for user_id, data in activity_data.items():
        username = data.get('username', 'unknown')
        video_count = len(data['videos'])
        total_sends += video_count
        last_video = data['videos'][-1]['video_name'] if data['videos'] else 'none'
        
        message.append(
            f"\n👤 User: {username} (ID: {user_id})\n"
            f"📹 Videos sent: {video_count}\n"
            f"🎬 Last video: {last_video}"
        )
    
    message.append(f"\n\n📈 Total videos sent: {total_sends}")
    
    await update.message.reply_text('\n'.join(message))

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors and send a message to the user"""
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your request."
        )

def main() -> None:
    """Start the bot."""
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7641317425:AAHfWDG6uHQZeG8BQ5JvuvjMFvLFgrqbh9Q").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addvideo", addvideo))
    application.add_handler(CommandHandler("rename", rename))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("list", list_videos))
    application.add_handler(CommandHandler("stats", user_stats))
    
    # Handle button presses
    application.add_handler(CallbackQueryHandler(button))
    
    # on non command i.e video messages
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()