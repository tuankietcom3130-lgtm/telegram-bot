#!/usr/bin/env python3
import logging
import os
import httpx  # Thư viện có sẵn để cào dữ liệu qua mạng
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
GUIDE_VIDEO_ID = os.getenv('GUIDE_VIDEO_ID', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')
CHANNEL_URL = os.getenv('CHANNEL_URL', 'https://t.me/')
GROUP_URL = os.getenv('GROUP_URL', 'https://t.me/')

if not BOT_TOKEN:
    raise ValueError("Lỗi: Chưa cấu hình BOT_TOKEN trong file .env.")

# --- CẤU TRÚC DỮ LIỆU ---
BASE_FILES_DIR = "files"
USERS_FILE = os.path.join(BASE_FILES_DIR, "users.txt") # File users vẫn lưu cục bộ trên VPS

os.makedirs(BASE_FILES_DIR, exist_ok=True)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        pass

# --- HÀM ĐỌC DATABASE TRỰC TIẾP TỪ GITHUB (ASYNC) ---
async def get_database() -> dict:
    db = {}
    if not DATABASE_URL:
        logger.error("Lỗi: Chưa cấu hình DATABASE_URL trong file .env")
        return db
        
    try:
        # Tự động lên mạng kết nối với GitHub để lấy nội dung file database.txt mới nhất
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(DATABASE_URL)
            if response.status_code == 200:
                lines = response.text.splitlines()
                for line in lines:
                    if '=' in line and '|' in line:
                        name, rest = line.strip().split('=', 1)
                        parts = rest.split('|')
                        file_id = parts[0].strip()
                        pwd = parts[1].strip() if len(parts) > 1 else "None"
                        preview_id = parts[2].strip() if len(parts) > 2 else "None"
                        date = parts[3].strip() if len(parts) > 3 else "Đang cập nhật"
                        db[name.strip()] = {'id': file_id, 'pass': pwd, 'preview': preview_id, 'date': date}
            else:
                logger.error(f"GitHub trả về mã lỗi: {response.status_code}")
    except Exception as e:
        logger.error(f"Không thể kết nối đến GitHub Raw URL: {e}")
        
    return db

def track_user(user_id: int):
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = set(f.read().splitlines())
    if str(user_id) not in users:
        with open(USERS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{user_id}\n")

def get_user_count() -> int:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return len(f.read().splitlines())
    return 0

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
        'guide_text': "📖 <b>How to use the extraction password:</b>\n\nPlease watch the tutorial video above carefully to know how to copy the password and extract the theme file properly without errors.",
        'no_guide_video': "⚠️ The tutorial video has not been updated yet. Please contact the admin.",
        'group_alert': "🤖 <b>Theme Library</b>\n\nTo view the theme list, check preview images, and download files, please click the button below to chat privately with me!",
        'btn_chat_bot': "🚀 Chat with Bot",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n📅 <b>Updated:</b> <code>{date}</code>\n🔑 <b>Pass:</b> <code>{pwd}</code>\n\nSelect an action below:",
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
        'guide_text': "📖 <b>Hướng dẫn nhập mật khẩu giải nén:</b>\n\nBạn vui lòng xem kỹ video hướng dẫn ở trên để biết cách copy mật khẩu và giải nén file theme đúng cách, tránh bị lỗi nhé!",
        'no_guide_video': "⚠️ Hiện tại video hướng dẫn chưa được cập nhật trên hệ thống.",
        'group_alert': "🤖 <b>Kho Theme</b>\n\nĐể xem danh sách, ảnh preview và tải các bản theme mới nhất, bạn vui lòng bấm vào nút bên dưới để trò chuyện riêng với Bot nhé!",
        'btn_chat_bot': "🚀 Trò Chuyện Với Bot",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n📅 <b>Cập nhật:</b> <code>{date}</code>\n🔑 <b>Pass giải nén:</b> <code>{pwd}</code>\n\nBạn muốn thực hiện thao tác nào:",
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

# --- TÍNH NĂNG DÀNH CHO ADMIN ---
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    if update.effective_chat.type != 'private':
        await update.message.reply_text("⚠️ Lệnh này chỉ dùng được trong phần chat riêng với Bot.")
        return

    db_data = await get_database()
    theme_count = len(db_data)
    user_count = get_user_count()

    admin_text = (
        "👨‍💻 <b>BẢNG ĐIỀU KHIỂN QUẢN TRỊ VIÊN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Tổng số Người dùng:</b> <code>{user_count}</code>\n"
        f"🎨 <b>Tổng số Chủ đề (Theme):</b> <code>{theme_count}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>💡 Hệ thống hiện đang đọc dữ liệu trực tiếp từ GitHub Cloud Cloud.</i>"
    )
    await update.message.reply_text(admin_text, parse_mode="HTML")

async def handle_admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return

    if update.message.document:
        doc = update.message.document
        await update.message.reply_text(f"✅ <b>Mã File ID (Tệp):</b>\n<code>{doc.file_id}</code>", parse_mode="HTML")
    elif update.message.photo:
        photo_id = update.message.photo[-1].file_id
        await update.message.reply_text(f"✅ <b>Mã File ID (Ảnh Preview):</b>\n<code>{photo_id}</code>", parse_mode="HTML")
    elif update.message.video:
        video_id = update.message.video.file_id
        await update.message.reply_text(f"✅ <b>Mã File ID (Video Hướng Dẫn):</b>\n<code>{video_id}</code>", parse_mode="HTML")

# --- LỆNH /theme & /langs CHO NHÓM ---
async def theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']:
        lang = context.chat_data.get('lang', 'vi')
        bot_username = context.bot.username
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_chat_bot'), url=f"https://t.me/{bot_username}?start=true")]]
        await update.message.reply_text(get_text(lang, 'group_alert'), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("Vui lòng sử dụng lệnh /start để mở Menu chính.")

async def langs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    if chat_type in ['group', 'supergroup']:
        keyboard = [
            [InlineKeyboardButton("Việt Nam 🇻🇳", callback_data="setlang_vi")],
            [InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en")]
        ]
        await update.message.reply_text(
            "⚙️ <b>Cấu hình ngôn ngữ hiển thị của Bot trong nhóm:</b>\n"
            "Select the default display language for the Bot in this group:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================= CORE FLOW =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    track_user(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")], 
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    welcome_text = (
        "🇻🇳 Xin chào! Vui lòng chọn ngôn ngữ của bạn để bắt đầu sử dụng Bot.\n\n"
        "🇬🇧 Hello! Please select your preferred language to start using the Bot."
    )
    await update.effective_message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def check_and_show_menu(query, context, lang, show_alert=False):
    user = query.from_user
    track_user(user.id)
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

    if data.startswith("setlang_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("❌ Bạn không có quyền thay đổi cấu hình này.", show_alert=True)
            return
        new_lang = data.split('_')[1]
        context.chat_data['lang'] = new_lang
        await query.answer("✅ Đã cập nhật ngôn ngữ nhóm!", show_alert=True)
        msg = "⚙️ <b>Cấu hình nhóm</b>\n\n"
        if new_lang == 'vi':
            msg += "Ngôn ngữ hiển thị khi gõ lệnh <code>/theme</code> đã được chuyển sang: <b>Tiếng Việt</b> 🇻🇳"
        else:
            msg += "The display language for <code>/theme</code> command has been switched to: <b>English</b> 🇬🇧"
        await query.edit_message_text(msg, parse_mode="HTML")
        return

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
        if GUIDE_VIDEO_ID:
            await query.answer()
            try:
                await query.message.delete()
                keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=GUIDE_VIDEO_ID,
                    caption=get_text(lang, 'guide_text'),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Lỗi gửi video hướng dẫn: {e}")
                await query.message.reply_text("❌ Không thể tải video hướng dẫn lúc này.")
        else:
            await query.answer(get_text(lang, 'no_guide_video'), show_alert=True)

    elif data == "mode_password":
        await query.answer()
        db = await get_database()  # Thêm await để đọc qua mạng
        msg = "🔑 <b>Danh sách mật khẩu giải nén:</b>\n\n" if db else "📭 Chưa có dữ liệu."
        for name, info in db.items():
            msg += f"🔸 <b>{name}:</b> <code>{info['pass']}</code>\n"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "mode_themes":
        await query.answer()
        db = await get_database()  # Thêm await để đọc qua mạng
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
        db = await get_database()  # Thêm await để đọc qua mạng
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if actual_name:
            pwd = db[actual_name]['pass']
            date = db[actual_name]['date']
            keyboard = [
                [InlineKeyboardButton(get_text(lang, 'btn_download'), callback_data=f"dl_{short_name}")],
                [InlineKeyboardButton(get_text(lang, 'btn_view_preview'), callback_data=f"pv_{short_name}")],
                [InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_themes")]
            ]
            await query.edit_message_text(get_text(lang, 'theme_title', name=actual_name, pwd=pwd, date=date), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else:
            await query.answer(get_text(lang, 'not_found'), show_alert=True)

    elif data.startswith("dl_"):
        short_name = data.split('dl_', 1)[1]
        db = await get_database()  # Thêm await để đọc qua mạng
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

    elif data.startswith("pv_"):
        short_name = data.split('pv_', 1)[1]
        db = await get_database()  # Thêm await để đọc qua mạng
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if actual_name:
            preview_id = db[actual_name]['preview']
            if preview_id and preview_id.lower() != 'none':
                await query.answer()
                try:
                    photo_ids = [pid.strip() for pid in preview_id.split(',')]
                    if len(photo_ids) == 1:
                        await query.message.reply_photo(photo=photo_ids[0], caption=f"🖼️ Ảnh preview của theme: <b>{actual_name}</b>", parse_mode="HTML")
                    else:
                        media_group = []
                        for i, pid in enumerate(photo_ids):
                            caption = f"🖼️ Ảnh preview của theme: <b>{actual_name}</b>" if i == 0 else None
                            media_group.append(InputMediaPhoto(media=pid, caption=caption, parse_mode="HTML"))
                        await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
                except Exception as e:
                    logger.error(f"Lỗi gửi ảnh: {e}")
                    await query.message.reply_text("❌ Không thể hiển thị hình ảnh preview.")
            else:
                await query.answer(get_text(lang, 'no_preview'), show_alert=True)
        else:
            await query.answer(get_text(lang, 'not_found'), show_alert=True)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("theme", theme_command))
    application.add_handler(CommandHandler("langs", langs_command))
    application.add_handler(CommandHandler("admin", admin_command)) 
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_admin_media))
    
    print("🤖 Bot đang chạy (Bản Cloud Database hoàn chỉnh)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()