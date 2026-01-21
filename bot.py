import telebot
from telebot import types
import json
import os
import time
import urllib.parse
import random
import string
from datetime import datetime
import sys

# --- الإعدادات الأساسية ---
API_TOKEN = os.environ.get('API_TOKEN', '8145050607:AAHu04ckOXTooWhMssqVXRe3wuAs2PLEltA')
bot = telebot.TeleBot(API_TOKEN, parse_mode=None)
OWNER_ID = 1507470467
DB_FILE = "users_data.json"
ADMINS_FILE = "admins_list.json"
NETFLIX_FILE = "netflix_accounts.json"
ICLOUD_FILE = "icloud_accounts.json"
MANDATORY_CHANNELS_FILE = "mandatory_channels.json"
TELEGRAM_ORDERS_FILE = "telegram_orders.json"
PURCHASES_HISTORY_FILE = "purchases_history.json"

# --- قائمة الدول وأكوادها ---
TELEGRAM_COUNTRIES = [
    {"flag": "🇷🇺", "name": "Russia", "code": "+7"},
    {"flag": "🇮🇱", "name": "Israel", "code": "+972"},
    {"flag": "🇨🇮", "name": "Côte d'Ivoire", "code": "+225"},
    {"flag": "🇮🇹", "name": "Italy", "code": "+39"},
    {"flag": "🇸🇦", "name": "Saudi Arabia", "code": "+966"},
    {"flag": "🇰🇪", "name": "Kenya", "code": "+254"},
    {"flag": "🇺🇦", "name": "Ukraine", "code": "+380"},
    {"flag": "🇪🇬", "name": "Egypt", "code": "+20"},
    {"flag": "🇽🇰", "name": "Kosovo", "code": "+383"},
    {"flag": "🇰🇼", "name": "Kuwait", "code": "+965"},
    {"flag": "🇲🇦", "name": "Morocco", "code": "+212"},
    {"flag": "🇳🇵", "name": "Nepal", "code": "+977"},
    {"flag": "🇸🇳", "name": "Senegal", "code": "+221"},
    {"flag": "🇪🇹", "name": "Ethiopia", "code": "+251"},
    {"flag": "🇩🇿", "name": "Algeria", "code": "+213"},
    {"flag": "🇹🇿", "name": "Tanzania", "code": "+255"}
]

# --- تحميل القنوات الإجبارية ---
def load_mandatory_channels():
    default_channels = ["@RexSubChannel_AR", "@RexSubChannel_EN"]
    if os.path.exists(MANDATORY_CHANNELS_FILE):
        try:
            with open(MANDATORY_CHANNELS_FILE, "r", encoding="utf-8") as f:
                channels = json.load(f)
                return channels if isinstance(channels, list) else default_channels
        except:
            return default_channels
    return default_channels

def save_mandatory_channels(channels):
    with open(MANDATORY_CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=4, ensure_ascii=False)
    global MANDATORY_CHANNELS
    MANDATORY_CHANNELS = channels

MANDATORY_CHANNELS = load_mandatory_channels()

# --- أسعار المنتجات ---
PRODUCT_PRICES = {
    'buy_netflix': 5,
    'buy_icloud': 4,
    'buy_telegram': 20
}

