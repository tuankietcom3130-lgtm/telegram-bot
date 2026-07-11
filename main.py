#!/usr/bin/env python3
import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# Config logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BỘ LỌC TỰ ĐỘNG TIÊU HỦY KÝ TỰ ẨN (BOM) CỦA WINDOWS NOTEPAD ---
if os.path.exists('.env'):
    try:
        with open('.env', 'r', encoding='utf-8-sig') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()
    except Exception as e:
        logger.error(f"Lỗi quét file .env: {e}")

# Load đè lại bằng dotenv để đảm bảo không sót biến
load_dotenv()

# Lấy dữ liệu đã được làm sạch
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
GROUP_ID = int(os.getenv('GROUP_ID', 0))
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
GUIDE_VIDEO_ID = os.getenv('GUIDE_VIDEO_ID', '')
DONATE_IMAGE_ID = os.getenv('DONATE_IMAGE_ID', '') 
CHANNEL_URL = os.getenv('CHANNEL_URL', 'https://t.me/')
GROUP_URL = os.getenv('GROUP_URL', 'https://t.me/')

if not BOT_TOKEN:
    raise ValueError("Lỗi: Chưa cấu hình BOT_TOKEN trong file .env.")

# --- TRẠNG THÁI HOẠT ĐỘNG CỦA BOT ---
BOT_ACTIVE = True 

# --- CẤU TRÚC DỮ LIỆU CỤC BỘ TRÊN VPS ---
BASE_FILES_DIR = "files"
DATABASE_FILE = os.path.join(BASE_FILES_DIR, "database.txt")
USERS_FILE = os.path.join(BASE_FILES_DIR, "users.txt")

os.makedirs(BASE_FILES_DIR, exist_ok=True)
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f: pass
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f: pass

# --- HÀM XỬ LÝ DỮ LIỆU ---
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
                        date = parts[3].strip() if len(parts) > 3 else "Đang cập nhật"
                        db[name.strip()] = {'id': file_id, 'pass': pwd, 'preview': preview_id, 'date': date}
        except Exception as e:
            logger.error(f"Lỗi đọc file database: {e}")
    return db

def track_user(user_id: int):
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = set(f.read().splitlines())
    if str(user_id) not in users:
        with open(USERS_FILE, 'a', encoding='utf-8') as f: f.write(f"{user_id}\n")

def get_user_count() -> int:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                return len(set(lines))
        except: pass
    return 0

# --- HÀM TỰ ĐỘNG XÓA TIN NHẮN (CHẠY NGẦM) ---
async def delete_delayed(bot, chat_id, message_ids, delay):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except:
            pass

