#!/usr/bin/env python3
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# Load environment variables
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Lấy dữ liệu từ .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
GROUP_ID = int(os.getenv('GROUP_ID', 0))
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
CHANNEL_URL = os.getenv('CHANNEL_URL', 'https://t.me/')
GROUP_URL = os.getenv('GROUP_URL', 'https://t.me/')

if not BOT_TOKEN:
    raise ValueError("Lỗi: Chưa cấu hình BOT_TOKEN trong file .env.")

# --- CẤU TRÚC DỮ LIỆU ---
BASE_FILES_DIR = "files"
DATABASE_FILE = os.path.join(BASE_FILES_DIR, "database.txt")

os.makedirs(BASE_FILES_DIR, exist_ok=True)
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        f.write("Tên_Theme_Mau.zip=MÃ_FILE_ID_MẪU|123456\n")

def get_database() -> dict:
    db = {}
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and '|' in line:
                        name, rest = line.strip().split('=', 1)
                        file_id, pwd = rest.split('|', 1)
                        db[name.strip()] = {'id': file_id.strip(), 'pass': pwd.strip()}
        except Exception as e:
            logger.error(f"Lỗi đọc file database: {e}")
    return db

# --- TỪ ĐIỂN SONG NGỮ (PHONG CÁCH HIỆN ĐẠI, TECH-COMMUNITY) ---
LANG = {
    'en': {
        'not_configured': "⚠️ Bot is not fully configured. Please contact the admin.",
        'join_req': "🔒 <b>Access Required</b>\nTo use this bot, please join our official Channel and Group below, then click <b>Verify</b>.",
        'btn_channel': "📢 Channel",
        'btn_group': "💬 Group",
        'btn_verify': "🔄 Verify Membership",
        'verify_fail': "⚠️ Verification failed. Please make sure you have joined both and try again.",
        'main_menu': "⚡ <b>Main Menu</b>\nSelect an option below:",
        'btn_themes': "🎨 Theme List",
        'btn_pass': "🔑 Passwords",
        'btn_support': "💬 Contact Admin",
        'btn_back': "◀️ Back to Menu",
        'no_themes': "📭 No themes available at the moment.",
        'not_found': "❌ The requested file was not found or has been removed."
    },
    'vi': {
        'not_configured': "⚠️ Bot chưa được cấu hình đầy đủ. Vui lòng liên hệ Admin.",
        'join_req': "🔒 <b>Yêu cầu truy cập</b>\nĐể tiếp tục sử dụng Bot, bạn vui lòng tham gia vào Kênh và Nhóm hỗ trợ theo liên kết bên dưới. Sau đó nhấn nút <b>Xác nhận</b>.",
        'btn_channel': "📢 Kênh Thông Báo",
        'btn_group': "💬 Nhóm Thảo Luận",
        'btn_verify': "🔄 Xác Nhận Đã Tham Gia",
        'verify_fail': "⚠️ Xác nhận thất bại. Bạn vui lòng tham gia đủ cả Kênh và Nhóm rồi thử lại nhé!",
        'main_menu': "⚡ <b>Menu Chính</b>\nChào mừng bạn. Vui lòng chọn chức năng cần sử dụng:",
        'btn_themes': "🎨 Danh Sách Theme",
        'btn_pass': "🔑 Mật Khẩu",
        'btn_support': "💬 Liên Hệ Admin",
        'btn_back': "◀️ Quay Lại Menu",
        'no_themes': "📭 Hiện tại kho theme chưa có dữ liệu.",
        'not_found': "❌ Không tìm thấy file yêu cầu hoặc file đã bị xóa."
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    text = LANG.get(lang, LANG['en']).get(key, f"Missing text: {key}")
    return text.format(**kwargs) if kwargs else text

async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator'] or (member.status == 'restricted' and getattr(member, 'can_send_messages', False))
    except:
        return False

# --- HÀM LẤY FILE ID (CHỈ ADMIN) ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return

    doc = update.message.document
    file_id = doc.file_id
    file_name = doc.file_name or "Unknown_File"
    
    reply_text = (
        f"✅ <b>Đã lấy mã File ID thành công!</b>\n\n"
        f"Tên file: <code>{file_name}</code>\n"
        f"Mã File ID:\n<code>{file_id}</code>\n\n"
        f"<i>(Chạm vào mã để copy, sau đó cập nhật vào file database.txt)</i>"
    )
    await update.message.reply_text(reply_text, parse_mode="HTML")

# ================= CORE FLOW =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")], 
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    await update.effective_message.reply_text(
        "👋 Xin chào! \nVui lòng chọn ngôn ngữ để bắt đầu \n----------\n👋 Welcome! Please select your preferred language:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_and_show_menu(query, context, lang, show_alert=False):
    user = query.from_user
    if not (await check_membership(context, user.id, CHANNEL_ID) and await check_membership(context, user.id, GROUP_ID)):
        if show_alert: await query.answer(get_text(lang, 'verify_fail'), show_alert=True)
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL), InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)],
            [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]
        ]
        await query.edit_message_text(f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'join_req')}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    support_url = f"https://t.me/{ADMIN_USERNAME}" if ADMIN_USERNAME else f"tg://user?id={ADMIN_ID}"

    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'btn_themes'), callback_data="mode_themes")],
        [InlineKeyboardButton(get_text(lang, 'btn_pass'), callback_data="mode_password")],
        [InlineKeyboardButton(get_text(lang, 'btn_support'), url=support_url)]
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

    if data in ["verify_join", "mode_start"]:
        if data == "mode_start": await query.answer()
        await check_and_show_menu(query, context, lang, show_alert=(data=="verify_join"))

    elif data == "mode_password":
        await query.answer()
        db = get_database()
        msg = "🔑 <b>Danh sách mật khẩu giải nén:</b>\n\n" if db else "📭 Chưa có dữ liệu."
        for name, info in db.items():
            msg += f"🔸 <b>{name}:</b> <code>{info['pass']}</code>\n"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "mode_themes":
        await query.answer()
        db = get_database()
        if not db:
            keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
            await query.edit_message_text(get_text(lang, 'no_themes'), reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        keyboard = [[InlineKeyboardButton(f"🎨 {name}", callback_data=f"send_{name[:40]}")] for name in db.keys()]
        keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")])
        await query.edit_message_text(f"📁 <b>{get_text(lang, 'btn_themes')}</b>:\nChọn theme bạn muốn tải về dưới đây:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("send_"):
        short_name = data.split('send_', 1)[1]
        db = get_database()
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        
        if actual_name:
            await query.answer()
            file_id = db[actual_name]['id']
            file_pass = db[actual_name]['pass']
            caption_text = f"🎨 <b>{actual_name}</b>\n🔑 Pass giải nén: <code>{file_pass}</code>"
            
            try:
                await query.message.reply_document(document=file_id, caption=caption_text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Lỗi gửi file ID: {e}")
                await query.message.reply_text("❌ Gặp sự cố khi tải file từ máy chủ Telegram. Vui lòng thử lại sau.")
        else:
            await query.answer(get_text(lang, 'not_found'), show_alert=True)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("🤖 Bot đang chạy (Clean & Tech Style)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()