# --- وظائف البيانات الأساسية ---
def load_json(filename, default):
    """تحميل بيانات JSON"""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(filename, data):
    """حفظ بيانات JSON"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

def ensure_user_data(user_id):
    """التأكد من وجود بيانات المستخدم"""
    data = load_json(DB_FILE, {})
    user_id = str(user_id)
    
    if user_id not in data:
        data[user_id] = {
            'points': 0,
            'lang': 'ar',
            'referred_by': None,
            'rewarded': False,
            'purchases': 0,
            'spent_points': 0,
            'created_at': time.time(),
            'last_seen': time.time()
        }
        save_json(DB_FILE, data)
    
    return data[user_id]

def is_admin(user_id):
    """التحقق من صلاحيات المدير"""
    try:
        if int(user_id) == OWNER_ID:
            return True
        
        admins = load_json(ADMINS_FILE, [])
        if not admins:
            return False
        
        try:
            user_info = bot.get_chat(user_id)
            username = f"@{user_info.username}" if user_info.username else None
            return username in admins
        except:
            return False
    except:
        return False

def is_subscribed(user_id):
    """التحقق من اشتراك المستخدم في القنوات"""
    for ch in MANDATORY_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# --- البداية ---
@bot.message_handler(commands=['start', 'refresh'])
def start_command(message):
    """معالجة أمر /start"""
    user_id = str(message.chat.id)
    
    # إنشاء أو تحديث بيانات المستخدم
    user_data = ensure_user_data(user_id)
    
    # معالجة الإحالات
    command_parts = message.text.split()
    if len(command_parts) > 1:
        referrer_id = command_parts[1]
        if referrer_id != user_id and not user_data.get('rewarded', False):
            data = load_json(DB_FILE, {})
            if referrer_id in data:
                data[referrer_id]['points'] += 1
                user_data['referred_by'] = referrer_id
                user_data['rewarded'] = True
                data[user_id] = user_data
                save_json(DB_FILE, data)
    
    # إرسال رسالة الترحيب
    welcome_text = """🦖 أهلاً بك في ريكس ساب | RexSub 🔥
━━━━━━━━━━━━━━
يسعدنا انضمامك إلينا! هذا البوت مخصص لتقديم حسابات متنوعة.

💡 يمكنك البدء بجمع النقاط أو تصفح المتجر الآن."""
    
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")
    
    # عرض القائمة الرئيسية
    show_main_menu(user_id)

def show_main_menu(user_id):
    """عرض القائمة الرئيسية"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    markup.add("💰 الرصيد", "ℹ️ معلومات حسابك")
    markup.add("👫 الإحالات", "📞 الدعم الفني")
    markup.add("🔥 المتجر")
    
    if is_admin(user_id):
        markup.add("⚙️ لوحة الإدارة")
    
    menu_text = """🏠 **القائمة الرئيسية**
━━━━━━━━━━━━━━
استخدم الأزرار أدناه للتنقل داخل البوت:"""
    
    bot.send_message(user_id, menu_text, reply_markup=markup, parse_mode="Markdown")

# --- معالجة الرسائل النصية ---
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """معالجة جميع الرسائل النصية"""
    user_id = str(message.chat.id)
    user_data = ensure_user_data(user_id)
    
    # تحديث وقت آخر ظهور
    user_data['last_seen'] = time.time()
    data = load_json(DB_FILE, {})
    data[user_id] = user_data
    save_json(DB_FILE, data)
    
    # التحقق من الاشتراك في القنوات
    if not is_subscribed(user_id):
        show_subscription_required(user_id)
        return
    
    text = message.text.strip()
    
    # معالجة أوامر القائمة
    if text == "💰 الرصيد":
        show_balance(user_id)
    elif text == "ℹ️ معلومات حسابك":
        show_account_info(user_id)
    elif text == "👫 الإحالات":
        show_referrals(user_id)
    elif text == "📞 الدعم الفني":
        show_support(user_id)
    elif text == "🔥 المتجر":
        show_store(user_id)
    elif text == "⚙️ لوحة الإدارة":
        show_admin_panel(user_id)
    else:
        # إذا لم يكن الأمر معروفاً
        show_main_menu(user_id)
        bot.send_message(user_id, "🔍 لم أتعرف على طلبك. استخدم الأزرار أدناه للتنقل:")

def show_subscription_required(user_id):
    """عرض رسالة الاشتراك الإجباري"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in MANDATORY_CHANNELS:
        markup.add(types.InlineKeyboardButton(f"🔗 {ch}", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='verify'))
    
    sub_text = """🚫 **عذراً! الانضمام إجباري**
