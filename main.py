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

# --- BỘ LỌC TỰ ĐỘNG TIÊU HỦY KÝ TỰ ẨN (BOM) ---
if os.path.exists('.env'):
    try:
        with open('.env', 'r', encoding='utf-8-sig') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()
    except Exception as e:
        logger.error(f"Lỗi quét file .env: {e}")

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
GROUP_ID = int(os.getenv('GROUP_ID', 0))
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
GUIDE_VIDEO_ID = os.getenv('GUIDE_VIDEO_ID', '')
DONATE_IMAGE_ID = os.getenv('DONATE_IMAGE_ID', '') 
CHANNEL_URL = os.getenv('CHANNEL_URL', 'https://t.me/')
GROUP_URL = os.getenv('GROUP_URL', 'https://t.me/')

if not BOT_TOKEN: raise ValueError("Lỗi: Chưa cấu hình BOT_TOKEN trong file .env.")

BOT_ACTIVE = True 
BASE_FILES_DIR = "files"
DATABASE_FILE = os.path.join(BASE_FILES_DIR, "database.txt")
USERS_FILE = os.path.join(BASE_FILES_DIR, "users.txt")

os.makedirs(BASE_FILES_DIR, exist_ok=True)
if not os.path.exists(DATABASE_FILE): open(DATABASE_FILE, 'w', encoding='utf-8').close()
if not os.path.exists(USERS_FILE): open(USERS_FILE, 'w', encoding='utf-8').close()

def get_database() -> dict:
    db = {}
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and '|' in line:
                        name, rest = line.strip().split('=', 1)
                        parts = rest.split('|')
                        count = int(parts[4].strip()) if len(parts) > 4 and parts[4].strip().isdigit() else 0
                        db[name.strip()] = {'id': parts[0].strip(), 'pass': parts[1].strip() if len(parts) > 1 else "None", 'preview': parts[2].strip() if len(parts) > 2 else "None", 'date': parts[3].strip() if len(parts) > 3 else "Đang cập nhật", 'count': count}
        except Exception as e: logger.error(f"Lỗi đọc DB: {e}")
    return db

def save_database(db: dict):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        for name, info in db.items(): f.write(f"{name}={info['id']}|{info['pass']}|{info['preview']}|{info['date']}|{info['count']}\n")

def track_user(user_id: int):
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f: users = set(f.read().splitlines())
    if str(user_id) not in users:
        with open(USERS_FILE, 'a', encoding='utf-8') as f: f.write(f"{user_id}\n")

def get_user_count() -> int:
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f: return len(set([line.strip() for line in f if line.strip()]))
    except: return 0

async def delete_delayed(bot, chat_id, message_ids, delay):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try: await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except: pass

