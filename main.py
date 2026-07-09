#!/usr/bin/env python3
import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get config from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
GROUP_ID = int(os.getenv('GROUP_ID', 0))
CHANNEL_URL = os.getenv('CHANNEL_URL', 'https://t.me/')
GROUP_URL = os.getenv('GROUP_URL', 'https://t.me/')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set.")

# --- FILE STRUCTURE & PREFS (Giữ nguyên như cũ) ---
BASE_FILES_DIR = "files"
FILE_TYPES_DIRS = {
    'document': os.path.join(BASE_FILES_DIR, 'documents'),
    'image': os.path.join(BASE_FILES_DIR, 'images'),
    'video': os.path.join(BASE_FILES_DIR, 'videos'),
    'audio': os.path.join(BASE_FILES_DIR, 'audio'),
}
for directory in FILE_TYPES_DIRS.values():
    os.makedirs(directory, exist_ok=True)

USER_PREFERENCES_FILE = "user_preferences.json"
SUPPORTED_FILE_TYPES = {
    'document': '📄 Documents',
    'image': '🖼️ Images',
    'video': '🎬 Videos',
    'audio': '🎵 Audio',
}

# --- MULTILANGUAGE DICTIONARY ---
LANG = {
    'en': {
        'not_configured': "⚠️ Bot is not fully configured (missing IDs). Please contact admin.",
        'join_req': "❌ **Access Denied**\n\nYou must join both our Channel and Group to use this bot.\nPlease join via the links below, then click **Verify**.",
        'btn_channel': "📢 Join Channel",
        'btn_group': "💬 Join Group",
        'btn_verify': "🔄 Verify Membership",
        'verify_fail': "⚠️ You haven't joined both yet. Please check again!",
        'main_menu': "✅ **Main Menu**\n\nChoose an action below:",
        'btn_pref': "⚙️ Set Preferences",
        'btn_mypref': "📋 My Preferences",
        'btn_list': "📁 List Files",
        'btn_send': "📤 Send Files",
        'btn_help': "❓ Help",
        'btn_back': "◀️ Back to Menu"
    },
    'vi': {
        'not_configured': "⚠️ Bot chưa được cấu hình đầy đủ (thiếu ID). Vui lòng báo admin.",
        'join_req': "❌ **Chưa cấp quyền**\n\nBạn cần phải tham gia cả Kênh (Channel) và Nhóm thảo luận (Group) để sử dụng bot.\nVui lòng tham gia qua các nút bên dưới, sau đó bấm **Kiểm tra**.",
        'btn_channel': "📢 Vào Kênh",
        'btn_group': "💬 Vào Nhóm",
        'btn_verify': "🔄 Kiểm tra đã tham gia",
        'verify_fail': "⚠️ Bạn vẫn chưa tham gia đủ cả Kênh và Nhóm. Vui lòng thử lại!",
        'main_menu': "✅ **Menu Chính**\n\nChọn một chức năng bên dưới:",
        'btn_pref': "⚙️ Cài đặt File",
        'btn_mypref': "📋 Xem Cài đặt",
        'btn_list': "📁 Danh sách File",
        'btn_send': "📤 Nhận File",
        'btn_help': "❓ Trợ giúp",
        'btn_back': "◀️ Quay lại Menu"
    }
}

def get_text(lang: str, key: str) -> str:
    """Lấy text theo ngôn ngữ, mặc định tiếng Anh nếu không có."""
    return LANG.get(lang, LANG['en']).get(key, f"Missing text: {key}")

def load_user_preferences():
    if os.path.exists(USER_PREFERENCES_FILE):
        try:
            with open(USER_PREFERENCES_FILE, 'r') as f: return json.load(f)
        except: pass
    return {}

def save_user_preferences(preferences):
    try:
        with open(USER_PREFERENCES_FILE, 'w') as f: json.dump(preferences, f, indent=2)
    except: pass

async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> bool:
    """Kiểm tra user có trong 1 group/channel cụ thể không."""
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        if member.status == 'restricted':
            return member.can_send_messages if hasattr(member, 'can_send_messages') else False
        return False
    except TelegramError as e:
        logger.error(f"Membership check error for chat {chat_id}: {e}")
        return False

# ================= CORE FLOW =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bắt đầu: Cho chọn ngôn ngữ."""
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "👋 Welcome! Vui lòng chọn ngôn ngữ / Please select your language:",
        reply_markup=reply_markup
    )