━━━━━━━━━━━━━━
يرجى الانضمام للقنوات الرسمية لتتمكن من استخدام البوت:"""
    
    bot.send_message(user_id, sub_text, reply_markup=markup, parse_mode="Markdown")

def show_balance(user_id):
    """عرض رصيد المستخدم"""
    user_data = ensure_user_data(user_id)
    pts = user_data.get('points', 0)
    bot.send_message(user_id, f"💰 رصيدك الحالي: `{pts}` نقطة", parse_mode="Markdown")

def show_account_info(user_id):
    """عرض معلومات حساب المستخدم"""
    data = load_json(DB_FILE, {})
    user_data = data.get(user_id, {})
    
    current_points = user_data.get('points', 0)
    purchases = user_data.get('purchases', 0)
    spent_points = user_data.get('spent_points', 0)
    referrals = len([u for u in data.values() if u.get('referred_by') == user_id])
    
    details_text = f"""ℹ️ **معلومات حسابك الشخصي**
━━━━━━━━━━━━━━

💰 **رصيدك الحالي**: `{current_points}` نقطة

🛍️ **السلع التي اشتريتها**: `{purchases}` عملية شراء

👥 **مشاركاتك لرابط الدعوة**: `{referrals}` شخص انضم عبر رابطك

📊 **الرصيد الذي استخدمته**: `{spent_points}` نقطة

━━━━━━━━━━━━━━
🚀 استمر في جمع النقاط واستمتع بالمتجر!"""
    
    bot.send_message(user_id, details_text, parse_mode="Markdown")

def show_referrals(user_id):
    """عرض نظام الإحالات"""
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    encoded_link = urllib.parse.quote(ref_link)
    share_url = f"https://t.me/share/url?url={encoded_link}&text=🎁 انضم معي للحصول على حسابات عالية الجوده مجاناً ✨"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 مشاركة الرابط فوراً", url=share_url))
    
    ref_text = f"""💎 **نظام المكافآت**
━━━━━━━━━━━━━━
شارك الرابط مع أصدقائك واحصل على **1 نقطة** لكل صديق ينضم:

🔗 `{ref_link}`"""
    
    bot.send_message(user_id, ref_text, reply_markup=markup, parse_mode="Markdown")

def show_support(user_id):
    """عرض معلومات الدعم"""
    support_text = """📞 **مركز الدعم والمساعدة**
━━━━━━━━━━━━━━
إذا واجهت أي مشكلة، نحن هنا لمساعدتك:

👨‍💼 @RexSubSUPPORT
👤 @J_1hz"""
    bot.send_message(user_id, support_text)

def show_store(user_id):
    """عرض المتجر"""
    user_data = ensure_user_data(user_id)
    pts = user_data.get('points', 0)
    
    store_text = f"""🔁 يمكنك استبدال نقاطك بحسابات بريميوم عديدة

💰 رصيدك الحالي: `{pts}` نقاط

🎁 استبدل نقاطك بـ:
 • 🎬 نتفلكس — 5 نقاط
 • ☁️ حسابات آي كلاود — 4 نقاط
 • 📱 أرقام تليجرام — 20 نقاط"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🎬 نتفلكس", callback_data='buy_netflix'))
    markup.add(types.InlineKeyboardButton("☁️ حسابات آي كلاود (اضغط هنا لعرض الحسابات)", callback_data='buy_icloud'))
    markup.add(types.InlineKeyboardButton("📱 أرقام تليجرام (اضغط هنا لعرض الارقام)", callback_data='buy_telegram'))
    
    bot.send_message(user_id, store_text, reply_markup=markup)

