import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode, ContentType
from aiogram.client.default import DefaultBotProperties

# ========== SOZLASH ==========
BOT_TOKEN = "8513886696:AAEeA8SRojZYvDpWrDju06UiSm1vCzrH-mM"
ADMIN_ID = 7063084503

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== DATABASE ==========
DB_FILE = "chat_bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            age INTEGER,
            gender TEXT,
            interests TEXT,
            status TEXT DEFAULT 'idle',
            is_banned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # is_banned ustunini qo'shish (agar yo'q bo'lsa)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    # Suhbatlar jadvali (ended_at ustunisiz)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ended_at ustunini o'chirish (agar mavjud bo'lsa)
    try:
        cursor.execute("ALTER TABLE chats DROP COLUMN ended_at")
    except sqlite3.OperationalError:
        pass
    
    # Admin uchun statistik jadvallar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_users INTEGER DEFAULT 0,
            total_chats INTEGER DEFAULT 0,
            active_users INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database yaratildi!")

# ========== YORDAMCHI FUNKSIYALAR ==========
def is_admin(user_id):
    return user_id == ADMIN_ID

def get_user_info(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_stats():
    """Statistikani yangilash"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM chats')
        total_chats = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status != "idle"')
        active_users = cursor.fetchone()[0]
        
        cursor.execute('DELETE FROM admin_stats')
        cursor.execute('''
            INSERT INTO admin_stats (total_users, total_chats, active_users)
            VALUES (?, ?, ?)
        ''', (total_users, total_chats, active_users))
        
        conn.commit()
        conn.close()
    except:
        pass

# ========== FSM ==========
class ProfileStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_interests = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_broadcast = State()

# ========== START ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "👑 <b>Admin panelga xush kelibsiz!</b>\n\n"
            "<b>Admin buyruqlari:</b>\n"
            "/admin - 🛠️ Admin panel\n"
            "/stats - 📊 Statistika\n"
            "/users - 👥 Foydalanuvchilar ro'yxati\n"
            "/finduser - 🔍 Foydalanuvchi qidirish\n"
            "/ban - 🚫 Foydalanuvchini bloklash\n"
            "/unban - ✅ Blokdan chiqarish\n"
            "/broadcast - 📢 Hammaga xabar yuborish\n\n"
            "<b>Oddiy buyruqlar:</b>\n"
            "/find - Suhbatdosh qidirish\n"
            "/profile - Profil sozlash"
        )
    else:
        await message.answer(
            "👋 <b>Anonim Suhbat Botiga xush kelibsiz!</b>\n\n"
            "📋 <b>Komandalar:</b>\n"
            "/find - 🔍 Suhbatdosh qidirish\n"
            "/stop - 🛑 Suhbatni tugatish\n"
            "/next - ⏭️ Keyingi suhbatdosh\n"
            "/profile - 👤 Profil sozlash\n"
            "/help - ❓ Yordam\n\n"
            "📸 <b>Qo'llab-quvvatlanadigan formatlar:</b>\n"
            "• 📝 Matn\n"
            "• 🖼️ Rasm\n"
            "• 🎞️ Video\n"
            "• 🎵 Ovozli xabar\n"
            "• 😊 Stiker\n\n"
            "⚡ <b>Tezkor boshlash:</b> /find"
        )

# ========== HELP ==========
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "🆘 <b>Admin Yordam</b>\n\n"
            "1. /admin - Admin panelni ochish\n"
            "2. /stats - To'liq statistika\n"
            "3. /users - Foydalanuvchilar ro'yxati\n"
            "4. /finduser [ID] - Foydalanuvchini qidirish\n"
            "5. /ban [ID] - Foydalanuvchini bloklash\n"
            "6. /unban [ID] - Blokdan chiqarish\n"
            "7. /broadcast - Hammaga xabar yuborish\n\n"
            "⚠️ <b>Foydalanuvchi uchun:</b> /find, /profile, /stop, /next"
        )
    else:
        await message.answer(
            "🆘 <b>Yordam</b>\n\n"
            "1. Avval /profile bilan profil to'ldiring\n"
            "2. Keyin /find bilan suhbatdosh qidiring\n"
            "3. Har qanday xabar yuboring - suhbatdoshingizga boradi\n"
            "4. /stop - suhbatni tugatish\n"
            "5. /next - yangi suhbatdosh\n\n"
            "📸 <b>Qo'llab-quvvatlanadigan formatlar:</b>\n"
            "• 📝 Matn xabarlar\n"
            "• 🖼️ Rasm (rasm sarlavhasi bilan)\n"
            "• 🎞️ Video (video sarlavhasi bilan)\n"
            "• 🎵 Ovozli xabar (ovozli xabar sarlavhasi bilan)\n"
            "• 😊 Stikerlar\n\n"
            "⚠️ <b>Eslatma:</b> Barcha suhbatlar anonim!"
        )

# ========== PROFILE ==========
@dp.message(Command("profile"))
async def cmd_profile(message: types.Message, state: FSMContext):
    # Bloklanganligini tekshirish
    user = get_user_info(message.from_user.id)
    if user and len(user) > 8 and user[8] == 1:
        await message.answer("🚫 Siz bloklangansiz! Admin bilan bog'laning.")
        return
    
    await state.set_state(ProfileStates.waiting_for_age)
    await message.answer("🎂 <b>Yoshingizni kiriting:</b>\nMasalan: 25")

@dp.message(ProfileStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Yosh raqam bo'lishi kerak!")
        return
    
    age = int(message.text)
    if age < 13 or age > 100:
        await message.answer("❌ Yosh 13-100 oralig'ida bo'lishi kerak!")
        return
    
    await state.update_data(age=age)
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Erkak"), types.KeyboardButton(text="Ayol")]
        ],
        resize_keyboard=True
    )
    
    await state.set_state(ProfileStates.waiting_for_gender)
    await message.answer("⚧️ <b>Jinsingizni tanlang:</b>", reply_markup=keyboard)

@dp.message(ProfileStates.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    if message.text not in ["Erkak", "Ayol"]:
        await message.answer("❌ 'Erkak' yoki 'Ayol' ni tanlang!")
        return
    
    await state.update_data(gender=message.text)
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Musiqa"), types.KeyboardButton(text="Sport")],
            [types.KeyboardButton(text="Kino"), types.KeyboardButton(text="Kitob")],
            [types.KeyboardButton(text="O'yin"), types.KeyboardButton(text="Barchasi")]
        ],
        resize_keyboard=True
    )
    
    await state.set_state(ProfileStates.waiting_for_interests)
    await message.answer("🎯 <b>Qiziqishlaringizni tanlang:</b>", reply_markup=keyboard)

@dp.message(ProfileStates.waiting_for_interests)
async def process_interests(message: types.Message, state: FSMContext):
    interests = message.text
    data = await state.get_data()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (telegram_id, username, full_name, age, gender, interests)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        data['age'],
        data['gender'],
        interests
    ))
    
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer(
        f"✅ <b>Profil saqlandi!</b>\n\n"
        f"🎂 Yosh: {data['age']}\n"
        f"⚧️ Jins: {data['gender']}\n"
        f"🎯 Qiziqishlar: {interests}\n\n"
        f"🔍 Suhbat boshlash: /find",
        reply_markup=types.ReplyKeyboardRemove()
    )

# ========== FIND PARTNER ==========
@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    user_id = message.from_user.id
    
    # Bloklanganligini tekshirish
    user = get_user_info(user_id)
    if user and len(user) > 8 and user[8] == 1:
        await message.answer("🚫 Siz bloklangansiz! Admin bilan bog'laning.")
        return
    
    # Database dan foydalanuvchini tekshirish
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        await message.answer("❌ Avval profilingizni to'ldiring: /profile")
        return
    
    # Aktiv suhbatni tekshirish
    cursor.execute('''
        SELECT * FROM chats 
        WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
    ''', (user_id, user_id))
    
    active_chat = cursor.fetchone()
    
    if active_chat:
        conn.close()
        await message.answer("⚠️ Sizda aktiv suhbat bor! /stop bilan tugating.")
        return
    
    # Statusni qidiruv holatiga o'zgartirish
    cursor.execute('UPDATE users SET status = "searching" WHERE telegram_id = ?', (user_id,))
    conn.commit()
    
    await message.answer("🔍 <b>Suhbatdosh qidirilmoqda...</b>")
    
    # Suhbatdosh qidirish (bloklanganlarni o'tkazib yuborish)
    cursor.execute('''
        SELECT * FROM users 
        WHERE telegram_id != ? 
        AND status = 'searching'
        AND (is_banned = 0 OR is_banned IS NULL)
        LIMIT 1
    ''', (user_id,))
    
    partner = cursor.fetchone()
    
    if partner:
        partner_id = partner[1]
        
        # Chat yaratish
        cursor.execute('''
            INSERT INTO chats (user1_id, user2_id, status)
            VALUES (?, ?, 'active')
        ''', (user_id, partner_id))
        
        # Statuslarni yangilash
        cursor.execute('UPDATE users SET status = "in_chat" WHERE telegram_id IN (?, ?)', 
                      (user_id, partner_id))
        
        conn.commit()
        
        await message.answer(
            f"✅ <b>Suhbatdosh topildi!</b>\n\n"
            f"💬 Endi suhbatni boshlashingiz mumkin!\n"
            f"🛑 Tugatish: /stop\n"
            f"⏭️ Yangisi: /next"
        )
        
        # Suhbatdoshga xabar
        try:
            await bot.send_message(
                partner_id,
                f"✅ <b>Suhbatdosh topildi!</b>\n\n"
                f"💬 Endi suhbatni boshlashingiz mumkin!\n"
                f"🛑 Tugatish: /stop\n"
                f"⏭️ Yangisi: /next"
            )
        except:
            pass
        
    else:
        await message.answer("⏳ Suhbatdosh topilmadi. Birozdan keyin qayta urinib ko'ring.")
    
    conn.close()

# ========== STOP ==========
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Aktiv suhbatni topish
    cursor.execute('''
        SELECT * FROM chats 
        WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
    ''', (user_id, user_id))
    
    chat = cursor.fetchone()
    
    if not chat:
        # Agar aktiv suhbat bo'lmasa, lekin status searching bo'lsa
        cursor.execute('SELECT status FROM users WHERE telegram_id = ?', (user_id,))
        user_status = cursor.fetchone()
        
        if user_status and user_status[0] == "searching":
            cursor.execute('UPDATE users SET status = "idle" WHERE telegram_id = ?', (user_id,))
            conn.commit()
            conn.close()
            await message.answer("🔍 <b>Suhbatdosh qidirish to'xtatildi.</b>\n\n/find bilan qayta boshlashingiz mumkin.")
            return
            
        conn.close()
        await message.answer("ℹ️ Sizda aktiv suhbat yo'q.")
        return
    
    # Faqat kerakli 5 ta qiymatni olish
    chat_id = chat[0]
    user1_id = chat[1]
    user2_id = chat[2]
    status = chat[3]
    started_at = chat[4] if len(chat) > 4 else ""
    
    # Suhbatdoshni aniqlash
    partner_id = user2_id if user1_id == user_id else user1_id
    
    # Suhbatni tugatish
    cursor.execute('UPDATE chats SET status = "ended" WHERE id = ?', (chat_id,))
    
    # Statuslarni yangilash
    cursor.execute('UPDATE users SET status = "idle" WHERE telegram_id IN (?, ?)', 
                  (user_id, partner_id))
    
    conn.commit()
    conn.close()
    
    # Suhbatdoshga xabar
    try:
        await bot.send_message(
            partner_id,
            "ℹ️ <b>Suhbatdosh suhbatni tugatdi.</b>\n"
            "Yangi suhbat: /find"
        )
    except:
        pass
    
    await message.answer("🛑 <b>Suhbat tugatildi.</b>\nYangi suhbat uchun /find buyrug'ini bering")

# ========== NEXT ==========
@dp.message(Command("next"))
async def cmd_next(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Aktiv suhbatni topish
    cursor.execute('''
        SELECT * FROM chats 
        WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
    ''', (user_id, user_id))
    
    chat = cursor.fetchone()
    
    if chat:
        # Faqat kerakli 5 ta qiymatni olish
        chat_id = chat[0]
        user1_id = chat[1]
        user2_id = chat[2]
        
        # Suhbatdoshni aniqlash
        partner_id = user2_id if user1_id == user_id else user1_id
        
        # Suhbatni tugatish
        cursor.execute('UPDATE chats SET status = "ended" WHERE id = ?', (chat_id,))
        
        # Statuslarni yangilash
        cursor.execute('UPDATE users SET status = "idle" WHERE telegram_id IN (?, ?)', 
                      (user_id, partner_id))
        
        # Suhbatdoshga xabar
        try:
            await bot.send_message(
                partner_id,
                "ℹ️ <b>Suhbatdosh yangi suhbatdosha o'tdi.</b>\n"
                "Yangi suhbat: /find"
            )
        except:
            pass
    
    # Statusni qidiruv holatiga o'zgartirish
    cursor.execute('UPDATE users SET status = "searching" WHERE telegram_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    await message.answer("⏭️ <b>Yangi suhbatdosh qidirilmoqda...</b>")
    
    # Suhbatdosh qidirish
    await cmd_find(message)

# ========== ADMIN COMMANDS ==========
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [types.InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
        [types.InlineKeyboardButton(text="🚫 Bloklash", callback_data="admin_ban")],
        [types.InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data="admin_unban")],
        [types.InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")]
    ])
    
    await message.answer("👑 <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:", reply_markup=keyboard)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Umumiy statistika
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE status = "in_chat"')
    in_chat = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE status = "searching"')
    searching = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
    banned = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM chats')
    total_chats = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM chats WHERE status = "active"')
    active_chats = cursor.fetchone()[0]
    
    # Bugungi statistikalar
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(created_at) = ?', (today,))
    today_users = cursor.fetchone()[0]
    
    conn.close()
    
    # Statistikani yangilash
    update_stats()
    
    stats_text = f"""
📊 <b>Bot Statistikalari</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: {total_users}
├ Suhbatda: {in_chat}
├ Qidiryapti: {searching}
├ Bloklangan: {banned}
└ Bugun qo'shildi: {today_users}

💬 <b>Suhbatlar:</b>
├ Jami: {total_chats}
└ Faol: {active_chats}

⏰ <b>Oxirgi yangilanish:</b> {datetime.now().strftime('%H:%M:%S')}
"""
    
    await message.answer(stats_text)

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT telegram_id, username, full_name, status, is_banned, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 20
    ''')
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await message.answer("📭 Hozircha foydalanuvchilar yo'q.")
        return
    
    text = "👥 <b>Oxirgi 20 foydalanuvchi:</b>\n\n"
    for user in users:
        user_id, username, full_name, status, is_banned, created_at = user
        name = f"@{username}" if username else full_name
        ban_status = "🚫" if is_banned == 1 else "✅"
        text += f"{ban_status} <b>{name}</b>\nID: {user_id}\nHolat: {status}\nQo'shilgan: {created_at[:10]}\n\n"
    
    await message.answer(text)

@dp.message(Command("finduser"))
async def cmd_finduser(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("ℹ️ <b>Foydalanish:</b> /finduser [ID yoki username]\n\nMasalan: /finduser 123456789")
        return
    
    search_term = args[1].strip()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if search_term.startswith('@'):
        cursor.execute('SELECT * FROM users WHERE username = ?', (search_term[1:],))
    elif search_term.isdigit():
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (int(search_term),))
    else:
        cursor.execute('SELECT * FROM users WHERE full_name LIKE ? LIMIT 5', (f'%{search_term}%',))
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    
    text = "🔍 <b>Qidiruv natijalari:</b>\n\n"
    for user in users[:5]:
        user_id = user[1]
        username = user[2]
        full_name = user[3]
        age = user[4]
        gender = user[5]
        status = user[7]
        is_banned = user[8] if len(user) > 8 else 0
        created_at = user[9] if len(user) > 9 else ""
        
        name = f"@{username}" if username else full_name
        ban_status = "🚫 Bloklangan" if is_banned == 1 else "✅ Faol"
        
        text += f"👤 <b>{name}</b>\n"
        text += f"🆔 ID: {user_id}\n"
        if age:
            text += f"🎂 Yosh: {age}\n"
        if gender:
            text += f"⚧️ Jins: {gender}\n"
        text += f"📊 Holat: {status}\n"
        text += f"🔒 {ban_status}\n"
        if created_at:
            text += f"📅 Qo'shilgan: {created_at[:10]}\n"
        text += "\n"
    
    await message.answer(text)

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("ℹ️ <b>Foydalanish:</b> /ban [foydalanuvchi ID]\n\nMasalan: /ban 123456789")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Foydalanuvchini topish
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (target_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    
    # Bloklash
    cursor.execute('UPDATE users SET is_banned = 1, status = "idle" WHERE telegram_id = ?', (target_id,))
    
    # Agar suhbatda bo'lsa, uni tugatish
    cursor.execute('SELECT * FROM chats WHERE (user1_id = ? OR user2_id = ?) AND status = "active"', (target_id, target_id))
    active_chat = cursor.fetchone()
    if active_chat:
        chat_id = active_chat[0]
        user1_id = active_chat[1]
        user2_id = active_chat[2]
        partner_id = user2_id if user1_id == target_id else user1_id
        cursor.execute('UPDATE chats SET status = "ended" WHERE id = ?', (chat_id,))
        cursor.execute('UPDATE users SET status = "idle" WHERE telegram_id = ?', (partner_id,))
    
    conn.commit()
    conn.close()
    
    # Foydalanuvchiga xabar
    try:
        await bot.send_message(target_id, "🚫 <b>Siz bloklangansiz!</b>\n\nAdmin bilan bog'laning.")
    except:
        pass
    
    username = user[2] if user[2] else user[3]
    await message.answer(f"✅ Foydalanuvchi <b>{username}</b> (ID: {target_id}) bloklandi.")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("ℹ️ <b>Foydalanish:</b> /unban [foydalanuvchi ID]\n\nMasalan: /unban 123456789")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (target_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    
    # Blokdan chiqarish
    cursor.execute('UPDATE users SET is_banned = 0 WHERE telegram_id = ?', (target_id,))
    conn.commit()
    conn.close()
    
    username = user[2] if user[2] else user[3]
    await message.answer(f"✅ Foydalanuvchi <b>{username}</b> (ID: {target_id}) blokdan chiqarildi.")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_for_broadcast)
    await message.answer("📢 <b>Broadcast xabarini yuboring:</b>\n\nMatn, rasm, video yoki ovozli xabar yuborishingiz mumkin.")

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT telegram_id FROM users WHERE is_banned = 0')
    users = cursor.fetchall()
    conn.close()
    
    sent = 0
    failed = 0
    
    await message.answer(f"📤 {len(users)} ta foydalanuvchiga xabar yuborilmoqda...")
    
    for user in users:
        user_id = user[0]
        try:
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.voice:
                await bot.send_voice(user_id, message.voice.file_id)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await state.clear()
    await message.answer(f"✅ <b>Broadcast yakunlandi!</b>\n\n✅ Yuborildi: {sent}\n❌ Yuborilmadi: {failed}")

# ========== CALLBACK QUERIES ==========
@dp.callback_query(F.data.startswith("admin_"))
async def handle_admin_callback(query: types.CallbackQuery):
    if not is_admin(query.from_user.id):
        await query.answer("Siz admin emassiz!")
        return
    
    action = query.data
    
    if action == "admin_stats":
        await cmd_stats(query.message)
    elif action == "admin_users":
        await cmd_users(query.message)
    elif action == "admin_ban":
        await query.message.answer("ℹ️ <b>Foydalanish:</b> /ban [foydalanuvchi ID]\n\nMasalan: /ban 123456789")
    elif action == "admin_unban":
        await query.message.answer("ℹ️ <b>Foydalanish:</b> /unban [foydalanuvchi ID]\n\nMasalan: /unban 123456789")
    elif action == "admin_broadcast":
        await cmd_broadcast(query.message, FSMContext(dispatcher=dp, storage=storage))
    
    await query.answer()

# ========== MESSAGE HANDLERS ==========
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    
    # Bloklanganlikni tekshirish
    user = get_user_info(user_id)
    if user and len(user) > 8 and user[8] == 1:
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM chats 
        WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
    ''', (user_id, user_id))
    
    chat = cursor.fetchone()
    conn.close()
    
    if not chat:
        await message.answer("ℹ️ Suhbat boshlash uchun: /find")
        return
    
    # Faqat kerakli 5 ta qiymatni olish
    chat_id = chat[0]
    user1_id = chat[1]
    user2_id = chat[2]
    status = chat[3]
    started_at = chat[4] if len(chat) > 4 else ""
    
    partner_id = user2_id if user1_id == user_id else user1_id
    
    # Xabarni yuborish
    try:
        await bot.send_message(
            partner_id,
            f"👤: {message.text}\n\n🛑 /stop | ⏭️ /next"
        )
    except:
        await message.answer("❌ Xabar yuborishda xatolik. Yangi suhbat: /find")

# ========== MEDIA HANDLERS ==========
@dp.message(F.photo)
async def handle_photo_message(message: types.Message):
    await forward_media(message, 'photo')

@dp.message(F.video)
async def handle_video_message(message: types.Message):
    await forward_media(message, 'video')

@dp.message(F.voice)
async def handle_voice_message(message: types.Message):
    await forward_media(message, 'voice')

@dp.message(F.sticker)
async def handle_sticker_message(message: types.Message):
    await forward_media(message, 'sticker')

@dp.message(F.document)
async def handle_document_message(message: types.Message):
    await forward_media(message, 'document')

async def forward_media(message: types.Message, media_type: str):
    user_id = message.from_user.id
    
    # Bloklanganlikni tekshirish
    user = get_user_info(user_id)
    if user and len(user) > 8 and user[8] == 1:
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM chats 
        WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
    ''', (user_id, user_id))
    
    chat = cursor.fetchone()
    conn.close()
    
    if not chat:
        await message.answer("ℹ️ Suhbat boshlash uchun: /find")
        return
    
    # Faqat kerakli 5 ta qiymatni olish
    user1_id = chat[1]
    user2_id = chat[2]
    
    partner_id = user2_id if user1_id == user_id else user1_id
    
    try:
        if media_type == 'photo':
            caption = message.caption if message.caption else ""
            await bot.send_photo(
                partner_id,
                photo=message.photo[-1].file_id,
                caption=f"{caption}\n\n👤: [Rasm]\n\n🛑 /stop | ⏭️ /next" if caption else f"👤: [Rasm]\n\n🛑 /stop | ⏭️ /next"
            )
        elif media_type == 'video':
            caption = message.caption if message.caption else ""
            await bot.send_video(
                partner_id,
                video=message.video.file_id,
                caption=f"{caption}\n\n👤: [Video]\n\n🛑 /stop | ⏭️ /next" if caption else f"👤: [Video]\n\n🛑 /stop | ⏭️ /next"
            )
        elif media_type == 'voice':
            await bot.send_voice(
                partner_id,
                voice=message.voice.file_id,
                caption=f"👤: [Ovozli xabar]\n\n🛑 /stop | ⏭️ /next"
            )
        elif media_type == 'sticker':
            await bot.send_sticker(partner_id, sticker=message.sticker.file_id)
            await bot.send_message(partner_id, f"👤: [Stiker]\n\n🛑 /stop | ⏭️ /next")
        elif media_type == 'document':
            caption = message.caption if message.caption else ""
            await bot.send_document(
                partner_id,
                document=message.document.file_id,
                caption=f"{caption}\n\n👤: [Fayl]\n\n🛑 /stop | ⏭️ /next" if caption else f"👤: [Fayl]\n\n🛑 /stop | ⏭️ /next"
            )
    except Exception as e:
        logger.error(f"{media_type} yuborishda xatolik: {e}")
        await message.answer(f"❌ Xabar yuborishda xatolik. Yangi suhbat: /find")

# ========== MAIN ==========
async def main():
    # Database yaratish
    init_db()
    
    print("🚀 Bot ishga tushmoqda...")
    try:
        bot_info = await bot.get_me()
        print(f"🤖 Bot: @{bot_info.username}")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print(f"📊 Database: {DB_FILE}")
        print("\n📋 Admin buyruqlari:")
        print("• /admin - Admin panel")
        print("• /stats - Statistika")
        print("• /users - Foydalanuvchilar ro'yxati")
        print("• /finduser [ID] - Foydalanuvchi qidirish")
        print("• /ban [ID] - Foydalanuvchini bloklash")
        print("• /unban [ID] - Blokdan chiqarish")
        print("• /broadcast - Hammaga xabar yuborish")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return
    
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