async def check_and_show_menu(query, context: ContextTypes.DEFAULT_TYPE, lang: str, show_alert=False) -> None:
    """Kiểm tra điều kiện tham gia 2 nhóm. Nếu đủ thì hiện menu, thiếu thì bắt join."""
    user = query.from_user
    
    if CHANNEL_ID == 0 or GROUP_ID == 0:
        await query.edit_message_text(get_text(lang, 'not_configured'))
        return

    # Check cả 2 ID
    in_channel = await check_membership(context, user.id, CHANNEL_ID)
    in_group = await check_membership(context, user.id, GROUP_ID)

    if not (in_channel and in_group):
        # Nếu đang bấm nút verify mà fail thì hiện popup thông báo nhỏ
        if show_alert:
            await query.answer(get_text(lang, 'verify_fail'), show_alert=True)
            
        # Gửi lại giao diện bắt join nhóm
        keyboard = [
            [
                InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL),
                InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)
            ],
            [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]
        ]
        await query.edit_message_text(
            f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'join_req')}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Nếu đã đủ điều kiện -> Hiện Main Menu
    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, 'btn_pref'), callback_data="mode_preferences"),
            InlineKeyboardButton(get_text(lang, 'btn_mypref'), callback_data="mode_mypreferences"),
        ],
        [
            InlineKeyboardButton(get_text(lang, 'btn_list'), callback_data="mode_list"),
            InlineKeyboardButton(get_text(lang, 'btn_send'), callback_data="mode_send"),
        ],
        [
            InlineKeyboardButton(get_text(lang, 'btn_help'), callback_data="mode_help"),
        ],
    ]
    await query.edit_message_text(
        f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'main_menu')}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tất cả các nút bấm."""
    query = update.callback_query
    data = query.data

    # Xử lý chọn ngôn ngữ
    if data.startswith("lang_"):
        lang = data.split('_')[1] # 'vi' hoặc 'en'
        context.user_data['lang'] = lang # Lưu vào bộ nhớ
        await query.answer()
        await check_and_show_menu(query, context, lang)
        return
        
    # Lấy ngôn ngữ đang chọn, nếu không có mặc định là tiếng Anh
    lang = context.user_data.get('lang', 'en')

    if data == "verify_join":
        await check_and_show_menu(query, context, lang, show_alert=True)
        
    elif data == "mode_start":
        await query.answer()
        await check_and_show_menu(query, context, lang)

    elif data == "mode_help":
        await query.answer()
        help_text = "🤖 **Hướng dẫn / Help**\nCài đặt file bạn muốn, sau đó dùng lệnh Tải file."
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "mode_preferences":
        await query.answer()
        keyboard = [
            [InlineKeyboardButton(f"📄 Documents", callback_data="pref_document")],
            [InlineKeyboardButton(f"🖼️ Images", callback_data="pref_image")],
            [InlineKeyboardButton(f"🎬 Videos", callback_data="pref_video")],
            [InlineKeyboardButton(f"🎵 Audio", callback_data="pref_audio")],
            [InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")],
        ]
        await query.edit_message_text("📋 **Select preferred files:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("pref_"):
        ftype = data.split('_')[1]
        preferences = load_user_preferences()
        user_id = str(query.from_user.id)
        
        if user_id not in preferences:
            preferences[user_id] = {'username': query.from_user.username or 'Unknown', 'file_types': []}
            
        if ftype not in preferences[user_id]['file_types']:
            preferences[user_id]['file_types'].append(ftype)
            save_user_preferences(preferences)
            await query.answer(f"✅ Đã thêm / Added {ftype}!")
        else:
            await query.answer(f"ℹ️ Đã có sẵn / Already selected!", show_alert=False)

    elif data == "mode_mypreferences":
        await query.answer()
        prefs = load_user_preferences().get(str(query.from_user.id), {}).get('file_types', [])
        text = "✅ File Types:\n" + "\n".join(prefs) if prefs else "❌ Trống / Empty"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    # Bạn có thể tiếp tục bổ sung lại logic list_files_mode và send_files_mode ở đây
    # Lưu ý: dùng await query.edit_message_text(...) thay vì update.message.reply_text(...)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Bot is starting (Multilang & 2-Group Check)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()