def show_admin_panel(user_id):
    """عرض لوحة الإدارة"""
    if not is_admin(user_id):
        bot.send_message(user_id, "⛔ ليس لديك صلاحية الوصول إلى لوحة الإدارة.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ تحويل النقاط", callback_data='admin_transfer'))
    markup.add(types.InlineKeyboardButton("👥 عرض الأعضاء", callback_data='view_members'))
    markup.add(types.InlineKeyboardButton("🛒 عرض المشتريات", callback_data='view_purchases'))
    markup.add(types.InlineKeyboardButton("🔍 بحث عن عضو", callback_data='search_member'))
    markup.add(types.InlineKeyboardButton("🔧 إصلاح بيانات النقاط", callback_data='fix_data'))
    markup.add(types.InlineKeyboardButton("➕ إضافة حسابات نتفلكس", callback_data='add_netflix'))
    markup.add(types.InlineKeyboardButton("📋 عرض حسابات نتفلكس", callback_data='view_netflix'))
    markup.add(types.InlineKeyboardButton("➕ إضافة حسابات آي كلاود", callback_data='add_icloud'))
    markup.add(types.InlineKeyboardButton("📋 عرض حسابات iCloud", callback_data='view_icloud'))
    markup.add(types.InlineKeyboardButton("📢 إدارة القنوات الإجبارية", callback_data='manage_channels'))
    markup.add(types.InlineKeyboardButton("👤 إضافة مدير", callback_data='add_admin'))
    markup.add(types.InlineKeyboardButton("➖ إزالة مدير", callback_data='remove_admin'))
    markup.add(types.InlineKeyboardButton("🔍 التحقق من طلب رقم التليجرام", callback_data='check_telegram_order'))
    
    bot.send_message(user_id, "⚙️ **لوحة تحكم الإدارة**", reply_markup=markup, parse_mode="Markdown")

# --- معالجة الكولباك ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة جميع الكولباك"""
    user_id = str(call.from_user.id)
    
    try:
        if call.data == 'verify':
            if is_subscribed(user_id):
                bot.delete_message(call.message.chat.id, call.message.message_id)
                show_main_menu(user_id)
            else:
                bot.answer_callback_query(call.id, "❌ قم بالانضمام إلى جميع القنوات أولاً!", show_alert=True)
        
        elif call.data in ['buy_netflix', 'buy_icloud', 'buy_telegram']:
            handle_purchase(user_id, call.data)
        
        elif call.data == 'view_members':
            if is_admin(user_id):
                show_members_list(user_id)
        
        elif call.data == 'view_purchases':
            if is_admin(user_id):
                show_purchases_list(user_id)
        
        elif call.data == 'search_member':
            if is_admin(user_id):
                search_member(user_id)
        
        elif call.data == 'fix_data':
            if is_admin(user_id):
                fix_points_data(user_id)
        
        elif call.data == 'admin_transfer':
            if is_admin(user_id):
                transfer_points(user_id)
        
        elif call.data == 'add_admin':
            if is_admin(user_id):
                add_admin(user_id)
        
        elif call.data == 'remove_admin':
            if is_admin(user_id):
                remove_admin(user_id)
        
        elif call.data == 'add_netflix':
            if is_admin(user_id):
                add_netflix_accounts(user_id)
        
        elif call.data == 'view_netflix':
            if is_admin(user_id):
                view_netflix_accounts(user_id)
        
        elif call.data == 'add_icloud':
            if is_admin(user_id):
                add_icloud_accounts(user_id)
        
        elif call.data == 'view_icloud':
            if is_admin(user_id):
                view_icloud_accounts(user_id)
        
        elif call.data == 'manage_channels':
            if is_admin(user_id):
                manage_channels(user_id)
        
        elif call.data == 'check_telegram_order':
            if is_admin(user_id):
                check_telegram_order(user_id)
        
        else:
            bot.answer_callback_query(call.id, "❌ هذا الزر غير معروف")
    
    except Exception as e:
        print(f"❌ خطأ في معالجة الكولباك: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ، يرجى المحاولة مرة أخرى")