# --- TỪ ĐIỂN SONG NGỮ ---
LANG = {
    'en': {
        'not_configured': "⚠️ Bot is not fully configured. Please contact the admin.",
        'join_req': "🔒 <b>Access Required</b>\nTo use this bot, please join our official Channel and Group below, then click <b>Verify</b>.",
        'btn_channel': "📢 Channel", 'btn_group': "💬 Group", 'btn_verify': "🔄 Verify Membership", 'verify_fail': "⚠️ Verification failed. Please join both and try again.",
        'main_menu': "⚡ <b>Main Menu</b>\nSelect an option below:", 'btn_themes': "🎨 Theme List", 'btn_pass': "🔑 Passwords", 'btn_guide': "📖 Password Guide",
        'btn_donate': "☕ Support", 'btn_support': "💬 Contact Admin", 'btn_back': "◀️ Back to Menu", 'no_themes': "📭 No themes available at the moment.",
        'not_found': "❌ The requested file was not found.", 'guide_text': "📖 <b>How to use the password:</b>\n\nPlease watch the tutorial video above carefully to know how to copy and use the password properly without errors.",
        'no_guide_video': "⚠️ The tutorial video has not been updated yet. Please contact the admin.",
        'donate_text': "💖 <b>Thank you for your support!</b>\n\n🏦 <b>Bank:</b> MB Bank\n💳 <b>Account:</b> <code>29992992699999</code>\n👤 <b>Name:</b> DO DANG TUAN KIET",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n📅 <b>Updated:</b> <code>{date}</code>\n🔑 <b>Pass:</b> <code>{pwd}</code>\n\nSelect an action below:",
        'btn_download': "📥 Download File", 'btn_view_preview': "🖼️ View Preview", 'no_preview': "⚠️ This theme does not have a preview image available."
    },
    'vi': {
        'not_configured': "⚠️ Bot chưa được cấu hình đầy đủ. Vui lòng liên hệ Admin.",
        'join_req': "🔒 <b>Yêu cầu truy cập</b>\nĐể tiếp tục sử dụng Bot, bạn vui lòng tham gia vào Kênh và Nhóm hỗ trợ theo liên kết bên dưới. Sau đó nhấn nút <b>Xác nhận</b>.",
        'btn_channel': "📢 Kênh Thông Báo", 'btn_group': "💬 Nhóm Thảo Luận", 'btn_verify': "🔄 Xác Nhận Đã Tham Gia", 'verify_fail': "⚠️ Xác nhận thất bại. Bạn vui lòng tham gia đủ cả Kênh và Nhóm rồi thử lại nhé!",
        'main_menu': "⚡ <b>Menu Chính</b>\nChào mừng bạn. Vui lòng chọn chức năng cần sử dụng:", 'btn_themes': "🎨 Danh Sách Theme", 'btn_pass': "🔑 Mật Khẩu", 'btn_guide': "📖 Hướng Dẫn Nhập Pass",
        'btn_donate': "☕ Ủng Hộ", 'btn_support': "💬 Liên Hệ Admin", 'btn_back': "◀️ Quay Lại Menu", 'no_themes': "📭 Hiện tại kho theme chưa có dữ liệu.",
        'not_found': "❌ Không tìm thấy file yêu cầu hoặc file đã bị xóa.", 'guide_text': "📖 <b>Hướng dẫn nhập mật khẩu:</b>\n\nBạn vui lòng xem kỹ video hướng dẫn ở trên để biết cách copy và sử dụng mật khẩu đúng cách, tránh bị lỗi nhé!",
        'no_guide_video': "⚠️ Hiện tại video hướng dẫn chưa được cập nhật trên hệ thống.",
        'donate_text': "💖 <b>Cảm ơn bạn đã quan tâm!</b>\n\n🏦 <b>Ngân hàng:</b> MB Bank\n💳 <b>STK:</b> <code>29992992699999</code>\n👤 <b>Tên:</b> DO DANG TUAN KIET",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n📅 <b>Cập nhật:</b> <code>{date}</code>\n🔑 <b>Pass:</b> <code>{pwd}</code>\n\nBạn muốn thực hiện thao tác nào:",
        'btn_download': "📥 Tải File Theme", 'btn_view_preview': "🖼️ Xem Ảnh Preview", 'no_preview': "⚠️ Bản theme này hiện chưa được cập nhật ảnh preview."
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    text = LANG.get(lang, LANG['en']).get(key, f"Missing text: {key}")
    return text.format(**kwargs) if kwargs else text

async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator'] or (member.status == 'restricted' and getattr(member, 'can_send_messages', False))
    except: return False

# --- TÍNH NĂNG ĐIỀU KHIỂN CỦA ADMIN ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID or update.effective_chat.type != 'private': return
    help_text = (
        "🛠 <b>HƯỚNG DẪN QUẢN TRỊ VIÊN:</b>\n\n"
        "1️⃣ <b>Thêm Theme:</b> Reply file tệp với: <code>/add Tên Theme | Mật Khẩu | Ngày</code>\n"
        "2️⃣ <b>Thêm ảnh:</b> Reply ảnh với: <code>/addpv Tên_Theme</code>\n"
        "3️⃣ <b>Sửa Theme:</b> <code>/edit Tên Theme | Pass mới | Ngày mới</code>\n"
        "4️⃣ <b>Xóa Theme:</b> <code>/del Tên_Theme</code>\n"
        "5️⃣ <b>Trạng thái:</b> /status\n"
        "6️⃣ <b>Bật/Tắt Bot:</b> <code>/run</code> hoặc <code>/stop</code>\n"
        "7️⃣ <b>Ngôn ngữ nhóm:</b> /langs"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID or update.effective_chat.type != 'private': return
    db_data = get_database()
    current_status = "Đang chạy 🟢" if BOT_ACTIVE else "Đang tạm dừng bảo trì 🔴"
    theme_list_text = "".join([f"{i}. <code>{n}</code>\n" for i, n in enumerate(db_data.keys(), 1)]) if db_data else "<i>(Trống)</i>"
    await update.message.reply_text(
        f"📊 <b>BẢNG TRẠNG THÁI HỆ THỐNG</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚙️ <b>Trạng thái:</b> <b>{current_status}</b>\n👥 <b>User:</b> <code>{get_user_count()}</code>\n"
        f"🎨 <b>Theme:</b> <code>{len(db_data)}</code>\n\n📋 <b>DANH SÁCH THEME:</b>\n{theme_list_text}", parse_mode="HTML"
    )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global BOT_ACTIVE
    if update.effective_user.id == ADMIN_ID and update.effective_chat.type == 'private':
        BOT_ACTIVE = False
        await update.message.reply_text("💤 <b>Hệ thống ĐÃ TẠM DỪNG!</b>")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global BOT_ACTIVE
    if update.effective_user.id == ADMIN_ID and update.effective_chat.type == 'private':
        BOT_ACTIVE = True
        await update.message.reply_text("🚀 <b>Hệ thống HOẠT ĐỘNG TRỞ LẠI!</b>")

async def langs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id == ADMIN_ID and update.effective_chat.type in ['group', 'supergroup']:
        keyboard = [[InlineKeyboardButton("Việt Nam 🇻🇳", callback_data="setlang_vi")],[InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en")]]
        await update.message.reply_text("⚙️ <b>Cấu hình ngôn ngữ mặc định của nhóm:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# --- HỆ THỐNG XỬ LÝ MEDIA / LỆNH QUẢN TRỊ CHO ADMIN ---
async def handle_admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID or update.effective_chat.type != 'private': return
    text = (update.message.text or update.message.caption or "").strip()
    target_msg = update.message.reply_to_message if update.message.reply_to_message else update.message

    if text.startswith("/del"):
        theme_to_delete = text.replace("/del", "").strip()
        lines = []
        deleted = False
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith(theme_to_delete + "="): deleted = True
                else: f.write(line)
        await update.message.reply_text(f"🗑️ Đã xóa theme: {theme_to_delete}" if deleted else f"❌ Không tìm thấy theme {theme_to_delete}")

    elif text.startswith("/edit"):
        try:
            parts = text.replace("/edit", "").strip().split('|')
            theme_name_target = parts[0].strip()
            lines = []
            updated = False
            if os.path.exists(DATABASE_FILE):
                with open(DATABASE_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
            with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
                for line in lines:
                    if '=' in line and line.strip().split('=', 1)[0].strip() == theme_name_target:
                        name, rest = line.strip().split('=', 1)
                        p = rest.split('|')
                        file_id = target_msg.document.file_id if (target_msg and target_msg.document) else p[0].strip()
                        pwd = parts[1].strip() if (len(parts) > 1 and parts[1].strip()) else p[1].strip()
                        date = parts[2].strip() if (len(parts) > 2 and parts[2].strip()) else p[3].strip()
                        f.write(f"{name}={file_id}|{pwd}|{p[2].strip()}|{date}\n")
                        updated = True
                    else: f.write(line)
            await update.message.reply_text(f"📝 Đã sửa theme: {theme_name_target}" if updated else f"❌ Không tìm thấy theme")
        except Exception as e: await update.message.reply_text(f"❌ Lỗi: {e}")

    elif text.startswith("/addpv"):
        if not target_msg.photo: return await update.message.reply_text("❌ Hãy Reply vào tin nhắn ảnh!")
        try:
            theme_name_target = text.replace("/addpv", "").strip()
            lines = []
            updated = False
            if os.path.exists(DATABASE_FILE):
                with open(DATABASE_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
            with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
                for line in lines:
                    if '=' in line and line.strip().split('=', 1)[0].strip() == theme_name_target:
                        name, rest = line.strip().split('=', 1)
                        parts = rest.split('|')
                        new_pv = target_msg.photo[-1].file_id if parts[2].strip().lower() == 'none' else f"{parts[2].strip()},{target_msg.photo[-1].file_id}"
                        f.write(f"{name}={parts[0].strip()}|{parts[1].strip()}|{new_pv}|{parts[3].strip()}\n")
                        updated = True
                    else: f.write(line)
            await update.message.reply_text(f"🖼️ Đã thêm ảnh vào theme {theme_name_target}" if updated else f"❌ Không tìm thấy theme")
        except Exception as e: await update.message.reply_text(f"❌ Lỗi: {e}")
            
    elif text.startswith("/add"):
        if not target_msg.document: return await update.message.reply_text("❌ Hãy Reply vào file!")
        try:
            parts = text.replace("/add", "").strip().split('|')
            theme_name = parts[0].strip()
            pwd = parts[1].strip() if len(parts) > 1 else "None"
            date = parts[2].strip() if len(parts) > 2 else "Đang cập nhật"
            with open(DATABASE_FILE, 'a', encoding='utf-8') as f: f.write(f"{theme_name}={target_msg.document.file_id}|{pwd}|None|{date}\n")
            await update.message.reply_text(f"✅ Đã thêm theme: {theme_name}")
        except Exception as e: await update.message.reply_text(f"❌ Sai cú pháp /add")
            
    else:
        if update.message.document: await update.message.reply_text(f"✅ <b>File ID:</b>\n<code>{update.message.document.file_id}</code>", parse_mode="HTML")
        elif update.message.photo: await update.message.reply_text(f"✅ <b>Photo ID:</b>\n<code>{update.message.photo[-1].file_id}</code>", parse_mode="HTML")
        elif update.message.video: await update.message.reply_text(f"✅ <b>Video ID:</b>\n<code>{update.message.video.file_id}</code>", parse_mode="HTML")

# ================= CORE FLOW USER =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type in ['group', 'supergroup']: return 
    if not BOT_ACTIVE and update.effective_user.id != ADMIN_ID: return 
    track_user(update.effective_user.id)
    keyboard = [[InlineKeyboardButton("💡 Tiếng Việt 🇻🇳", callback_data="lang_vi"), InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")]]
    await update.effective_message.reply_text("Chọn ngôn ngữ / Select language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not BOT_ACTIVE and update.effective_user.id != ADMIN_ID: return
    chat_type = update.effective_chat.type
    user = update.effective_user
    track_user(user.id)
    
    lang = context.user_data.get('lang')
    if not lang:
        keyboard = [[InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi"), InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")]]
        sent_msg = await update.message.reply_text(f"Hi {user.mention_html()}! 👋\nChọn ngôn ngữ để mở Menu:", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        if chat_type in ['group', 'supergroup']: context.bot_data[f"owner_{sent_msg.message_id}"] = user.id
        return

    is_member = await check_membership(context, user.id, CHANNEL_ID) and await check_membership(context, user.id, GROUP_ID)
    if not is_member:
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL), InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)], [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'join_req')}"
    else:
        support_url = f"https://t.me/{ADMIN_USERNAME}" if ADMIN_USERNAME else f"tg://user?id={ADMIN_ID}"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_themes'), callback_data="mode_themes")],[InlineKeyboardButton(get_text(lang, 'btn_pass'), callback_data="mode_password")],[InlineKeyboardButton(get_text(lang, 'btn_guide'), callback_data="mode_guide")],[InlineKeyboardButton(get_text(lang, 'btn_donate'), callback_data="mode_donate"), InlineKeyboardButton(get_text(lang, 'btn_support'), url=support_url)]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'main_menu')}"
        
    sent_msg = await update.message.reply_text(msg_text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    if chat_type in ['group', 'supergroup']: context.bot_data[f"owner_{sent_msg.message_id}"] = user.id

async def check_and_show_menu(query, context, lang, show_alert=False):
    user = query.from_user
    is_member = await check_membership(context, user.id, CHANNEL_ID) and await check_membership(context, user.id, GROUP_ID)
    if not is_member:
        if show_alert: await query.answer(get_text(lang, 'verify_fail'), show_alert=True)
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL), InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)], [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'join_req')}"
    else:
        support_url = f"https://t.me/{ADMIN_USERNAME}" if ADMIN_USERNAME else f"tg://user?id={ADMIN_ID}"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_themes'), callback_data="mode_themes")],[InlineKeyboardButton(get_text(lang, 'btn_pass'), callback_data="mode_password")],[InlineKeyboardButton(get_text(lang, 'btn_guide'), callback_data="mode_guide")],[InlineKeyboardButton(get_text(lang, 'btn_donate'), callback_data="mode_donate"), InlineKeyboardButton(get_text(lang, 'btn_support'), url=support_url)]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'main_menu')}"
    try:
        if query.message.video or query.message.photo or query.message.document:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=msg_text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        else: await query.edit_message_text(text=msg_text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    except: pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    chat_type = query.message.chat.type
    user_clicking = query.from_user.id
    
    if not BOT_ACTIVE and user_clicking != ADMIN_ID: 
        await query.answer("⚠️ Bot đang tạm dừng bảo trì!", show_alert=True)
        return

    if chat_type in ['group', 'supergroup']:
        owner_id = context.bot_data.get(f"owner_{query.message.message_id}")
        if owner_id and user_clicking != owner_id and user_clicking != ADMIN_ID:
            await query.answer("❌ Menu này của người khác. Hãy gõ /theme để tự tạo riêng!", show_alert=True)
            return

    lang = context.user_data.get('lang')
    if not lang and not data.startswith("lang_"): lang = context.chat_data.get('lang', 'vi')

    if data.startswith("setlang_"):
        if user_clicking != ADMIN_ID: return
        context.chat_data['lang'] = data.split('_')[1]
        await query.answer("✅ Đã cập nhật cài đặt nhóm!", show_alert=True)
        await query.message.delete()
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
                await context.bot.send_video(chat_id=query.message.chat_id, video=GUIDE_VIDEO_ID, caption=get_text(lang, 'guide_text'), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            except: pass
        else: await query.answer(get_text(lang, 'no_guide_video'), show_alert=True)

    elif data == "mode_donate":
        await query.answer()
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        if DONATE_IMAGE_ID:
            try:
                await query.message.delete()
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=DONATE_IMAGE_ID, caption=get_text(lang, 'donate_text'), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            except: pass
        else: await query.edit_message_text(get_text(lang, 'donate_text'), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "mode_password":
        await query.answer()
        db = get_database() 
        msg = "🔑 <b>Danh sách mật khẩu:</b>\n\n" if db else "📭 Chưa có dữ liệu."
        for name, info in db.items(): msg += f"🔸 <b>{name}:</b> <code>{info['pass']}</code>\n"
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
        await query.edit_message_text(f"📁 <b>{get_text(lang, 'btn_themes')}</b>:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("sel_"):
        await query.answer()
        short_name = data.split('sel_', 1)[1]
        db = get_database() 
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if actual_name:
            keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_download'), callback_data=f"dl_{short_name}")],[InlineKeyboardButton(get_text(lang, 'btn_view_preview'), callback_data=f"pv_{short_name}")],[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_themes")]]
            await query.edit_message_text(get_text(lang, 'theme_title', name=actual_name, pwd=db[actual_name]['pass'], date=db[actual_name]['date']), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else: await query.answer(get_text(lang, 'not_found'), show_alert=True)

    elif data.startswith("dl_"):
        short_name = data.split('dl_', 1)[1]
        db = get_database() 
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if actual_name:
            await query.answer()
            try: await query.message.reply_document(document=db[actual_name]['id'], caption=f"🎨 <b>{actual_name}</b>\n🔑 Pass: <code>{db[actual_name]['pass']}</code>", parse_mode="HTML")
            except: pass
        else: await query.answer(get_text(lang, 'not_found'), show_alert=True)

    # --- TÍNH NĂNG MỚI: TỰ ĐỘNG XÓA ẢNH SAU 60 GIÂY ---
    elif data.startswith("pv_"):
        short_name = data.split('pv_', 1)[1]
        db = get_database() 
        actual_name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if actual_name:
            preview_id = db[actual_name]['preview']
            if preview_id and preview_id.lower() != 'none':
                await query.answer("Đang tải ảnh... (Sẽ tự xóa sau 1 phút) ⏳")
                try:
                    photo_ids = [pid.strip() for pid in preview_id.split(',')]
                    sent_msgs = []
                    
                    if len(photo_ids) == 1: 
                        msg = await query.message.reply_photo(photo=photo_ids[0], caption=f"🖼️ Ảnh preview: <b>{actual_name}</b>\n⏳ <i>Tự động xóa sau 60s</i>", parse_mode="HTML")
                        sent_msgs.append(msg)
                    else:
                        media_group = [InputMediaPhoto(media=pid, caption=f"🖼️ Ảnh preview: <b>{actual_name}</b>\n⏳ <i>Tự động xóa sau 60s</i>" if i == 0 else None, parse_mode="HTML") for i, pid in enumerate(photo_ids)]
                        msgs = await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
                        sent_msgs.extend(msgs)
                    
                    # Lấy danh sách Message ID vừa gửi và hẹn giờ thu hồi
                    msg_ids = [m.message_id for m in sent_msgs]
                    asyncio.create_task(delete_delayed(context.bot, query.message.chat_id, msg_ids, 60))
                
                except: pass
            else: await query.answer(get_text(lang, 'no_preview'), show_alert=True)
        else: await query.answer(get_text(lang, 'not_found'), show_alert=True)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handlers([
        CommandHandler("start", start), CommandHandler("run", run_command), CommandHandler("stop", stop_command),
        CommandHandler("theme", theme_command), CommandHandler("help", help_command), CommandHandler("langs", langs_command), CommandHandler("status", status_command),
        CallbackQueryHandler(button_callback), MessageHandler(filters.COMMAND | filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_admin_media)
    ])
    print("🤖 Bot đang chạy (Đã bật tính năng tự động xóa ảnh Preview sau 1 phút)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__': main()