#!/usr/bin/env python3
"""
Telegram Bot with group membership checking and file sharing based on user preferences
Built for python-telegram-bot v21+
"""

import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

# Define file storage structure
BASE_FILES_DIR = "files"
FILE_TYPES_DIRS = {
    'document': os.path.join(BASE_FILES_DIR, 'documents'),
    'image': os.path.join(BASE_FILES_DIR, 'images'),
    'video': os.path.join(BASE_FILES_DIR, 'videos'),
    'audio': os.path.join(BASE_FILES_DIR, 'audio'),
}

# Create directories if they don't exist
for directory in FILE_TYPES_DIRS.values():
    os.makedirs(directory, exist_ok=True)

# Store user preferences and group information
USER_PREFERENCES_FILE = "user_preferences.json"
SUPPORTED_FILE_TYPES = {
    'document': '📄 Documents (PDF, DOCX, etc.)',
    'image': '🖼️ Images (JPG, PNG, etc.)',
    'video': '🎬 Videos (MP4, MOV, etc.)',
    'audio': '🎵 Audio (MP3, WAV, etc.)',
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


def get_available_files(file_types: list) -> dict:
    """
    Get all available files for the given file types.
    
    Args:
        file_types: List of file type preferences (e.g., ['document', 'image'])
        
    Returns:
        dict: Dictionary with file types as keys and list of files as values
    """
    available_files = {}
    
    for file_type in file_types:
        if file_type in FILE_TYPES_DIRS:
            dir_path = FILE_TYPES_DIRS[file_type]
            try:
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                if files:
                    available_files[file_type] = files
            except Exception as e:
                logger.error(f"Error reading files from {dir_path}: {e}")
    
    return available_files


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
    
    # Create main menu buttons
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Set Preferences", callback_data="mode_preferences"),
            InlineKeyboardButton("📋 My Preferences", callback_data="mode_mypreferences"),
        ],
        [
            InlineKeyboardButton("📁 List Files", callback_data="mode_list"),
            InlineKeyboardButton("📤 Send Files", callback_data="mode_send"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="mode_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # User is a member, show welcome message with buttons
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n"
        f"✅ Welcome! You're a member of our group.\n\n"
        f"Choose an action below:",
        reply_markup=reply_markup
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
🤖 **Available Modes:**

⚙️ **Set Preferences** - Choose your file type preferences (Documents, Images, Videos, Audio)
📋 **My Preferences** - View your current file type preferences
📁 **List Files** - Browse all available files for your preferences
📤 **Send Files** - Download all files matching your preferences
❓ **Help** - Show this help message

**How to Use:**
1. Click "Set Preferences" to select file types
2. Click "List Files" to see what's available
3. Click "Send Files" to download them
4. Use "My Preferences" to see your selections anytime
    """
    
    # Create back button
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)


async def preferences_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user preferences setting with buttons."""
    user_id = str(update.effective_user.id)
    
    # Check group membership
    is_member = await is_user_in_group(context, update.effective_user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_text(
            "❌ You need to be a member of our group to set preferences."
        )
        return
    
    # Create preference buttons
    keyboard = [
        [InlineKeyboardButton(f"📄 Documents", callback_data="pref_document")],
        [InlineKeyboardButton(f"🖼️ Images", callback_data="pref_image")],
        [InlineKeyboardButton(f"🎬 Videos", callback_data="pref_video")],
        [InlineKeyboardButton(f"🎵 Audio", callback_data="pref_audio")],
        [InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    preference_text = "📋 **Select your preferred file types:**\n\n💡 Click multiple buttons to add multiple preferences"
    
    await update.message.reply_text(preference_text, parse_mode='Markdown', reply_markup=reply_markup)


async def set_preference_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set preference from button callback."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    # Extract preference from callback data
    command = query.data.split('_')[1] if '_' in query.data else None
    
    if command not in SUPPORTED_FILE_TYPES:
        await query.answer("❌ Invalid preference type.", show_alert=True)
        return
    
    # Load and update preferences
    preferences = load_user_preferences()
    
    if user_id not in preferences:
        preferences[user_id] = {
            'username': query.from_user.username or 'Unknown',
            'file_types': []
        }
    
    if command not in preferences[user_id]['file_types']:
        preferences[user_id]['file_types'].append(command)
        save_user_preferences(preferences)
        await query.answer(f"✅ Added {SUPPORTED_FILE_TYPES[command].split(' ', 1)[1]} to preferences!")
    else:
        await query.answer(f"ℹ️ {SUPPORTED_FILE_TYPES[command].split(' ', 1)[1]} already selected!", show_alert=False)


async def view_preferences_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        pref_text = "📋 **Your Preferences:**\n\n❌ No preferences set yet."
    else:
        file_types = preferences[user_id]['file_types']
        pref_text = "📋 **Your Current Preferences:**\n\n"
        for ftype in file_types:
            pref_text += f"✅ {SUPPORTED_FILE_TYPES.get(ftype, ftype)}\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(pref_text, parse_mode='Markdown', reply_markup=reply_markup)


async def list_files_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available files matching user's preferences."""
    user_id = str(update.effective_user.id)
    
    # Check group membership
    is_member = await is_user_in_group(context, update.effective_user.id, GROUP_ID)
    
    if not is_member:
        await update.message.reply_text(
            "❌ You need to be a member of our group to access files."
        )
        return
    
    preferences = load_user_preferences()
    
    if user_id not in preferences or not preferences[user_id]['file_types']:
        keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ You haven't set any file type preferences yet.\n"
            "Use the preferences mode to set them first.",
            reply_markup=reply_markup
        )
        return
    
    file_types = preferences[user_id]['file_types']
    available_files = get_available_files(file_types)
    
    if not available_files:
        keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📭 No files available for your preferences at the moment.\n"
            "Please check back later or contact the administrator.",
            reply_markup=reply_markup
        )
        return
    
    # Build file list message
    message = "📁 **Available Files for Your Preferences:**\n\n"
    
    for file_type, files in available_files.items():
        message += f"{SUPPORTED_FILE_TYPES.get(file_type, file_type)}:\n"
        for i, filename in enumerate(files, 1):
            message += f"  {i}. `{filename}`\n"
        message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("📤 Send All Files", callback_data="mode_send")],
        [InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)


async def send_files_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ You haven't set any file type preferences yet.\n"
            "Use the preferences mode to set them first.",
            reply_markup=reply_markup
        )
        return
    
    file_types = preferences[user_id]['file_types']
    available_files = get_available_files(file_types)
    
    if not available_files:
        keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📭 No files available for your preferences at the moment.",
            reply_markup=reply_markup
        )
        return
    
    # Send files to user
    await update.message.reply_text(
        "📤 Preparing to send files...\n"
        "This may take a moment depending on the file sizes."
    )
    
    files_sent = 0
    errors = 0
    
    for file_type, files in available_files.items():
        file_dir = FILE_TYPES_DIRS[file_type]
        
        for filename in files:
            file_path = os.path.join(file_dir, filename)
            
            try:
                # Determine file type and send accordingly
                if file_type == 'document':
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=open(file_path, 'rb'),
                        caption=f"📄 {filename}"
                    )
                elif file_type == 'image':
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=open(file_path, 'rb'),
                        caption=f"🖼️ {filename}"
                    )
                elif file_type == 'video':
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=open(file_path, 'rb'),
                        caption=f"🎬 {filename}"
                    )
                elif file_type == 'audio':
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=open(file_path, 'rb'),
                        title=filename
                    )
                
                files_sent += 1
                logger.info(f"Sent file: {filename} to user {user_id}")
                
            except Exception as e:
                logger.error(f"Error sending file {filename}: {e}")
                errors += 1
    
    # Send summary
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="mode_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    summary = f"✅ Sent {files_sent} file(s)"
    if errors > 0:
        summary += f"\n⚠️ Failed to send {errors} file(s)"
    
    await update.message.reply_text(summary, reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()  # Remove the loading state
    
    # Route to appropriate handler based on callback data
    if query.data == "mode_start":
        # Get the user
        user = query.from_user
        
        # Check if user is in the group
        if GROUP_ID == 0:
            await query.edit_message_text(
                f"⚠️ GROUP_ID is not configured. Please set GROUP_ID in your .env file."
            )
            return
        
        is_member = await is_user_in_group(context, user.id, GROUP_ID)
        
        if not is_member:
            await query.edit_message_text(
                f"❌ Sorry, you need to be a member of our group to use this bot."
            )
            return
        
        # Create main menu buttons
        keyboard = [
            [
                InlineKeyboardButton("⚙️ Set Preferences", callback_data="mode_preferences"),
                InlineKeyboardButton("📋 My Preferences", callback_data="mode_mypreferences"),
            ],
            [
                InlineKeyboardButton("📁 List Files", callback_data="mode_list"),
                InlineKeyboardButton("📤 Send Files", callback_data="mode_send"),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="mode_help"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Hi {user.mention_html()}! 👋\n"
            f"✅ Main Menu\n\n"
            f"Choose an action below:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    elif query.data == "mode_preferences":
        await preferences_mode(update, context)
    
    elif query.data == "mode_mypreferences":
        await view_preferences_mode(update, context)
    
    elif query.data == "mode_list":
        await list_files_mode(update, context)
    
    elif query.data == "mode_send":
        await send_files_mode(update, context)
    
    elif query.data == "mode_help":
        await help_command(update, context)
    
    elif query.data.startswith("pref_"):
        await set_preference_button(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


async def post_init(application: Application) -> None:
    """Post init function to set up the bot."""
    logger.info("Bot initialized successfully")


async def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback query handler for button presses
    application.add_handler(CallbackQueryHandler(button_callback))

    # Log all errors
    application.add_error_handler(error_handler)
    
    # Post init
    application.post_init = post_init

    # Run the bot
    print("🤖 Bot is starting...")
    print(f"GROUP_ID configured: {GROUP_ID if GROUP_ID != 0 else 'NOT SET'}")
    print(f"Files directory structure created at: {BASE_FILES_DIR}")
    print("Press Ctrl+C to stop the bot")
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