def handle_purchase(user_id, product):
    """معالجة عملية الشراء"""
    user_data = ensure_user_data(user_id)
    pts = user_data.get('points', 0)
    
    if product == 'buy_netflix':
        required = 5
        if pts >= required:
            # معالجة شراء نتفلكس
            bot.send_message(user_id, "🎬 جاري معالجة طلب نتفلكس...")
            # هنا يمكنك إضافة منطق الشراء
        else:
            bot.send_message(user_id, f"🚫 رصيدك غير كافٍ! تحتاج {required} نقاط، لديك {pts} نقاط")
    
    elif product == 'buy_icloud':
        required = 4
        if pts >= required:
            # معالجة شراء iCloud
            bot.send_message(user_id, "☁️ جاري معالجة طلب iCloud...")
            # هنا يمكنك إضافة منطق الشراء
        else:
            bot.send_message(user_id, f"🚫 رصيدك غير كافٍ! تحتاج {required} نقاط، لديك {pts} نقاط")
    
    elif product == 'buy_telegram':
        required = 20
        if pts >= required:
            # معالجة شراء رقم تليجرام
            bot.send_message(user_id, "📱 جاري معالجة طلب رقم تليجرام...")
            # هنا يمكنك إضافة منطق الشراء
        else:
            bot.send_message(user_id, f"🚫 رصيدك غير كافٍ! تحتاج {required} نقاط، لديك {pts} نقاط")

# --- وظائف الإدارة ---
def show_members_list(admin_id):
    """عرض قائمة الأعضاء"""
    data = load_json(DB_FILE, {})
    
    if not data:
        bot.send_message(admin_id, "ℹ️ لا يوجد أعضاء في البوت بعد.")
        return
    
    total_members = len(data)
    total_points = sum(user.get('points', 0) for user in data.values())
    
    stats_text = f"""📊 **إحصائيات الأعضاء**
━━━━━━━━━━━━━━

👥 **إجمالي الأعضاء:** {total_members}
💰 **إجمالي النقاط:** {total_points}
📈 **متوسط النقاط:** {round(total_points/total_members, 2) if total_members > 0 else 0}
📅 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    bot.send_message(admin_id, stats_text, parse_mode="Markdown")
    
    # عرض 10 أعضاء كعينة
    members_text = "👥 **عينة من الأعضاء:**\n━━━━━━━━━━━━━━\n\n"
    
    for i, (user_id, user_data) in enumerate(list(data.items())[:10], 1):
        try:
            user_info = bot.get_chat(user_id)
            username = f"@{user_info.username}" if user_info.username else "بدون يوزر"
            name = user_info.first_name or "مجهول"
            points = user_data.get('points', 0)
            
            members_text += f"{i}. {name} ({username})\n💰 النقاط: {points}\n🆔 المعرف: `{user_id}`\n━━━━━━━━━━━━━━\n"
        except:
            continue
    
    bot.send_message(admin_id, members_text, parse_mode="Markdown")

def show_purchases_list(admin_id):
    """عرض قائمة المشتريات"""
    purchases = load_json(PURCHASES_HISTORY_FILE, [])
    
    if not purchases:
        bot.send_message(admin_id, "ℹ️ لا توجد مشتريات مسجلة بعد.")
        return
    
    total_purchases = len(purchases)
    total_amount = sum(p.get('price', 0) for p in purchases)
    
    stats_text = f"""📊 **إحصائيات المشتريات**
━━━━━━━━━━━━━━

🛍️ **إجمالي المشتريات:** {total_purchases}
💰 **إجمالي المبلغ:** {total_amount} نقطة
📅 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    bot.send_message(admin_id, stats_text, parse_mode="Markdown")
    
    # عرض آخر 5 مشتريات
    recent_text = "🛒 **آخر المشتريات:**\n━━━━━━━━━━━━━━\n\n"
    
    for i, purchase in enumerate(purchases[:5], 1):
        username = purchase.get('username', 'غير معروف')
        product = purchase.get('product', 'غير معروف')
        price = purchase.get('price', 0)
        date = purchase.get('date', 'غير معروف')
        
        recent_text += f"{i}. {username}\n📦 المنتج: {product}\n💰 السعر: {price} نقطة\n📅 التاريخ: {date}\n━━━━━━━━━━━━━━\n"
    
    bot.send_message(admin_id, recent_text, parse_mode="Markdown")