# --- TỪ ĐIỂN SONG NGỮ ĐÃ ĐƯỢC BỔ SUNG FULL 100% ---
LANG = {
    'en': {
        'join_req': "🔒 <b>Access Required</b>\nPlease join our Channel and Group below, then click <b>Verify</b>.",
        'btn_channel': "📢 Channel", 'btn_group': "💬 Group", 'btn_verify': "🔄 Verify Membership", 'verify_fail': "⚠️ Please join both and try again.",
        'main_menu': "⚡ <b>Main Menu</b>\nSelect an option below:", 'btn_themes': "🎨 Theme List", 'btn_top': "🔥 Top Trending",
        'btn_pass': "🔑 Passwords", 'btn_guide': "📖 Password Guide", 'btn_donate': "☕ Support", 'btn_support': "💬 Contact Admin", 'btn_back': "◀️ Back to Menu", 
        'no_themes': "📭 No themes available.", 'not_found': "❌ File not found.", 'no_guide_video': "⚠️ No guide video yet.",
        'guide_text': "📖 <b>How to use the password:</b>\nWatch the tutorial above to copy the password correctly.",
        'donate_text': "💖 <b>Thank you!</b>\n🏦 <b>Bank:</b> MB Bank\n💳 <b>Account:</b> <code>29992992699999</code>\n👤 <b>Name:</b> DO DANG TUAN KIET",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n📅 <b>Updated:</b> <code>{date}</code>\n🔑 <b>Pass:</b> <code>{pwd}</code>\n📈 <b>Downloads:</b> {count}\n\nSelect an action:",
        'btn_download': "📥 Download File", 'btn_view_preview': "🖼️ View Preview", 'no_preview': "⚠️ No preview image.",
        'bot_maintenance': "⚠️ Bot is currently under maintenance!",
        'old_menu': "⚠️ This menu is outdated. Please type /theme to open a new one!",
        'not_your_menu': "❌ This menu belongs to someone else. Type /theme to create yours!",
        'lang_updated': "✅ Language updated successfully!",
        'loading_file': "Loading file... (Auto-deletes in 3 mins) ⏳",
        'auto_del_file': "\n\n⏳ <i>File will be auto-deleted in 3 minutes for copyright protection. Save it now!</i>",
        'loading_photo': "Loading photo... (Auto-deletes in 60s) ⏳",
        'auto_del_photo': "\n⏳ <i>Auto-deletes in 60s</i>",
        'top_title': "🔥 <b>TOP 5 TRENDING THEMES:</b>\n\n",
        'top_downloads': "downloads"
    },
    'vi': {
        'join_req': "🔒 <b>Yêu cầu truy cập</b>\nVui lòng tham gia Kênh và Nhóm hỗ trợ bên dưới rồi nhấn <b>Xác nhận</b>.",
        'btn_channel': "📢 Kênh Thông Báo", 'btn_group': "💬 Nhóm Thảo Luận", 'btn_verify': "🔄 Xác Nhận Tham Gia", 'verify_fail': "⚠️ Bạn chưa tham gia đủ Kênh và Nhóm!",
        'main_menu': "⚡ <b>Menu Chính</b>\nVui lòng chọn chức năng:", 'btn_themes': "🎨 Kho Theme", 'btn_top': "🔥 Bảng Xếp Hạng",
        'btn_pass': "🔑 Mật Khẩu", 'btn_guide': "📖 Hướng Dẫn Pass", 'btn_donate': "☕ Ủng Hộ", 'btn_support': "💬 Liên Hệ Admin", 'btn_back': "◀️ Quay Lại", 
        'no_themes': "📭 Kho chưa có dữ liệu.", 'not_found': "❌ Không tìm thấy file.", 'no_guide_video': "⚠️ Chưa có video hướng dẫn.",
        'guide_text': "📖 <b>Hướng dẫn nhập mật khẩu:</b>\nXem kỹ video trên để copy và nhập pass không bị lỗi nhé!",
        'donate_text': "💖 <b>Cảm ơn bạn!</b>\n🏦 <b>Ngân hàng:</b> MB Bank\n💳 <b>STK:</b> <code>29992992699999</code>\n👤 <b>Tên:</b> DO DANG TUAN KIET",
        'theme_title': "🎨 <b>Theme:</b> <code>{name}</code>\n📅 <b>Cập nhật:</b> <code>{date}</code>\n🔑 <b>Pass:</b> <code>{pwd}</code>\n📈 <b>Lượt tải:</b> {count}\n\nBạn muốn làm gì:",
        'btn_download': "📥 Tải File Theme", 'btn_view_preview': "🖼️ Xem Ảnh Preview", 'no_preview': "⚠️ Chưa có ảnh preview.",
        'bot_maintenance': "⚠️ Bot đang bảo trì, vui lòng quay lại sau!",
        'old_menu': "⚠️ Menu này đã cũ (do Bot vừa khởi động lại). Vui lòng gõ /theme để mở menu mới!",
        'not_your_menu': "❌ Menu này do người khác gọi. Hãy gõ /theme để tự tạo riêng!",
        'lang_updated': "✅ Đã cập nhật cài đặt ngôn ngữ!",
        'loading_file': "Đang tải file... (Sẽ tự hủy sau 3 phút) ⏳",
        'auto_del_file': "\n\n⏳ <i>File sẽ tự động xóa sau 3 phút để bảo vệ bản quyền. Bạn hãy lưu ngay nhé!</i>",
        'loading_photo': "Đang tải ảnh... (Tự xóa sau 60s) ⏳",
        'auto_del_photo': "\n⏳ <i>Tự xóa sau 60s</i>",
        'top_title': "🔥 <b>TOP 5 THEME THỊNH HÀNH:</b>\n\n",
        'top_downloads': "tải"
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    text = LANG.get(lang, LANG['en']).get(key, f"Missing: {key}")
    return text.format(**kwargs) if kwargs else text

async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator'] or (member.status == 'restricted' and getattr(member, 'can_send_messages', False))
    except: return False

# --- QUẢN TRỊ VIÊN (Admin chỉ xài tiếng Việt nên không cần dịch) ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID or update.effective_chat.type != 'private': return
    help_text = "🛠 <b>HƯỚNG DẪN ADMIN:</b>\n\n1️⃣ <b>Thêm Theme:</b> Reply file với: <code>/add Tên Theme | Pass | Ngày</code>\n2️⃣ <b>Thêm ảnh:</b> Reply ảnh với: <code>/addpv Tên_Theme</code>\n3️⃣ <b>Sửa Theme:</b> <code>/edit Tên Theme | Pass mới | Ngày mới</code>\n4️⃣ <b>Xóa Theme:</b> <code>/del Tên_Theme</code>\n5️⃣ <b>Trạng thái:</b> /status\n6️⃣ <b>Gửi TB Hàng loạt:</b> Gõ hoặc Reply với <code>/broadcast Nội_dung</code>\n7️⃣ <b>Bật/Tắt Bot:</b> <code>/run</code> hoặc <code>/stop</code>\n8️⃣ <b>Ngôn ngữ:</b> /langs"
    await update.message.reply_text(help_text, parse_mode="HTML")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID or update.effective_chat.type != 'private': return
    db = get_database()
    stt = "Đang chạy 🟢" if BOT_ACTIVE else "Bảo trì 🔴"
    list_t = "".join([f"{i}. <code>{n}</code> (Tải: {v['count']})\n" for i, (n, v) in enumerate(db.items(), 1)]) if db else "<i>Trống</i>"
    await update.message.reply_text(f"📊 <b>TRẠNG THÁI</b>\n⚙️ <b>Bot:</b> {stt}\n👥 <b>User:</b> {get_user_count()}\n🎨 <b>Theme:</b> {len(db)}\n\n📋 <b>DANH SÁCH:</b>\n{list_t}", parse_mode="HTML")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global BOT_ACTIVE
    if update.effective_user.id == ADMIN_ID and update.effective_chat.type == 'private': BOT_ACTIVE = False; await update.message.reply_text("💤 <b>Hệ thống ĐÃ TẠM DỪNG!</b>")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global BOT_ACTIVE
    if update.effective_user.id == ADMIN_ID and update.effective_chat.type == 'private': BOT_ACTIVE = True; await update.message.reply_text("🚀 <b>Hệ thống HOẠT ĐỘNG TRỞ LẠI!</b>")

async def langs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id == ADMIN_ID and update.effective_chat.type in ['group', 'supergroup']:
        keyboard = [[InlineKeyboardButton("Việt Nam 🇻🇳", callback_data="setlang_vi")],[InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en")]]
        await update.message.reply_text("⚙️ <b>Cấu hình ngôn ngữ nhóm:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID or update.effective_chat.type != 'private': return
    target_msg = update.message.reply_to_message
    text = update.message.text.replace("/broadcast", "").strip()
    if not target_msg and not text: return await update.message.reply_text("❌ Hãy Reply một tin nhắn hoặc gõ: /broadcast [Nội dung]")
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f: users = set(f.read().splitlines())
    if not users: return await update.message.reply_text("📭 Chưa có user nào để gửi.")
    await update.message.reply_text(f"🚀 Bắt đầu phát sóng tới {len(users)} người...")
    success, fail = 0, 0
    for uid in users:
        try:
            if target_msg: await context.bot.copy_message(chat_id=uid, from_chat_id=update.effective_chat.id, message_id=target_msg.message_id)
            else: await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05) 
        except: fail += 1
    await update.message.reply_text(f"✅ <b>BROADCAST HOÀN TẤT</b>\n- Thành công: {success}\n- Thất bại: {fail}", parse_mode="HTML")

async def handle_admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID or update.effective_chat.type != 'private': return
    text = (update.message.text or update.message.caption or "").strip()
    target_msg = update.message.reply_to_message if update.message.reply_to_message else update.message

    if text.startswith("/del"):
        name = text.replace("/del", "").strip()
        db = get_database()
        if name in db: del db[name]; save_database(db); await update.message.reply_text(f"🗑️ Đã xóa: {name}")
        else: await update.message.reply_text("❌ Không tìm thấy theme.")
    elif text.startswith("/edit"):
        try:
            parts = text.replace("/edit", "").strip().split('|')
            name = parts[0].strip()
            db = get_database()
            if name in db:
                db[name]['id'] = target_msg.document.file_id if (target_msg and target_msg.document) else db[name]['id']
                db[name]['pass'] = parts[1].strip() if len(parts)>1 and parts[1].strip() else db[name]['pass']
                db[name]['date'] = parts[2].strip() if len(parts)>2 and parts[2].strip() else db[name]['date']
                save_database(db); await update.message.reply_text(f"📝 Đã sửa: {name}")
            else: await update.message.reply_text("❌ Không tìm thấy theme.")
        except Exception as e: await update.message.reply_text(f"❌ Lỗi: {e}")
    elif text.startswith("/addpv"):
        if not target_msg.photo: return await update.message.reply_text("❌ Reply ảnh!")
        name = text.replace("/addpv", "").strip()
        db = get_database()
        if name in db:
            old_pv = db[name]['preview']
            db[name]['preview'] = target_msg.photo[-1].file_id if old_pv.lower() == 'none' else f"{old_pv},{target_msg.photo[-1].file_id}"
            save_database(db); await update.message.reply_text(f"🖼️ Đã thêm ảnh cho: {name}")
        else: await update.message.reply_text("❌ Không tìm thấy theme.")
    elif text.startswith("/add"):
        if not target_msg.document: return await update.message.reply_text("❌ Reply file!")
        try:
            parts = text.replace("/add", "").strip().split('|')
            name = parts[0].strip()
            db = get_database()
            db[name] = {'id': target_msg.document.file_id, 'pass': parts[1].strip() if len(parts)>1 else "None", 'preview': 'None', 'date': parts[2].strip() if len(parts)>2 else "Đang cập nhật", 'count': 0}
            save_database(db); await update.message.reply_text(f"✅ Đã thêm: {name}")
        except: await update.message.reply_text("❌ Sai cú pháp.")
    elif not text.startswith("/"):
        if update.message.document: await update.message.reply_text(f"✅ <b>File ID:</b>\n<code>{update.message.document.file_id}</code>", parse_mode="HTML")
        elif update.message.photo: await update.message.reply_text(f"✅ <b>Photo ID:</b>\n<code>{update.message.photo[-1].file_id}</code>", parse_mode="HTML")
        elif update.message.video: await update.message.reply_text(f"✅ <b>Video ID:</b>\n<code>{update.message.video.file_id}</code>", parse_mode="HTML")

# --- LUỒNG USER ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type in ['group', 'supergroup']: return 
    if not BOT_ACTIVE and update.effective_user.id != ADMIN_ID: return 
    track_user(update.effective_user.id)
    keyboard = [[InlineKeyboardButton("💡 Tiếng Việt 🇻🇳", callback_data="lang_vi"), InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")]]
    await update.effective_message.reply_text("Chọn ngôn ngữ / Select language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not BOT_ACTIVE and update.effective_user.id != ADMIN_ID: return
    user = update.effective_user
    chat_type = update.effective_chat.type
    track_user(user.id)
    lang = context.user_data.get('lang')
    if not lang:
        keyboard = [[InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi"), InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")]]
        sent_msg = await update.message.reply_text(f"Hi {user.mention_html()}! 👋\nChọn ngôn ngữ / Select language:", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        if chat_type in ['group', 'supergroup']: context.bot_data[f"owner_{sent_msg.message_id}"] = user.id
        return

    is_member = await check_membership(context, user.id, CHANNEL_ID) and await check_membership(context, user.id, GROUP_ID)
    if not is_member:
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL), InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)], [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'join_req')}"
    else:
        support = f"https://t.me/{ADMIN_USERNAME}" if ADMIN_USERNAME else f"tg://user?id={ADMIN_ID}"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_themes'), callback_data="mode_themes"), InlineKeyboardButton(get_text(lang, 'btn_top'), callback_data="mode_top")],[InlineKeyboardButton(get_text(lang, 'btn_pass'), callback_data="mode_password")],[InlineKeyboardButton(get_text(lang, 'btn_guide'), callback_data="mode_guide")],[InlineKeyboardButton(get_text(lang, 'btn_donate'), callback_data="mode_donate"), InlineKeyboardButton(get_text(lang, 'btn_support'), url=support)]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'main_menu')}"
        
    sent_msg = await update.message.reply_text(msg_text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    if chat_type in ['group', 'supergroup']: context.bot_data[f"owner_{sent_msg.message_id}"] = user.id

async def check_and_show_menu(query, context, lang, show_alert=False):
    user = query.from_user
    chat_type = query.message.chat.type
    is_member = await check_membership(context, user.id, CHANNEL_ID) and await check_membership(context, user.id, GROUP_ID)
    if not is_member:
        if show_alert: await query.answer(get_text(lang, 'verify_fail'), show_alert=True)
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_channel'), url=CHANNEL_URL), InlineKeyboardButton(get_text(lang, 'btn_group'), url=GROUP_URL)], [InlineKeyboardButton(get_text(lang, 'btn_verify'), callback_data="verify_join")]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'join_req')}"
    else:
        support = f"https://t.me/{ADMIN_USERNAME}" if ADMIN_USERNAME else f"tg://user?id={ADMIN_ID}"
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_themes'), callback_data="mode_themes"), InlineKeyboardButton(get_text(lang, 'btn_top'), callback_data="mode_top")],[InlineKeyboardButton(get_text(lang, 'btn_pass'), callback_data="mode_password")],[InlineKeyboardButton(get_text(lang, 'btn_guide'), callback_data="mode_guide")],[InlineKeyboardButton(get_text(lang, 'btn_donate'), callback_data="mode_donate"), InlineKeyboardButton(get_text(lang, 'btn_support'), url=support)]]
        msg_text = f"Hi {user.mention_html()}! 👋\n{get_text(lang, 'main_menu')}"
    try:
        if query.message.video or query.message.photo or query.message.document:
            await query.message.delete()
            sent_msg = await context.bot.send_message(chat_id=query.message.chat_id, text=msg_text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            if chat_type in ['group', 'supergroup']: context.bot_data[f"owner_{sent_msg.message_id}"] = user.id
        else: await query.edit_message_text(text=msg_text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    except: pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    chat_type = query.message.chat.type
    
    # 1. LẤY NGÔN NGỮ TRƯỚC ĐỂ DỊCH POP-UP LỖI
    lang = context.user_data.get('lang')
    if not lang and not data.startswith("lang_"): lang = context.chat_data.get('lang', 'vi')
    if not lang: lang = 'vi' # Mặc định an toàn

    if not BOT_ACTIVE and user_id != ADMIN_ID: return await query.answer(get_text(lang, 'bot_maintenance'), show_alert=True)

    if chat_type in ['group', 'supergroup']:
        owner_id = context.bot_data.get(f"owner_{query.message.message_id}")
        if not owner_id: return await query.answer(get_text(lang, 'old_menu'), show_alert=True)
        if user_id != owner_id and user_id != ADMIN_ID: return await query.answer(get_text(lang, 'not_your_menu'), show_alert=True)

    if data.startswith("setlang_"):
        if user_id != ADMIN_ID: return
        context.chat_data['lang'] = data.split('_')[1]
        await query.answer(get_text(context.chat_data['lang'], 'lang_updated'), show_alert=True)
        await query.message.delete()
        return

    if data.startswith("lang_"):
        lang = data.split('_')[1]
        context.user_data['lang'] = lang
        await query.answer()
        return await check_and_show_menu(query, context, lang)

    if data in ["verify_join", "mode_start"]:
        if data == "mode_start": await query.answer()
        return await check_and_show_menu(query, context, lang, show_alert=(data=="verify_join"))

    elif data == "mode_guide":
        if GUIDE_VIDEO_ID:
            await query.answer()
            try:
                await query.message.delete()
                msg = await context.bot.send_video(chat_id=query.message.chat_id, video=GUIDE_VIDEO_ID, caption=get_text(lang, 'guide_text'), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]))
                if chat_type in ['group', 'supergroup']: context.bot_data[f"owner_{msg.message_id}"] = user_id
            except: pass
        else: await query.answer(get_text(lang, 'no_guide_video'), show_alert=True)

    elif data == "mode_donate":
        await query.answer()
        keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]
        if DONATE_IMAGE_ID:
            try:
                await query.message.delete()
                msg = await context.bot.send_photo(chat_id=query.message.chat_id, photo=DONATE_IMAGE_ID, caption=get_text(lang, 'donate_text'), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
                if chat_type in ['group', 'supergroup']: context.bot_data[f"owner_{msg.message_id}"] = user_id
            except: pass
        else: await query.edit_message_text(get_text(lang, 'donate_text'), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "mode_password":
        await query.answer()
        db = get_database() 
        msg = "🔑 <b>Danh sách mật khẩu / Password List:</b>\n\n" if db else get_text(lang, 'no_themes')
        for name, info in db.items(): msg += f"🔸 <b>{name}:</b> <code>{info['pass']}</code>\n"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]), parse_mode="HTML")

    elif data == "mode_themes":
        await query.answer()
        db = get_database() 
        if not db: return await query.edit_message_text(get_text(lang, 'no_themes'), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]))
        keyboard = [[InlineKeyboardButton(f"🎨 {name}", callback_data=f"sel_{name[:40]}")] for name in db.keys()]
        keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")])
        await query.edit_message_text(f"📁 <b>{get_text(lang, 'btn_themes')}</b>:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "mode_top":
        await query.answer()
        db = get_database()
        if not db: return await query.edit_message_text(get_text(lang, 'no_themes'), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")]]))
        
        sorted_themes = sorted(db.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        msg = get_text(lang, 'top_title')
        keyboard = []
        for i, (name, info) in enumerate(sorted_themes, 1):
            msg += f"{i}. <b>{name}</b> - <i>{info['count']} {get_text(lang, 'top_downloads')}</i>\n"
            keyboard.append([InlineKeyboardButton(f"🎨 {name}", callback_data=f"sel_{name[:40]}")])
        keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_start")])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("sel_"):
        await query.answer()
        short_name = data.split('sel_', 1)[1]
        db = get_database() 
        name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if name:
            keyboard = [[InlineKeyboardButton(get_text(lang, 'btn_download'), callback_data=f"dl_{short_name}")],[InlineKeyboardButton(get_text(lang, 'btn_view_preview'), callback_data=f"pv_{short_name}")],[InlineKeyboardButton(get_text(lang, 'btn_back'), callback_data="mode_themes")]]
            await query.edit_message_text(get_text(lang, 'theme_title', name=name, pwd=db[name]['pass'], date=db[name]['date'], count=db[name]['count']), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else: await query.answer(get_text(lang, 'not_found'), show_alert=True)

    elif data.startswith("dl_"):
        short_name = data.split('dl_', 1)[1]
        db = get_database() 
        name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if name:
            await query.answer(get_text(lang, 'loading_file'))
            try:
                db[name]['count'] += 1
                save_database(db)
                msg = await query.message.reply_document(document=db[name]['id'], caption=f"🎨 <b>{name}</b>\n🔑 Pass: <code>{db[name]['pass']}</code>{get_text(lang, 'auto_del_file')}", parse_mode="HTML")
                asyncio.create_task(delete_delayed(context.bot, query.message.chat_id, [msg.message_id], 180))
            except: pass
        else: await query.answer(get_text(lang, 'not_found'), show_alert=True)

    elif data.startswith("pv_"):
        short_name = data.split('pv_', 1)[1]
        db = get_database() 
        name = next((n for n in db.keys() if n.startswith(short_name)), None)
        if name:
            pv = db[name]['preview']
            if pv and pv.lower() != 'none':
                await query.answer(get_text(lang, 'loading_photo'))
                try:
                    p_ids = [p.strip() for p in pv.split(',')]
                    s_msgs = []
                    if len(p_ids) == 1: 
                        msg = await query.message.reply_photo(photo=p_ids[0], caption=f"🖼️ <b>{name}</b>{get_text(lang, 'auto_del_photo')}", parse_mode="HTML")
                        s_msgs.append(msg)
                    else:
                        m_grp = [InputMediaPhoto(media=p, caption=f"🖼️ <b>{name}</b>{get_text(lang, 'auto_del_photo')}" if i==0 else None, parse_mode="HTML") for i, p in enumerate(p_ids)]
                        msgs = await context.bot.send_media_group(chat_id=query.message.chat_id, media=m_grp)
                        s_msgs.extend(msgs)
                    asyncio.create_task(delete_delayed(context.bot, query.message.chat_id, [m.message_id for m in s_msgs], 60))
                except: pass
            else: await query.answer(get_text(lang, 'no_preview'), show_alert=True)
        else: await query.answer(get_text(lang, 'not_found'), show_alert=True)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handlers([
        CommandHandler("start", start), CommandHandler("run", run_command), CommandHandler("stop", stop_command),
        CommandHandler("theme", theme_command), CommandHandler("help", help_command), CommandHandler("langs", langs_command), 
        CommandHandler("status", status_command), CommandHandler("broadcast", broadcast_command),
        CallbackQueryHandler(button_callback), MessageHandler(filters.COMMAND | filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_admin_media)
    ])
    print("🤖 Bot đang chạy (Đã hoàn thiện Đa Ngôn Ngữ 100% cho mọi thông báo)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__': main()