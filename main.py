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

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
GROUP_ID = int(os.getenv('GROUP_ID', 0))
CHANNEL_URL = os.getenv('CHANNEL_URL', 'https://t.me/')
GROUP_URL = os.getenv('GROUP_URL', 'https://t.me/')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set.")

# --- CẤU TRÚC DỮ LIỆU MỚI ---
BASE_FILES_DIR = "files"
DATABASE_FILE = os.path.join(BASE_FILES_DIR, "database.txt")

os.makedirs(BASE_FILES_DIR, exist_ok=True)
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        # Cấu trúc: Tên file = File_ID | Mật khẩu
        f.write("Tên_Theme_Mau.zip=MÃ_FILE_ID_MẪU|123456\n")

# --- HÀM ĐỌC DATABASE ---
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

# --- TỪ ĐIỂN SONG NGỮ ---
LANG = {
    'en': {
        'not_configured': "⚠️ Bot missing IDs.",
        'join_req': "❌ **Access Denied**\nYou must join both our Channel and Group.",
        'btn_channel': "📢 Join Channel",
        'btn_group': "💬 Join Group",
        'btn_verify': "🔄 Verify",
        'verify_fail': "⚠️ You haven't joined both yet!",
        'main_menu': "✅ **Main Menu**",
        'btn_themes': "🎨 Theme List",
        'btn_pass': "🔑 Get Passwords",
        'btn_help': "❓ Help",
        'btn_back': "◀️ Back",
        'no_themes': "📭 No themes available.",
        'not_found': "❌ File not found."
    },
    'vi': {
        'not_configured': "⚠️ Bot thiếu ID.",
        'join_req': "❌ **Chưa cấp quyền**\nBạn cần tham gia cả Kênh và Nhóm để dùng bot.",
        'btn_channel': "📢 Vào Kênh",
        'btn_group': "💬 Vào Nhóm",
        'btn_verify': "🔄 Kiểm tra",
        'verify_fail': "⚠️ Bạn chưa tham gia đủ!",
        'main_menu': "✅ **Menu Chính**",
        'btn_themes': "🎨 Danh sách Theme",
        'btn_pass': "🔑 Lấy Mật Khẩu",
        'btn_help': "❓ Trợ giúp",
        'btn_back': "◀️ Quay lại",
        'no_themes': "📭 Chưa có theme nào.",
        'not_found': "❌ File không tồn tại."
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    text = LANG.get(lang, LANG['en']).get(key, f"Missing text: {key}")
    return text.format(**kwargs) if kwargs else text

# --- KIỂM TRA THÀNH VIÊN ---
async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator'] or (member.status == 'restricted' and getattr(member, 'can_send_messages', False))
    except:
        return False

# --- BỘ TẠO FILE ID TỰ ĐỘNG (Dành cho Admin) ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    file_id = doc.file_id
    file_name = doc.file_name or "Unknown_File"
    
    reply_text = (
        f"✅ **Đã lấy File ID thành công!**\n\n"
        f"Tên file: `{file_name}`\n"
        f"Mã File ID:\n`{file_id}`\n\n"
        f"*(Chạm vào mã để copy, sau đó dán vào file database.txt trên GitHub)*"
    )
    await update.message.reply_text(reply_text, parse_mode="Markdown")

# ================= CORE FLOW =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")], [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]]
    await update.effective_message.reply_text("👋 Welcome! Chọn ngôn ngữ / Select language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_and_show_menu(query, context, lang, show_alert=False):
    user = query.from_user
    if not (await check_membership(context, user.id, CHANNEL_ID) and await check_membership(context, user.id, GROUP_ID)):
        if show_alert: await query.answer(get_text(lang, 'verify_fail'), show_alert=True)
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL), InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)],
            [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]
        ]
        await query.edit_message_text(f"Hi {user.mention_html()}!\n{get_text(lang, 'join_req')}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'btn_themes'), callback_data="mode_themes")],
        [InlineKeyboardButton(get_text(lang, 'btn_pass'), callback_data="mode_password")],
    ]
    await query.edit_message_text(f"Hi {user.mention_html()}!\n{get_text(lang, 'main_menu')}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

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

    if data == "verify_join" or data == "mode_start":
        if data == "mode_start": await query.answer()
        await check_and_show_menu(query, context, lang, show_alert=(data=="verify_join"))

    elif data == "mode_password":
        await query.answer()
        db = get_database()
        msg = "🔐 **Danh sách Mật khẩu:**\n\n" if db else "📭 Chưa có dữ liệu."
        for name, info in db.items():
            msg += f"🔸 **{name}:** `{info['pass']}`\n"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "mode_themes":
        await query.answer()
        db = get_database()
        if not db:
            keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
            await query.edit_message_text(get_text(lang, 'no_themes'), reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        keyboard = [[InlineKeyboardButton(f"🎨 {name}", callback_data=f"send_{name[:40]}")] for name in db.keys()]
        keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")])
        await query.edit_message_text(f"📁 **{get_text(lang, 'btn_themes')}**:\nChọn một file để tải:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("send_"):
        short_name = data.split('send_', 1)[1]
        db = get_database()
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        
        if actual_name:
            await query.answer()
            file_id = db[actual_name]['id']
            file_pass = db[actual_name]['pass']
            caption_text = f"🎁 **{actual_name}**\n🔑 Pass: `{file_pass}`"
            
            try:
                # GỬI BẰNG FILE ID SIÊU TỐC
                await query.message.reply_document(document=file_id, caption=caption_text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Lỗi gửi file ID: {e}")
                await query.message.reply_text("❌ Lỗi: Mã File ID không hợp lệ hoặc file đã bị xóa khỏi hệ thống Telegram.")
        else:
            await query.answer(get_text(lang, 'not_found'), show_alert=True)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    # Handler mới: Bắt mọi file gửi vào bot để nhả ra File ID
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("🤖 Bot is starting (File ID Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()