def search_member(admin_id):
    """البحث عن عضو"""
    msg = bot.send_message(admin_id, "🔍 أدخل يوزر العضو أو معرفه للبحث:")
    bot.register_next_step_handler(msg, process_member_search)

def process_member_search(message):
    """معالجة بحث العضو"""
    admin_id = str(message.chat.id)
    search_query = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    data = load_json(DB_FILE, {})
    
    found = False
    for user_id, user_data in data.items():
        try:
            user_info = bot.get_chat(user_id)
            
            # البحث بالمعرف
            if search_query == user_id:
                show_member_details(admin_id, user_id, user_data, user_info)
                found = True
                break
            
            # البحث باليوزر
            if user_info.username and f"@{user_info.username}" == search_query:
                show_member_details(admin_id, user_id, user_data, user_info)
                found = True
                break
        
        except:
            continue
    
    if not found:
        bot.send_message(admin_id, "❌ لم يتم العثور على العضو")

def show_member_details(admin_id, user_id, user_data, user_info):
    """عرض تفاصيل العضو"""
    username = f"@{user_info.username}" if user_info.username else "بدون يوزر"
    name = user_info.first_name or "غير معروف"
    points = user_data.get('points', 0)
    purchases = user_data.get('purchases', 0)
    
    details = f"""✅ **تم العثور على العضو**
━━━━━━━━━━━━━━

👤 **الاسم:** {name}
📱 **اليوزر:** {username}
💰 **النقاط:** {points}
🛍️ **المشتريات:** {purchases}
🆔 **المعرف:** `{user_id}`"""
    
    bot.send_message(admin_id, details, parse_mode="Markdown")

def fix_points_data(admin_id):
    """إصلاح بيانات النقاط"""
    data = load_json(DB_FILE, {})
    fixed = 0
    
    for user_id, user_data in data.items():
        # التأكد من أن النقاط هي عدد صحيح
        if not isinstance(user_data.get('points'), int):
            try:
                user_data['points'] = int(user_data.get('points', 0))
                fixed += 1
            except:
                user_data['points'] = 0
                fixed += 1
        
        # التأكد من عدم وجود نقاط سالبة
        if user_data['points'] < 0:
            user_data['points'] = 0
            fixed += 1
    
    save_json(DB_FILE, data)
    
    result = f"""🔧 **نتيجة الإصلاح**
━━━━━━━━━━━━━━

✅ **تم إصلاح:** {fixed} حساب
👥 **إجمالي الأعضاء:** {len(data)}
💾 **تم حفظ البيانات بنجاح**"""
    
    bot.send_message(admin_id, result, parse_mode="Markdown")

def transfer_points(admin_id):
    """تحويل النقاط"""
    msg = bot.send_message(admin_id, "👤 أدخل معرف المستخدم أو يوزره:")
    bot.register_next_step_handler(msg, process_transfer_user)

def process_transfer_user(message):
    """معالجة تحويل النقاط - الخطوة 1"""
    admin_id = str(message.chat.id)
    target = message.text.strip()
    
    msg = bot.send_message(admin_id, "💰 أدخل عدد النقاط:")
    bot.register_next_step_handler(msg, lambda m: process_transfer_amount(m, admin_id, target))

