import os
import logging
import json
import io
from PIL import Image
from datetime import datetime
from telegram import InputMediaPhoto
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

BLOCKED_USERS_FILE = 'blocked_users.json'
MAX_VIDEOS_BEFORE_BLOCK = 5

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

def load_blocked_users():
    """Load blocked users from JSON file"""
    try:
        with open(BLOCKED_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_blocked_users(blocked_users):
    """Save blocked users to JSON file"""
    with open(BLOCKED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(blocked_users, f, indent=2)

def is_user_blocked(user_id):
    """Check if user is blocked"""
    blocked_users = load_blocked_users()
    user_blocked = str(user_id) in blocked_users
    
    if user_blocked:
        user_data = blocked_users.get(str(user_id), {})
        return not user_data.get('unblocked')
    return False

def block_user(user_id, username, first_name):
    """Block a user from receiving more videos"""
    blocked_users = load_blocked_users()
    blocked_users[str(user_id)] = {
        'username': username,
        'first_name': first_name,
        'blocked_at': datetime.now().isoformat(),
        'unblocked': False
    }
    save_blocked_users(blocked_users)

def unblock_user(user_id):
    """Unblock a user"""
    blocked_users = load_blocked_users()
    if str(user_id) in blocked_users:
        blocked_users[str(user_id)]['unblocked'] = True
        blocked_users[str(user_id)]['unblocked_at'] = datetime.now().isoformat()
        save_blocked_users(blocked_users)
        return True
    return False

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
        'text': text
    }
    
    try:
        os.makedirs('logs', exist_ok=True)
        with open('logs/message_logs.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry))  # No comma here
            f.write('\n')  # Ensure each entry is on a new line
    except Exception as e:
        logger.error(f"Failed to log message: {e}")

def reset_user_video_count(user_id):
    """Reset a user's video count"""
    activity_data = load_user_activity()
    if str(user_id) in activity_data:
        activity_data[str(user_id)]['videos'] = []
        save_user_activity(activity_data)
        return True
    return False

def unblock_user(user_id):
    """Unblock a user and reset their video count"""
    blocked_users = load_blocked_users()
    if str(user_id) in blocked_users:
        blocked_users[str(user_id)]['unblocked'] = True
        blocked_users[str(user_id)]['unblocked_at'] = datetime.now().isoformat()
        save_blocked_users(blocked_users)
        reset_user_video_count(user_id)  # Reset their video count
        return True
    return False

def log_sent_video(user_id, video_name):
    """Log successfully sent videos with timestamp"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'video_name': video_name,
        'status': 'sent'
    }
    
    try:
        os.makedirs('logs', exist_ok=True)
        with open('logs/video_delivery_log.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry))
            f.write('\n')
    except Exception as e:
        logger.error(f"Failed to log video delivery: {e}")

def update_payment_status(user_id, status):
    """Update payment status in the database"""
    try:
        with open('payment_submissions.json', 'r+', encoding='utf-8') as f:
            data = json.load(f)
            
        # Find most recent submission from this user
        for submission in reversed(data):
            if submission['user_id'] == user_id:
                submission['status'] = status
                submission['processed_at'] = datetime.now().isoformat()
                break
                
        with open('payment_submissions.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error updating payment status: {e}")

def save_payment_submission(payment_data):
    """Save payment submission to JSON file"""
    try:
        with open('payment_submissions.json', 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    except FileNotFoundError:
        data = []
    
    data.append(payment_data)
    
    with open('payment_submissions.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
  
async def notify_admin_payment_submission(context: CallbackContext, user, file_path):
    """Notify admin about new payment submission"""
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        with open(file_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo,
                caption=f"🆕 Payment from @{user.username or user.first_name} (ID: {user.id})",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error sending payment notification: {e}")

async def handle_screenshot(update: Update, context: CallbackContext) -> None:
    """Handle payment screenshot submissions"""
    user = update.effective_user

    try:
        # Record the submission
        payment_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }

        save_payment_submission(payment_data)

        # Notify user
        await update.message.reply_text(
            "✅ Payment screenshot received!\n"
            "Admin will verify it shortly.\n\n"
            f"Your User ID: {user.id}"
        )
                
        # Forward to admin with approval buttons
        keyboard = [
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}")],
            [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create caption for admin
        caption = (f"🆕 Payment from @{user.username or user.first_name} (ID: {user.id})\n"
                  f"Status: {'BLOCKED (reached limit)' if is_user_blocked(user.id) else 'Active'}\n"
                  f"User message: {update.message.caption or 'No caption'}")
        
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error handling screenshot: {e}")
        await update.message.reply_text(
            "❌ Error processing your screenshot. Please try again."
        )

async def reset_user(update: Update, context: CallbackContext) -> None:
    """Reset a user's video count (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("Permission denied.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /resetuser <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if reset_user_video_count(user_id):
            await update.message.reply_text(f"User {user_id}'s video count has been reset.")
        else:
            await update.message.reply_text(f"User {user_id} not found or already has no videos.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Must be a number.")

async def send_video_with_limit_check(update: Update, context: CallbackContext, user, video_name):
    """Handle video sending with limit checks"""
    # First check if user is blocked
    if is_user_blocked(user.id):  # This stays the same
        blocked_users = load_blocked_users()
        user_data = blocked_users.get(str(user.id), {})
        if not user_data.get('unblocked'):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You've reached the 5 video limit. Please wait for admin approval."
            )
            return False
    
    # Record the activity first
    record_user_activity(
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        video_name
    )
    
    # Check if user reached limit
    activity_data = load_user_activity()
    user_videos = activity_data.get(str(user.id), {}).get('videos', [])
    unique_videos = len({v['video_name'] for v in user_videos})
    
    if unique_videos >= MAX_VIDEOS_BEFORE_BLOCK:
        # Send the 5th video first (with protect_content)
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video_db[video_name],
            protect_content=True,
            caption=f"Here's your requested video: {video_name}"
        )
        log_sent_video(user.id, video_name)

        # Then block them and send payment instructions
        block_user(user.id, user.username, user.first_name)
        payment_message = (
            "⚠️ You've reached the 5 video limit.\n\n"
            "To continue accessing videos, please send 10,000 MNT to:\n"
            "🏦 Khan Bank: 5926271236\n\n"
            "Include this in the transaction description:\n"
            f"UserID:{user.id} 10000\n\n"
            "After payment, send a screenshot of the transaction here.\n"
            "Admin will review it and approve your access."
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=payment_message
        )

        await notify_admin_limit_reached(context, user)
        return False
    
    # Send video if under limit (with protected content)
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=video_db[video_name],
        protect_content=True,
        caption=f"Here's your requested video: {video_name}"
    )
    log_sent_video(user.id, video_name)
    return True

