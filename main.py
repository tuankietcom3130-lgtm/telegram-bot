#!/usr/bin/env python3
"""
Telegram Bot with group membership checking and file sharing based on user preferences
"""

import logging
import os
import json
from dotenv import load_dotenv
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID', 0))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set. Please set it in .env file or environment.")

# Store user preferences and group information
USER_PREFERENCES_FILE = "user_preferences.json"
SUPPORTED_FILE_TYPES = {
    'document': 'Documents (PDF, DOCX, etc.)',
    'image': 'Images (JPG, PNG, etc.)',
    'video': 'Videos (MP4, MOV, etc.)',
    'audio': 'Audio (MP3, WAV, etc.)',
}


def load_user_preferences():
    """Load user preferences from file."""
    if os.path.exists(USER_PREFERENCES_FILE):
        try:
            with open(USER_PREFERENCES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
    return {}


def save_user_preferences(preferences):
    """Save user preferences to file."""
    try:
        with open(USER_PREFERENCES_FILE, 'w') as f:
            json.dump(preferences, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving preferences: {e}")


async def is_user_in_group(context: ContextTypes.DEFAULT_TYPE, user_id: int, group_id: int) -> bool:
    """
    Check if a user is a member of the specified group.
    
    Args:
        context: Telegram context
        user_id: The user's ID to check
        group_id: The group ID to check in
        
    Returns:
        bool: True if user is in group, False otherwise
    """
    try:
        member = await context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
        # Check if user is active member (not kicked or left)
        if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.CREATOR]:
            return True
        return False
    except TelegramError as e:
        logger.error(f"Error checking group membership: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_id = str(user.id)
    
    # Check if user is in the group
    if GROUP_ID == 0:
        await update.message.reply_html(
            f"Hi {user.mention_html()}! 👋\n"
            f"⚠️ GROUP_ID is not configured. Please set GROUP_ID in your .env file."
        )
        return
    
    is_member = await is_user_in_group(context, user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_html(
            f"Hi {user.mention_html()}! 👋\n"
            f"❌ Sorry, you need to be a member of our group to use this bot.\n"
            f"Please join the group first, then use this bot."
        )
        return
    
    # User is a member, show welcome message
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n"
        f"✅ Welcome! You're a member of our group.\n"
        f"Use /preferences to set your file type preferences.\n"
        f"Use /help to see available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = str(update.effective_user.id)
    
    # Check group membership
    is_member = await is_user_in_group(context, update.effective_user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_text(
            "❌ You need to be a member of our group to access this bot."
        )
        return
    
    help_text = """
🤖 **Available Commands:**

/start - Start the bot
/help - Show this help message
/preferences - Set your file type preferences
/mypreferences - View your current preferences
/send_files - Send files based on your preferences

**File Type Preferences:**
• document - Documents (PDF, DOCX, etc.)
• image - Images (JPG, PNG, etc.)
• video - Videos (MP4, MOV, etc.)
• audio - Audio (MP3, WAV, etc.)
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user preferences setting."""
    user_id = str(update.effective_user.id)
    
    # Check group membership
    is_member = await is_user_in_group(context, update.effective_user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_text(
            "❌ You need to be a member of our group to set preferences."
        )
        return
    
    # Show preference options
    preference_text = "📋 **Select your preferred file types:**\n\n"
    for key, value in SUPPORTED_FILE_TYPES.items():
        preference_text += f"• /pref_{key} - {value}\n"
    
    preference_text += "\n💡 You can select multiple preferences by using multiple commands."
    
    await update.message.reply_text(preference_text, parse_mode='Markdown')


async def set_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a specific file type preference."""
    user_id = str(update.effective_user.id)
    
    # Check group membership
    is_member = await is_user_in_group(context, update.effective_user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_text(
            "❌ You need to be a member of our group to set preferences."
        )
        return
    
    # Extract preference from command
    command = update.message.text.split('_')[1] if '_' in update.message.text else None
    
    if command not in SUPPORTED_FILE_TYPES:
        await update.message.reply_text("❌ Invalid preference type.")
        return
    
    # Load and update preferences
    preferences = load_user_preferences()
    
    if user_id not in preferences:
        preferences[user_id] = {
            'username': update.effective_user.username or 'Unknown',
            'file_types': []
        }
    
    if command not in preferences[user_id]['file_types']:
        preferences[user_id]['file_types'].append(command)
        save_user_preferences(preferences)
        
        await update.message.reply_text(
            f"✅ Added {SUPPORTED_FILE_TYPES[command]} to your preferences!"
        )
    else:
        await update.message.reply_text(
            f"ℹ️ {SUPPORTED_FILE_TYPES[command]} is already in your preferences."
        )


async def view_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View user's current preferences."""
    user_id = str(update.effective_user.id)
    
    # Check group membership
    is_member = await is_user_in_group(context, update.effective_user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_text(
            "❌ You need to be a member of our group to view preferences."
        )
        return
    
    preferences = load_user_preferences()
    
    if user_id not in preferences or not preferences[user_id]['file_types']:
        await update.message.reply_text(
            "📋 You haven't set any preferences yet.\n"
            "Use /preferences to set your preferred file types."
        )
        return
    
    file_types = preferences[user_id]['file_types']
    pref_text = "📋 **Your Preferences:**\n\n"
    for ftype in file_types:
        pref_text += f"✅ {SUPPORTED_FILE_TYPES.get(ftype, ftype)}\n"
    
    await update.message.reply_text(pref_text, parse_mode='Markdown')


async def send_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send files to user based on their preferences."""
    user_id = str(update.effective_user.id)
    
    # Check group membership
    is_member = await is_user_in_group(context, update.effective_user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_text(
            "❌ You need to be a member of our group to receive files."
        )
        return
    
    preferences = load_user_preferences()
    
    if user_id not in preferences or not preferences[user_id]['file_types']:
        await update.message.reply_text(
            "❌ You haven't set any file type preferences yet.\n"
            "Use /preferences to set your preferences first."
        )
        return
    
    file_types = preferences[user_id]['file_types']
    
    # Here you would implement actual file sending logic
    # For now, we'll just show what would be sent
    message = "📁 **Files matching your preferences:**\n\n"
    for ftype in file_types:
        message += f"📦 {SUPPORTED_FILE_TYPES.get(ftype, ftype)}\n"
    
    message += "\n💡 File sending functionality to be implemented."
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("preferences", preferences))
    application.add_handler(CommandHandler("mypreferences", view_preferences))
    application.add_handler(CommandHandler("send_files", send_files))
    
    # Add preference handlers for each file type
    for file_type in SUPPORTED_FILE_TYPES.keys():
        application.add_handler(
            CommandHandler(f"pref_{file_type}", set_preference)
        )

    # Log all errors
    application.add_error_handler(error_handler)

    # Run the bot
    print("🤖 Bot is starting...")
    print(f"GROUP_ID configured: {GROUP_ID if GROUP_ID != 0 else 'NOT SET'}")
    print("Press Ctrl+C to stop the bot")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