def process_transfer_amount(message, admin_id, target):
    """معالجة تحويل النقاط - الخطوة 2"""
    try:
        amount = int(message.text.strip())
        
        if amount <= 0:
            bot.send_message(admin_id, "❌ الرجاء إدخال عدد موجب")
            return
        
        data = load_json(DB_FILE, {})
        found_user_id = None
        
        # البحث عن المستخدم
        for user_id, user_data in data.items():
            try:
                user_info = bot.get_chat(user_id)
                if target == user_id or (user_info.username and f"@{user_info.username}" == target):
                    found_user_id = user_id
                    break
            except:
                continue
        
        if not found_user_id:
            bot.send_message(admin_id, "❌ لم يتم العثور على المستخدم")
            return
        
        # إضافة النقاط
        data[found_user_id]['points'] += amount
        save_json(DB_FILE, data)
        
        # إرسال إشعار للمستخدم
        try:
            bot.send_message(found_user_id, f"🎁 **مبروك! استلمت نقاط جديدة**\n━━━━━━━━━━━━━━\nتمت إضافة **{amount}** نقطة إلى حسابك من قبل الإدارة.", parse_mode="Markdown")
        except:
            pass
        
        bot.send_message(admin_id, f"✅ تم تحويل {amount} نقطة بنجاح!")
    
    except ValueError:
        bot.send_message(admin_id, "❌ الرجاء إدخال رقم صحيح")

def add_admin(admin_id):
    """إضافة مدير جديد"""
    msg = bot.send_message(admin_id, "👤 أدخل يوزر المدير الجديد (مثال: @username):")
    bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    """معالجة إضافة مدير"""
    admin_id = str(message.chat.id)
    new_admin = message.text.strip()
    
    if not new_admin.startswith('@'):
        bot.send_message(admin_id, "❌ الرجاء إدخال يوزر يبدأ بـ @")
        return
    
    admins = load_json(ADMINS_FILE, [])
    
    if new_admin in admins:
        bot.send_message(admin_id, "❌ هذا المدير موجود بالفعل")
        return
    
    admins.append(new_admin)
    save_json(ADMINS_FILE, admins)
    bot.send_message(admin_id, f"✅ تم إضافة المدير {new_admin} بنجاح!")

def remove_admin(admin_id):
    """إزالة مدير"""
    admins = load_json(ADMINS_FILE, [])
    
    if not admins:
        bot.send_message(admin_id, "ℹ️ لا يوجد مدراء لإزالتهم")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for admin in admins:
        markup.add(types.InlineKeyboardButton(admin, callback_data=f'remove_{admin}'))
    
    bot.send_message(admin_id, "📋 اختر المدير لإزالته:", reply_markup=markup)

def add_netflix_accounts(admin_id):
    """إضافة حسابات نتفلكس"""
    msg = bot.send_message(admin_id, "📝 أدخل حسابات نتفلكس (إيميل:باسورد، كل حساب في سطر):")
    bot.register_next_step_handler(msg, process_add_netflix)

def process_add_netflix(message):
    """معالجة إضافة حسابات نتفلكس"""
    admin_id = str(message.chat.id)
    accounts_text = message.text.strip()
    
    accounts = [acc.strip() for acc in accounts_text.split('\n') if ':' in acc]
    
    if not accounts:
        bot.send_message(admin_id, "❌ لم يتم إضافة حسابات")
        return
    
    netflix_data = load_json(NETFLIX_FILE, [])
    for acc in accounts:
        netflix_data.append({
            'account': acc,
            'max_users': 1,
            'remaining_users': 1,
            'users_received': []
        })
    
    save_json(NETFLIX_FILE, netflix_data)
    bot.send_message(admin_id, f"✅ تم إضافة {len(accounts)} حساب نتفلكس")

def view_netflix_accounts(admin_id):
    """عرض حسابات نتفلكس"""
    accounts = load_json(NETFLIX_FILE, [])
    
    if not accounts:
        bot.send_message(admin_id, "ℹ️ لا توجد حسابات نتفلكس")
        return
    
    total = len(accounts)
    available = sum(1 for acc in accounts if acc['remaining_users'] > 0)
    
    stats = f"""📺 **حسابات نتفلكس**
━━━━━━━━━━━━━━

📊 **الإجمالي:** {total} حساب
✅ **المتاحة:** {available} حساب
🚫 **المباعة:** {total - available} حساب"""
    
    bot.send_message(admin_id, stats, parse_mode="Markdown")

