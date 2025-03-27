import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
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
        with open('video_db.json', 'r', encoding='utf-8') as f:
            video_db = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        video_db = {}

def save_video_db():
    """Save video database to JSON file"""
    with open('video_db.json', 'w', encoding='utf-8') as f:
        json.dump(video_db, f, indent=2)

load_video_db()

def load_user_activity():
    """Load user activity data from file"""
    try:
        with open(USER_ACTIVITY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
def save_user_activity(activity_data):
    """Save user activity data to file"""
    with open(USER_ACTIVITY_FILE, 'w', encoding='utf-8') as f:
        json.dump(activity_data, f, indent=2)

def record_user_activity(user_id, username, first_name, last_name, video_name):
    """Record that a video was sent to a user"""
    activity_data = load_user_activity()
    user_id_str = str(user_id)
    
    if user_id_str not in activity_data:
        activity_data[user_id_str] = {
            'username': username,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'videos': []
        }
    
    activity_data[user_id_str]['videos'].append({
        'video_name': video_name,
        'timestamp': datetime.now().isoformat()
    })
    
    save_user_activity(activity_data)

def load_video_data():
    """Load video metadata from JSON file"""
    try:
        with open('video_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading video_data.json: {e}")
        return {}
def sync_video_data():
    """
    Synchronize video_db.json with video_data.json:
    - Adds any missing videos from video_data.json
    - Removes videos that no longer exist in video_data.json
    - Preserves existing file_ids
    """
    try:
        video_data = load_video_data()
        changes_made = False
        
        # Add new videos from video_data.json
        for name, data in video_data.items():
            if name not in video_db and 'file_id' in data:
                video_db[name] = data['file_id']
                logger.info(f"Added new video: {name}")
                changes_made = True
        
        # Remove videos that don't exist in video_data.json
        for name in list(video_db.keys()):
            if name not in video_data:
                del video_db[name]
                logger.info(f"Removed video: {name}")
                changes_made = True
        
        if changes_made:
            save_video_db()
            logger.info("Video database synchronized with video_data.json")
        return changes_made
    except Exception as e:
        logger.error(f"Error syncing video data: {e}")
        return False

def log_user_message(user_id, username, first_name, text, chat_type):
    """Save user messages to a separate log file"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'chat_type': chat_type,
        'text': text  # Actual message content
    }
    
    try:
        with open('message_logs.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.error(f"Failed to log message: {e}")

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Log all user messages"""
    user = update.effective_user
    message = update.effective_message
    
    # Don't log commands or videos (already handled)
    if message.text and not message.text.startswith('/'):
        log_user_message(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            text=message.text,
            chat_type=update.effective_chat.type
        )

async def start(update: Update, context: CallbackContext) -> None:
    """Handle /start command with video requests"""
    user = update.effective_user
    video_name = None  # Initialize variable outside the if block
    
    # Check if this is a video request
    if context.args and context.args[0].startswith('video_'):
        video_name = context.args[0][6:]  # Remove 'video_' prefix
        if video_name in video_db:
            await update.message.reply_text("Sending your video...")
            record_user_activity(
                user.id, 
                user.username, 
                user.first_name, 
                user.last_name,
                video_name
            )

            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_db[video_name],
                protect_content=True,
                caption=f"Here's your requested video: {video_name}"
            )
            return
    if video_name is not None:  # Only show this if we were actually looking for a video
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

        # Update video_data.json if this is a new video
        video_data = load_video_data()
        if video_name not in video_data:
            video_data[video_name] = {
                "title": video_name,
                "description": "No description available",
                "views": 0,
                "file_id": video_file_id
            }
            with open('video_data.json', 'w') as f:
                json.dump(video_data, f, indent=2)

        await update.message.reply_text(f"Video '{video_name}' added successfully!")
    else:
        await update.message.reply_text("Please reply to a video message with this command.")
async def sync(update: Update, context: CallbackContext) -> None:
    """Manually sync video data (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    if sync_video_data():
        await update.message.reply_text("Video database synchronized successfully!")
    else:
        await update.message.reply_text("No changes needed - databases are already in sync.")

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
        # Update video_db
        video_db[new_name] = video_db.pop(old_name)
        save_video_db()  # Save to JSON file

        # Update video_data
        video_data = load_video_data()
        if old_name in video_data:
            video_data[new_name] = video_data.pop(old_name)
            # Ensure title matches new name if it matched old name
            if video_data[new_name]['title'] == old_name:
                video_data[new_name]['title'] = new_name
            with open('video_data.json', 'w') as f:
                json.dump(video_data, f, indent=2)

        # Update user activity logs
        activity_data = load_user_activity()
        for user_data in activity_data.values():
            for video in user_data['videos']:
                if video['video_name'] == old_name:
                    video['video_name'] = new_name
        save_user_activity(activity_data)
        
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

        video_data = load_video_data()
        if video_name in video_data:
            del video_data[video_name]
            with open('video_data.json', 'w') as f:
                json.dump(video_data, f, indent=2)

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
                record_user_activity(
                    user.id, 
                    user.username, 
                    user.first_name, 
                    user.last_name,
                    video_name
                )

                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_db[video_name],
                    protect_content=True,
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
    
    load_dotenv()
    
    # Load and sync video database at startup
    load_video_db()
    sync_video_data()

    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("Telegram bot token not found in environment variables")
        return
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("sync", sync))  # Add this line
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()