async def notify_admin_limit_reached(context: CallbackContext, user):
    """Notify admin when a user reaches the limit"""
    keyboard = [
        [InlineKeyboardButton("✅ Unblock User", callback_data=f"unblock_{user.id}")],
        [InlineKeyboardButton("❌ Keep Blocked", callback_data=f"keep_blocked_{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 User @{user.username or user.first_name} (ID: {user.id}) "
                 f"has reached the 5 video limit.\n\n"
                 f"Please wait for their payment screenshot or manually verify.\n"
                 f"Username: @{user.username}\n"
                 f"First Name: {user.first_name}\n"
                 f"User ID: {user.id}",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

async def unblock_command(update: Update, context: CallbackContext) -> None:
    """Unblock a user by ID (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("Permission denied.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if unblock_user(user_id):
            await update.message.reply_text(f"User {user_id} has been unblocked.")
            # Notify the user
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 You've been unblocked by admin! You can now request videos again."
            )
        else:
            await update.message.reply_text(f"User {user_id} wasn't blocked.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Must be a number.")

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
    video_name = None 
    
    if context.args and context.args[0].startswith('video_'):
        video_name = context.args[0][6:]
        if video_name in video_db:
            await update.message.reply_text("Sending your video...")
            success = await send_video_with_limit_check(update, context, user, video_name)
            if not success:
                return
            
    if video_name is not None:  # Only show this if we were actually looking for a video
        await update.message.reply_text(f"Video '{video_name}' not found. Available videos: /list")
    else:
        await update.message.reply_text(f'Hi {user.first_name}! Use /list to see available videos.')

async def blocked_users(update: Update, context: CallbackContext) -> None:
    """Show list of blocked users (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    blocked_users = load_blocked_users()
    if not blocked_users:
        await update.message.reply_text("No users are currently blocked.")
        return
    
    message = ["🚫 Blocked Users:"]
    keyboard = []

    for user_id, data in blocked_users.items():
        if data.get('unblocked'):
            status = "✅ Unblocked"
        else:
            status = "❌ Blocked"
            # Add unblock button for blocked users
            keyboard.append([
                InlineKeyboardButton(
                    f"Unblock {data.get('first_name', 'User')} (ID: {user_id})",
                    callback_data=f"unblock_{user_id}"
                )
            ])
        
        message.append(
            f"\n👤 {data.get('first_name', 'Unknown')} "
            f"(ID: {user_id}) - @{data.get('username', 'no_username')}\n"
            f"Blocked at: {data.get('blocked_at')}\n"
            f"Status: {status}"
        )

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(
        '\n'.join(message),
        reply_markup=reply_markup
    )

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

async def video_logs(update: Update, context: CallbackContext) -> None:
    """Show video delivery logs (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("Permission denied.")
        return
    
    try:
        if not os.path.exists('logs/video_delivery_log.json'):
            await update.message.reply_text("No video logs available yet.")
            return
        
        with open('logs/video_delivery_log.json', 'r', encoding='utf-8') as f:
            logs = [json.loads(line) for line in f if line.strip()]
            
        if not logs:
            await update.message.reply_text("No video delivery logs found.")
            return
            
        # Count unique videos sent
        video_counts = {}
        for log in logs:
            video_counts[log['video_name']] = video_counts.get(log['video_name'], 0) + 1
            
        message = ["📊 Video Delivery Statistics:"]
        message.append(f"\nTotal videos sent: {len(logs)}")
        message.append("\nUnique videos sent:")
        
        for video, count in sorted(video_counts.items(), key=lambda x: x[1], reverse=True):
            message.append(f"{video}: {count}")
            
        await update.message.reply_text('\n'.join(message))
        
    except Exception as e:
        logger.error(f"Error reading video logs: {e}")
        await update.message.reply_text("Error reading video logs.")

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

    try:
        await query.answer()

        if query.data.startswith('video_'):
            video_name = query.data[6:]
            if video_name in video_db:
                user = query.from_user
                try:
                    success = await send_video_with_limit_check(update, context, user, video_name)

                    if not success:
                        await query.edit_message_text(text="You've reached the video limit.")
                except Exception as e:
                    logger.error(f"Error sending video: {e}")
                    await context.bot.send_message(
                        chat_id=user.id,
                        text="An error occurred while processing your request."
                    )
                

        elif query.data.startswith('unblock_'):
            user_id = int(query.data[8:])
            if is_admin(update):
                # Remove from blocked_users.json completely
                blocked_users = load_blocked_users()
                if str(user_id) in blocked_users:
                    user_data = blocked_users.pop(str(user_id))
                    save_blocked_users(blocked_users)
                    reset_user_video_count(user_id)
                    
                    try:
                        await query.edit_message_text(
                            text=f"✅ User {user_data.get('first_name', 'Unknown')} "
                                 f"(ID: {user_id}) has been unblocked."
                        )
                    except Exception as e:
                        logger.error(f"Error editing message: {e}")
                        await context.bot.send_message(
                            chat_id=ADMIN_ID,
                            text=f"✅ User {user_data.get('first_name', 'Unknown')} "
                                 f"(ID: {user_id}) has been unblocked."
                        )
                    
                    # Notify the unblocked user
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text="🎉 You've been unblocked by admin! Your video count has been reset."
                        )
                    except Exception as e:
                        logger.error(f"Error notifying unblocked user: {e}")
                
        elif query.data.startswith('keep_blocked_'):
            user_id = int(query.data[12:])
            if is_admin(update):
                try:
                    await query.edit_message_text(
                        text=f"User (ID: {user_id}) remains blocked."
                    )
                except Exception as e:
                    logger.error(f"Error editing message: {e}")
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"User (ID: {user_id}) remains blocked."
                    )
        elif query.data.startswith('approve_'):
            user_id = int(query.data[8:])
            if is_admin(update):
                # Update payment status
                update_payment_status(user_id, 'approved')

                # Unblock user
                unblock_user(user_id)
                reset_user_video_count(user_id)

                # Notify user
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 Your payment has been verified! You can now request videos again."
                )

                try:
                    # Try to edit the original message
                    await query.edit_message_text(
                        text=f"✅ Payment from user ID {user_id} approved."
                    )
                except Exception as e:
                    logger.error(f"Error editing approval message: {e}")
                    # Fallback - send a new message if editing fails
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"✅ Payment from user ID {user_id} approved."
                    )

        elif query.data.startswith('reject_'):
            user_id = int(query.data[7:])
            if is_admin(update):
                # Update payment status
                update_payment_status(user_id, 'rejected')

                # Notify user
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Your payment couldn't be verified. Please send a clear screenshot of your transaction."
                )

                try:
                    # Try to edit the original message
                    await query.edit_message_text(
                        text=f"❌ Payment from user ID {user_id} rejected."
                    )
                except Exception as e:
                    logger.error(f"Error editing rejection message: {e}")
                    # Fallback - send a new message if editing fails
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"❌ Payment from user ID {user_id} rejected."
                    )


    except Exception as e:
        logger.error(f"Error handling button press: {e}")
        try:
            if query.message:
                await query.edit_message_text(
                    text="Sorry, an error occurred while processing your request."
                )
        except:
            if update.effective_user:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="Sorry, an error occurred while processing your request."
                )

async def search_user_messages(update: Update, context: CallbackContext, search_term: str) -> None:
    """Search through user messages for specific text"""
    try:
        # Parse user filter syntax: "user:1234" or "user:@username"
        user_filter = None
        actual_search_term = search_term

        # Check for user: prefix
        if 'user:' in search_term.lower():
            parts = search_term.split('user:', 1)
            user_part = parts[1].split()[0]  # Get the user specifier
            actual_search_term = ' '.join(parts[1].split()[1:]) if len(parts[1].split()) > 1 else ''

            # Check if user is ID or username
            if user_part.startswith('@'):
                user_filter = {'username': user_part[1:].lower()}
            else:
                try:
                    user_filter = {'user_id': int(user_part)}
                except ValueError:
                    await update.message.reply_text("Invalid user ID. Use @username or numeric ID")
                    return
            
        if not actual_search_term and not user_filter:
            await update.message.reply_text("Please provide a search term or user filter")
            return

        if not os.path.exists('logs/message_logs.json'):
            await update.message.reply_text("No message logs available yet.")
            return
        
        with open('logs/message_logs.json', 'r', encoding='utf-8') as f:
            # Read all lines as individual JSON objects
            messages = [json.loads(line) for line in f if line.strip()]
        
        # Filter messages containing the search term (case insensitive)
        results = []
        for msg in messages:
            # Apply user filter if specified
            if user_filter:
                if 'user_id' in user_filter and msg.get('user_id') != user_filter['user_id']:
                    continue
                if 'username' in user_filter and msg.get('username', '').lower() != user_filter['username']:
                    continue
            
            # Apply simple text search
            if actual_search_term and actual_search_term.lower() not in msg.get('text', '').lower():
                continue
            
            results.append(msg)
        
        if not results:
            await update.message.reply_text(f"No messages found containing:")
            return
        
        # Format results with pagination
        response = [f"🔍 Search results for:\n"]
        if user_filter:
            response[0] += f"👤 Filtered by user: {user_filter}\n"

        for i, msg in enumerate(results[:15], 1):  # Show first 15 results
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%Y-%m-%d %H:%M')
            response.append(
                f"\n{i}. {timestamp} - @{msg.get('username', '?')} "
                f"({msg.get('first_name', 'Unknown')}):\n"
                f"{msg['text']}"
            )
        
        if len(results) > 15:
            response.append(f"\n\nℹ️ Showing 10 of {len(results)} results.")
        
        # Split long messages to avoid Telegram's message length limit
        full_response = '\n'.join(response)
        for i in range(0, len(full_response), 4000):
            await update.message.reply_text(full_response[i:i+4000])
            
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        await update.message.reply_text("An error occurred while searching messages.")

async def handle_video(update: Update, context: CallbackContext) -> None:
    """Handle video messages"""
    if is_admin(update):
        await update.message.reply_text("To add this video, reply to it with /addvideo <name>")
async def user_stats(update: Update, context: CallbackContext) -> None:
    """Show user activity statistics (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    # Check if this is a search request
    if context.args and context.args[0].startswith('search:'):
        search_term = ' '.join(context.args)[7:]  # Remove 'search:' prefix
        return await search_user_messages(update, context, search_term)

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
    message.append("\n\n🔍 Search user messages with: /stats search:<query>")
    
    await update.message.reply_text('\n'.join(message))

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors and send a message to the user"""
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your request."
        )
async def verify_payment(update: Update, context: CallbackContext) -> None:
    """Verify a payment manually (admin only)"""
    if not is_admin(update):
        await update.message.reply_text("You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /verifypayment <user_id> <approve/reject>")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Please specify both user_id and action (approve/reject)")
        return
    
    try:
        user_id = int(context.args[0])
        action = context.args[1].lower()
        
        if action not in ['approve', 'reject']:
            await update.message.reply_text("Action must be either 'approve' or 'reject'")
            return
            
        # Update payment status
        update_payment_status(user_id, 'approved' if action == 'approve' else 'rejected')
        
        if action == 'approve':
            # Unblock user if approved
            unblock_user(user_id)
            reset_user_video_count(user_id)
            await update.message.reply_text(f"✅ Payment from user {user_id} approved and user unblocked.")
            # Notify the user
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 Your payment has been verified! You can now request videos again."
            )
        else:
            await update.message.reply_text(f"❌ Payment from user {user_id} rejected.")
            # Notify the user
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Your payment was rejected. Please contact support if you believe this is an error."
            )
            
    except ValueError:
        await update.message.reply_text("Invalid user ID. Must be a number.")

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
    application.add_handler(CommandHandler("blocked", blocked_users))
    application.add_handler(CommandHandler("unblock", unblock_command))
    application.add_handler(CommandHandler("resetuser", reset_user))
    application.add_handler(CommandHandler("videologs", video_logs))
    application.add_handler(CommandHandler("verifypayment", verify_payment))

    
    # Handle button presses
    application.add_handler(CallbackQueryHandler(button))
    
    # on non command i.e video messages
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_screenshot))

    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()