def add_icloud_accounts(admin_id):
    """إضافة حسابات iCloud"""
    msg = bot.send_message(admin_id, "📝 أدخل حساب iCloud (إيميل:باسورد):")
    bot.register_next_step_handler(msg, process_add_icloud)

def process_add_icloud(message):
    """معالجة إضافة حساب iCloud"""
    admin_id = str(message.chat.id)
    account = message.text.strip()
    
    if ':' not in account:
        bot.send_message(admin_id, "❌ تنسيق غير صحيح")
        return
    
    icloud_data = load_json(ICLOUD_FILE, [])
    icloud_data.append({
        'account': account,
        'max_users': 1,
        'remaining_users': 1,
        'users_received': []
    })
    
    save_json(ICLOUD_FILE, icloud_data)
    bot.send_message(admin_id, "✅ تم إضافة حساب iCloud")

def view_icloud_accounts(admin_id):
    """عرض حسابات iCloud"""
    accounts = load_json(ICLOUD_FILE, [])
    
    if not accounts:
        bot.send_message(admin_id, "ℹ️ لا توجد حسابات iCloud")
        return
    
    total = len(accounts)
    available = sum(1 for acc in accounts if acc['remaining_users'] > 0)
    
    stats = f"""☁️ **حسابات iCloud**
━━━━━━━━━━━━━━

📊 **الإجمالي:** {total} حساب
✅ **المتاحة:** {available} حساب
🚫 **المباعة:** {total - available} حساب"""
    
    bot.send_message(admin_id, stats, parse_mode="Markdown")

def manage_channels(admin_id):
    """إدارة القنوات الإجبارية"""
    channels = MANDATORY_CHANNELS
    
    if not channels:
        channels_text = "ℹ️ لا توجد قنوات إجبارية"
    else:
        channels_text = "📋 **القنوات الإجبارية:**\n\n"
        for i, ch in enumerate(channels, 1):
            channels_text += f"{i}. {ch}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة", callback_data='add_channel'),
        types.InlineKeyboardButton("➖ إزالة", callback_data='remove_channel_menu')
    )
    
    bot.send_message(admin_id, channels_text, reply_markup=markup, parse_mode="Markdown")

def check_telegram_order(admin_id):
    """التحقق من طلب تليجرام"""
    msg = bot.send_message(admin_id, "🔢 أدخل كود الطلب:")
    bot.register_next_step_handler(msg, process_check_order)

def process_check_order(message):
    """معالجة التحقق من الطلب"""
    admin_id = str(message.chat.id)
    order_code = message.text.strip()
    
    orders = load_json(TELEGRAM_ORDERS_FILE, [])
    
    for order in orders:
        if order.get('order_id') == order_code:
            details = f"""📋 **تفاصيل الطلب**
━━━━━━━━━━━━━━

🆔 **الكود:** {order['order_id']}
👤 **المستخدم:** {order.get('username', 'غير معروف')}
🌍 **الدولة:** {order.get('country', 'غير معروف')}
📅 **التاريخ:** {order.get('date', 'غير معروف')}
⏰ **الوقت:** {order.get('time', 'غير معروف')}"""
            
            bot.send_message(admin_id, details, parse_mode="Markdown")
            return
    
    bot.send_message(admin_id, "❌ لم يتم العثور على الطلب")

# --- تشغيل البوت ---
print("🚀 بدء تشغيل بوت RexSub...")
print(f"📱 التوكن: {API_TOKEN[:10]}...")
print("✅ البوت جاهز للعمل")

if __name__ == "__main__":
    try:
        print("🔧 جاري بدء الاستماع...")
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        print("🔄 إعادة التشغيل خلال 10 ثواني...")
        time.sleep(10)
