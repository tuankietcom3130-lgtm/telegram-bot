#!/usr/bin/env python3
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Lấy cấu hình từ .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
GROUP_ID = int(os.getenv('GROUP_ID', 0))
CHANNEL_URL = os.getenv('CHANNEL_URL', 'https://t.me/')
GROUP_URL = os.getenv('GROUP_URL', 'https://t.me/')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set.")

# --- CẤU TRÚC THƯ MỤC MỚI ---
BASE_FILES_DIR = "files"
THEMES_DIR = os.path.join(BASE_FILES_DIR, "themes")
PASSWORD_FILE = os.path.join(BASE_FILES_DIR, "password.txt")

os.makedirs(THEMES_DIR, exist_ok=True)
if not os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE, 'w', encoding='utf-8') as f:
        f.write("default=123456\n")

# --- HÀM ĐỌC MẬT KHẨU TỪ FILE ---
def get_passwords() -> dict:
    pass_dict = {}
    if os.path.exists(PASSWORD_FILE):
        try:
            with open(PASSWORD_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        pass_dict[k.strip()] = v.strip()
        except Exception as e:
            logger.error(f"Lỗi đọc file password: {e}")
    return pass_dict

# --- TỪ ĐIỂN SONG NGỮ ---
LANG = {
    'en': {
        'not_configured': "⚠️ Bot is not fully configured (missing IDs). Please contact admin.",
        'join_req': "❌ **Access Denied**\n\nYou must join both our Channel and Group to use this bot.\nPlease join via the links below, then click **Verify**.",
        'btn_channel': "📢 Join Channel",
        'btn_group': "💬 Join Group",
        'btn_verify': "🔄 Verify Membership",
        'verify_fail': "⚠️ You haven't joined both yet. Please check again!",
        'main_menu': "✅ **Main Menu**\n\nChoose an action below:",
        'btn_themes': "🎨 Theme List",
        'btn_pass': "🔑 Get Passwords",
        'btn_help': "❓ Help",
        'btn_back': "◀️ Back to Menu",
        'no_themes': "📭 No themes available at the moment.",
        'sending': "📤 Sending `{filename}`...",
        'not_found': "❌ File `{filename}` is no longer available.",
        'help_text': "🤖 **Help**\n1. Select **Theme List** to download themes.\n2. Select **Get Passwords** to view all extraction passwords.\n\n*Note: Themes are updated regularly!*"
    },
    'vi': {
        'not_configured': "⚠️ Bot chưa được cấu hình đầy đủ (thiếu ID). Vui lòng báo admin.",
        'join_req': "❌ **Chưa cấp quyền**\n\nBạn cần phải tham gia cả Kênh và Nhóm để sử dụng bot.\nVui lòng tham gia qua các nút bên dưới, sau đó bấm **Kiểm tra**.",
        'btn_channel': "📢 Vào Kênh",
        'btn_group': "💬 Vào Nhóm",
        'btn_verify': "🔄 Kiểm tra đã tham gia",
        'verify_fail': "⚠️ Bạn vẫn chưa tham gia đủ cả Kênh và Nhóm. Vui lòng thử lại!",
        'main_menu': "✅ **Menu Chính**\n\nChọn một chức năng bên dưới:",
        'btn_themes': "🎨 Danh sách Theme",
        'btn_pass': "🔑 Lấy Mật Khẩu",
        'btn_help': "❓ Trợ giúp",
        'btn_back': "◀️ Quay lại Menu",
        'no_themes': "📭 Hiện tại chưa có theme nào được tải lên.",
        'sending': "📤 Đang gửi `{filename}` cho bạn...",
        'not_found': "❌ File `{filename}` không còn tồn tại hoặc đã bị xóa.",
        'help_text': "🤖 **Hướng dẫn**\n1. Chọn **Danh sách Theme** để tải file.\n2. Chọn **Lấy Mật Khẩu** để xem danh sách pass giải nén.\n\n*Lưu ý: File và mật khẩu sẽ được admin cập nhật liên tục!*"
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    text = LANG.get(lang, LANG['en']).get(key, f"Missing text: {key}")
    return text.format(**kwargs) if kwargs else text

# --- HÀM KIỂM TRA THÀNH VIÊN ---
async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']: return True
        if member.status == 'restricted': return getattr(member, 'can_send_messages', False)
        return False
    except TelegramError:
        return False

# ================= CORE FLOW =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    await update.effective_message.reply_text(
        "👋 Welcome! Vui lòng chọn ngôn ngữ / Please select your language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_and_show_menu(query, context: ContextTypes.DEFAULT_TYPE, lang: str, show_alert=False) -> None:
    user = query.from_user
    if CHANNEL_ID == 0 or GROUP_ID == 0:
        await query.edit_message_text(get_text(lang, 'not_configured'))
        return

    in_channel = await check_membership(context, user.id, CHANNEL_ID)
    in_group = await check_membership(context, user.id, GROUP_ID)

    if not (in_channel and in_group):
        if show_alert: await query.answer(get_text(lang, 'verify_fail'), show_alert=True)
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL),
             InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)],
            [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]
        ]
        await query.edit_message_text(f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'join_req')}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'btn_themes'), callback_data="mode_themes")],
        [InlineKeyboardButton(get_text(lang, 'btn_pass'), callback_data="mode_password")],
        [InlineKeyboardButton(get_text(lang, 'btn_help'), callback_data="mode_help")],
    ]
    await query.edit_message_text(f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'main_menu')}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    if data.startswith("lang_"):
        lang = data.split('_')[1]
        context.user_data['lang'] = lang
        await query.answer()
        await check_and_show_menu(query, context, lang)
        return
        
    lang = context.user_data.get('lang', 'en')

    if data == "verify_join":
        await check_and_show_menu(query, context, lang, show_alert=True)
        
    elif data == "mode_start":
        await query.answer()
        await check_and_show_menu(query, context, lang)

    elif data == "mode_help":
        await query.answer()
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(get_text(lang, 'help_text'), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "mode_password":
        await query.answer()
        pass_dict = get_passwords()
        
        if not pass_dict:
            msg = "📭 Hiện tại chưa có mật khẩu nào được lưu." if lang == 'vi' else "📭 No passwords stored currently."
        else:
            msg = "🔐 **Danh sách Mật khẩu / Passwords:**\n\n"
            for name, pwd in pass_dict.items():
                if name.lower() == 'default':
                    msg += f"🔹 **Chung (Default):** `{pwd}`\n"
                else:
                    msg += f"🔸 **{name}:** `{pwd}`\n"
            msg += "\n*(Chạm vào mật khẩu để copy)*"
            
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "mode_themes":
        await query.answer()
        themes = [f for f in os.listdir(THEMES_DIR) if os.path.isfile(os.path.join(THEMES_DIR, f))]
        
        if not themes:
            keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
            await query.edit_message_text(get_text(lang, 'no_themes'), reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        keyboard = []
        for theme in themes:
            safe_callback = f"send_{theme[:40]}" 
            keyboard.append([InlineKeyboardButton(f"🎨 {theme}", callback_data=safe_callback)])
            
        keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")])
        await query.edit_message_text(f"📁 **{get_text(lang, 'btn_themes')}**:\n\nChọn một file bên dưới để tải:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("send_"):
        short_filename = data.split('send_', 1)[1]
        all_themes = os.listdir(THEMES_DIR)
        actual_filename = next((f for f in all_themes if f.startswith(short_filename)), None)
        
        if actual_filename:
            filepath = os.path.join(THEMES_DIR, actual_filename)
            await query.answer()
            status_msg = await query.message.reply_text(get_text(lang, 'sending', filename=actual_filename), parse_mode="Markdown")
            
            # Đọc pass cho file cụ thể này
            pass_dict = get_passwords()
            file_pass = pass_dict.get(actual_filename, pass_dict.get('default', 'Không yêu cầu / No pass'))
            
            # Gắn trực tiếp mật khẩu vào caption của file
            caption_text = f"🎁 **{actual_filename}**\n🔑 Pass: `{file_pass}`"
            
            try:
                await query.message.reply_document(document=open(filepath, 'rb'), caption=caption_text, parse_mode="Markdown")
                await status_msg.delete() 
            except Exception as e:
                logger.error(f"Lỗi khi gửi file: {e}")
                await status_msg.edit_text("❌ Lỗi hệ thống khi gửi file.")
        else:
            await query.answer(get_text(lang, 'not_found', filename=short_filename), show_alert=True)


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Bot is starting (Multi-Password Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()