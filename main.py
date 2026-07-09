#!/usr/bin/env python3
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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
        f.write("Tên_Theme_Mau.zip=MÃ_FILE_ID_MẪU|123456|MÃ_ẢNH_1,MÃ_ẢNH_2\n")

def get_database() -> dict:
    db = {}
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and '|' in line:
                        name, rest = line.strip().split('=', 1)
                        parts = rest.split('|')
                        file_id = parts[0].strip()
                        pwd = parts[1].strip() if len(parts) > 1 else "None"
                        preview_id = parts[2].strip() if len(parts) > 2 else "None"
                        db[name.strip()] = {'id': file_id, 'pass': pwd, 'preview': preview_id}
        except Exception as e:
            logger.error(f"Lỗi đọc file database: {e}")
    return db

# --- TỪ ĐIỂN SONG NGỮ ---
LANG = {
    'en': {
        'not_configured': "⚠️ Bot is not fully configured. Please contact the admin.",
        'join_req': "🔒 <b>Access Required</b>\nTo use this bot, please join our official Channel and Group below, then click <b>Verify</b>.",
        'btn_channel': "📢 Channel",
        'btn_group': "💬 Group",
        'btn_verify': "🔄 Verify Membership",
        'verify_fail': "⚠️ Verification failed. Please join both and try again.",
        'main_menu': "⚡ <b>Main Menu</b>\nSelect an option below:",
        'btn_themes': "🎨 Theme List",
        'btn_pass': "🔑 Passwords",
        'btn_guide': "📖 Password Guide",
        'btn_support': "💬 Contact Admin",
        'btn_back': "◀️ Back to Menu",
        'no_themes': "📭 No themes available at the moment.",
        'not_found': "❌ The requested file was not found.",
        'guide_text': "📖 <b>How to use the extraction password:</b>\n\n1. Tap the password string inside the bot to auto-copy it.\n2. Use extraction apps like <b>ZArchiver</b> (Android) or <b>Documents</b> (iOS).\n3. Paste the exact password. Make sure there are no accidental trailing spaces.",
        'group_alert': "🤖 <b>Theme Library</b>\n\nTo view the theme list, check preview images, and download files, please click the button below to chat privately with me!",
        'btn_chat_bot': "🚀 Chat with Bot",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n🔑 <b>Pass:</b> <code>{pwd}</code>\n\nSelect an action below:",
        'btn_download': "📥 Download File",
        'btn_view_preview': "🖼️ View Preview",
        'no_preview': "⚠️ This theme does not have a preview image available."
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
        'btn_pass': "🔑 Mật Khẩu Giải Nén",
        'btn_guide': "📖 Hướng Dẫn Nhập Pass",
        'btn_support': "💬 Liên Hệ Admin",
        'btn_back': "◀️ Quay Lại Menu",
        'no_themes': "📭 Hiện tại kho theme chưa có dữ liệu.",
        'not_found': "❌ Không tìm thấy file yêu cầu hoặc file đã bị xóa.",
        'guide_text': "📖 <b>Hướng dẫn nhập mật khẩu giải nén:</b>\n\n1. Chạm vào đoạn mật khẩu được bọc trong khung để tự động copy.\n2. Sử dụng các ứng dụng giải nén chuyên dụng như <b>ZArchiver</b> (Android) hoặc <b>Documents</b> (iOS).\n3. Dán (Paste) chính xác mật khẩu vào ô yêu cầu. Lưu ý xóa khoảng trắng thừa nếu có.",
        'group_alert': "🤖 <b>Kho Theme</b>\n\nĐể xem danh sách, ảnh preview và tải các bản theme mới nhất, bạn vui lòng bấm vào nút bên dưới để trò chuyện riêng với Bot nhé!",
        'btn_chat_bot': "🚀 Trò Chuyện Với Bot",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n🔑 <b>Pass giải nén:</b> <code>{pwd}</code>\n\nBạn muốn thực hiện thao tác nào:",
        'btn_download': "📥 Tải File Theme",
        'btn_view_preview': "🖼️ Xem Ảnh Preview",
        'no_preview': "⚠️ Bản theme này hiện chưa được cập nhật ảnh preview."
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

# --- TÍNH NĂNG CHAT TRONG NHÓM ---
async def theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.effective_chat.type
    lang = 'vi' 
    if chat_type in ['group', 'supergroup']:
        bot_username = context.bot.username
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_chat_bot'), url=f"https://t.me/{bot_username}?start=true")]]
        await update.message.reply_text(
            get_text(lang, 'group_alert'), 
            parse_mode="HTML", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("Vui lòng sử dụng lệnh /start để mở Menu chính.")

# --- HÀM LẤY FILE ID & ẢNH ID ---
async def handle_admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return

    if update.message.document:
        doc = update.message.document
        await update.message.reply_text(
            f"✅ <b>Mã File ID (Tệp):</b>\n<code>{doc.file_id}</code>", parse_mode="HTML"
        )
    elif update.message.photo:
        photo_id = update.message.photo[-1].file_id
        await update.message.reply_text(
            f"✅ <b>Mã File ID (Ảnh Preview):</b>\n<code>{photo_id}</code>", parse_mode="HTML"
        )

# ================= CORE FLOW =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")], [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]]
    await update.effective_message.reply_text("👋 Xin chào! \nVui lòng chọn ngôn ngữ để bắt đầu\n👋Welcome! \nPlease select your preferred language:", reply_markup=InlineKeyboardMarkup(keyboard))

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
        [InlineKeyboardButton(get_text(lang, 'btn_guide'), callback_data="mode_guide")],
        [InlineKeyboardButton(get_text(lang, 'btn_support'), url=support_url)]
    ]
    await query.edit_message_text(f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'main_menu')}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    lang = context.user_data.get('lang', 'en')

    if data.startswith("lang_"):
        lang = data.split('_')[1]
        context.user_data['lang'] = lang
        await query.answer()
        await check_and_show_menu(query, context, lang)
        return

    if data in ["verify_join", "mode_start"]:
        if data == "mode_start": await query.answer()
        await check_and_show_menu(query, context, lang, show_alert=(data=="verify_join"))

    elif data == "mode_guide":
        await query.answer()
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(get_text(lang, 'guide_text'), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

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
            
        keyboard = [[InlineKeyboardButton(f"🎨 {name}", callback_data=f"sel_{name[:40]}")] for name in db.keys()]
        keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")])
        await query.edit_message_text(f"📁 <b>{get_text(lang, 'btn_themes')}</b>:\nChọn theme bạn muốn xem dưới đây:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("sel_"):
        await query.answer()
        short_name = data.split('sel_', 1)[1]
        db = get_database()
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        
        if actual_name:
            pwd = db[actual_name]['pass']
            keyboard = [
                [InlineKeyboardButton(get_text(lang, 'btn_download'), callback_data=f"dl_{short_name}")],
                [InlineKeyboardButton(get_text(lang, 'btn_view_preview'), callback_data=f"pv_{short_name}")],
                [InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_themes")]
            ]
            await query.edit_message_text(
                get_text(lang, 'theme_title', name=actual_name, pwd=pwd), 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="HTML"
            )
        else:
            await query.answer(get_text(lang, 'not_found'), show_alert=True)

    elif data.startswith("dl_"):
        short_name = data.split('dl_', 1)[1]
        db = get_database()
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        
        if actual_name:
            await query.answer()
            file_id = db[actual_name]['id']
            pwd = db[actual_name]['pass']
            caption_text = f"🎨 <b>{actual_name}</b>\n🔑 Pass giải nén: <code>{pwd}</code>"
            try:
                await query.message.reply_document(document=file_id, caption=caption_text, parse_mode="HTML")
            except:
                await query.message.reply_text("❌ Gặp sự cố khi tải file từ máy chủ Telegram.")
        else:
            await query.answer(get_text(lang, 'not_found'), show_alert=True)

    # TÍNH NĂNG XỬ LÝ ẢNH (HỖ TRỢ NHIỀU ẢNH LÀM ALBUM)
    elif data.startswith("pv_"):
        short_name = data.split('pv_', 1)[1]
        db = get_database()
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        
        if actual_name:
            preview_id = db[actual_name]['preview']
            if preview_id and preview_id.lower() != 'none':
                await query.answer()
                try:
                    # Tách các ID bằng dấu phẩy
                    photo_ids = [pid.strip() for pid in preview_id.split(',')]
                    
                    if len(photo_ids) == 1:
                        # Nếu chỉ có 1 ảnh, gửi bình thường
                        await query.message.reply_photo(photo=photo_ids[0], caption=f"🖼️ Ảnh preview của theme: <b>{actual_name}</b>", parse_mode="HTML")
                    else:
                        # Nếu có nhiều ảnh, gom lại thành Media Group (Album)
                        media_group = []
                        for i, pid in enumerate(photo_ids):
                            # Chỉ gắn caption vào tấm ảnh đầu tiên trong Album
                            caption = f"🖼️ Ảnh preview của theme: <b>{actual_name}</b>" if i == 0 else None
                            media_group.append(InputMediaPhoto(media=pid, caption=caption, parse_mode="HTML"))
                        
                        await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
                except Exception as e:
                    logger.error(f"Lỗi gửi ảnh: {e}")
                    await query.message.reply_text("❌ Không thể hiển thị hình ảnh preview này. Có thể mã ảnh bị sai.")
            else:
                await query.answer(get_text(lang, 'no_preview'), show_alert=True)
        else:
            await query.answer(get_text(lang, 'not_found'), show_alert=True)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("theme", theme_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_admin_media))
    
    print("🤖 Bot đang chạy (Bản hỗ trợ Multi-Image/Album)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()