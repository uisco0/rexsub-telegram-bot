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

# --- إعدادات التسجيل ---
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
# احصل على التوكن من متغير البيئة أو استخدم التوكن المباشر
API_TOKEN = os.environ.get('API_TOKEN', '8145050607:AAHu04ckOXTooWhMssqVXRe3wuAs2PLEltA')
bot = telebot.TeleBot(API_TOKEN)
OWNER_ID = 1507470467
DB_FILE = "users_data.json"
ADMINS_FILE = "admins_list.json"
NETFLIX_FILE = "netflix_accounts.json"
ICLOUD_FILE = "icloud_accounts.json"
MANDATORY_CHANNELS_FILE = "mandatory_channels.json"
TELEGRAM_ORDERS_FILE = "telegram_orders.json"

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

# --- وظائف إدارة طلبات التليجرام ---
def generate_order_id():
    """توليد كود طلب فريد يبدأ بـ RS"""
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"RS-{timestamp}-{random_str}"

def save_telegram_order(order_data):
    """حفظ طلب التليجرام"""
    orders = load_json(TELEGRAM_ORDERS_FILE, [])
    if not isinstance(orders, list):
        orders = [orders] if orders else []
    orders.append(order_data)
    save_json(TELEGRAM_ORDERS_FILE, orders)

def get_telegram_order(order_id):
    """الحصول على طلب التليجرام بواسطة الكود"""
    orders = load_json(TELEGRAM_ORDERS_FILE, [])
    if not isinstance(orders, list):
        orders = [orders] if orders else []
    for order in orders:
        if order.get('order_id') == order_id:
            return order
    return None

def generate_random_number(country_code):
    """توليد رقم عشوائي للدولة"""
    clean_code = country_code.replace('+', '')
    
    if country_code == "+7":
        remaining = ''.join(random.choices('0123456789', k=10))
    elif country_code == "+39":
        remaining = ''.join(random.choices('0123456789', k=9))
    else:
        remaining = ''.join(random.choices('0123456789', k=9))
    
    return f"{country_code}{remaining}"

# --- قاموس النصوص ---
STRINGS = {
    'ar': {
        'welcome_msg': "🦖 أهلاً بك في ريكس ساب | RexSub 🔥\n━━━━━━━━━━━━━━\nيسعدنا انضمامك إلينا! هذا البوت مخصص لتقديم حسابات متنوعة.\n\n💡 يمكنك البدء بجمع النقاط أو تصفح المتجر الآن.",
        'main_menu': "🏠 **القائمة الرئيسية**\n━━━━━━━━━━━━━━\nاستخدم الأزرار أدناه للتنقل داخل البوت:",
        'sub_required': "🚫 **عذراً! الانضمام إجباري**\n━━━━━━━━━━━━━━\nيرجى الانضمام للقنوات الرسمية لتتمكن من استخدام البوت:",
        'verify': "✅ تحقق من الاشتراك",
        'my_account': "💰 الرصيد",
        'account_info': "ℹ️ معلومات حسابك",
        'earn_points': "👫 الإحالات",
        'support': "📞 الدعم الفني",
        'store': "🔥 المتجر",
        'admin': "⚙️ لوحة الإدارة",
        'acc_info': "💰 رصيدك الحالي: `{pts}` نقطة",
        'account_details': "ℹ️ **معلومات حسابك الشخصي**\n━━━━━━━━━━━━━━\n\n💰 **رصيدك الحالي**: `{current_points}` نقطة\n\n🛍️ **السلع التي اشتريتها**: `{purchases}` عملية شراء\n\n👥 **مشاركاتك لرابط الدعوة**: `{referrals}` شخص انضم عبر رابطك\n\n📊 **الرصيد الذي استخدمته**: `{spent_points}` نقطة\n\n━━━━━━━━━━━━━━\n🚀 استمر في جمع النقاط واستمتع بالمتجر!",
        'ref_info': "💎 **نظام المكافآت**\n━━━━━━━━━━━━━━\nشارك الرابط مع أصدقائك واحصل على **1 نقطة** لكل صديق ينضم:\n\n🔗 `{link}`",
        'share_btn': "🚀 مشاركة الرابط فوراً",
        'support_info': "📞 **مركز الدعم والمساعدة**\n━━━━━━━━━━━━━━\nإذا واجهت أي مشكلة، نحن هنا لمساعدتك:\n\n👨‍💼 @RexSubSUPPORT\n👤 @J_1hz",
        'transfer_msg': "🎁 **مبروك! استلمت نقاط جديدة**\n━━━━━━━━━━━━━━\nتمت إضافة **{amount}** نقطة إلى حسابك من قبل الإدارة.\n🚀 يمكنك استخدامها الآن في المتجر.",
        'share_text': "🎁 انضم معي للحصول على حسابات عالية الجوده مجاناً ✨",
        'store_msg': "🔁 يمكنك استبدال نقاطك بحسابات بريميوم عديدة\n\n💰 رصيدك الحالي: `{pts}` نقاط\n\n🎁 استبدل نقاطك بـ:\n • 🎬 نتفلكس — 5 نقاط\n • ☁️ حسابات آي كلاود — 4 نقاط\n • 📱 أرقام تليجرام — 20 نقاط",
        'btn_netflix': "🎬 نتفلكس",
        'btn_icloud': "☁️ حسابات آي كلاود (اضغط هنا لعرض الحسابات)",
        'btn_telegram': "📱 أرقام تليجرام (اضغط هنا لعرض الارقام)",
        'insufficient_points': "🚫 عذرًا، رصيدك غير كافٍ لشراء هذا المنتج!\n\n💰 رصيدك الحالي: {current} نقاط\n🔴 تحتاج إلى {required} نقاط لهذا المنتج\n\n💎 اجمع المزيد من النقاط عبر نظام الإحالة!",
        'success_select': "✅ تم اختيار المنتج بنجاح!\nجاري المعالجة...",
        'generating_msg': "🕒 جاري توليد الحساب...\n━━━━━━━━━━━━━━\nيرجى الانتظار لحظات قليلة ⏳",
        'account_delivered': "🎉 **مبروك! إليك حسابك**\n━━━━━━━━━━━━━━\n📧 **الإيميل**: `{email}`\n🔑 **كلمة السر**: `{password}`\n\n🔥 استمتع! إذا واجهت مشكلة، تواصل مع الدعم.",
        'add_netflix': "➕ إضافة حسابات نتفلكس",
        'add_netflix_prompt': "🆕 أدخل حسابات نتفلكس جديدة (إيميل:باسورد، كل حساب في سطر منفصل):",
        'add_netflix_success': "✅ تم إضافة الحسابات بنجاح!",
        'add_netflix_max_users_prompt': "🧑‍🤝‍🧑 أدخل عدد المستخدمين المسموح لكل حساب (مثال: 4):",
        'add_netflix_max_users_success': "✅ تم تحديد عدد المستخدمين بنجاح!",
        'product_unavailable': "🚫 عذرًا، هذا المنتج غير متوفر حاليًا!\n━━━━━━━━━━━━━━",
        'already_received': "🚫 لقد حصلت على هذا الحساب سابقًا!\n━━━━━━━━━━━━━━\n💡 يمكنك شراء حساب آخر إذا كان متوفرًا، أو اجمع نقاطًا لمزيد من الخيارات.",
        'remove_admin': "➖ إزالة مدير",
        'current_admins': "📋 **قائمة المدراء الحاليين**\n━━━━━━━━━━━━━━\nاختر المدير الذي تريد إزالته:",
        'admin_removed': "✅ تم إزالة المدير بنجاح!",
        'no_admins': "ℹ️ لا يوجد مدراء إضافيين حاليًا.",
        'view_netflix': "📋 عرض حسابات نتفلكس",
        'netflix_list_title': "📺 **حسابات نتفلكس المضافة**\n━━━━━━━━━━━━━━\nاختر حسابًا لحذفه يدويًا:",
        'netflix_item': "📧 {email}\n👥 متبقي {remaining} من {max}",
        'no_netflix': "ℹ️ لا توجد حسابات نتفلكس مضافة حاليًا.",
        'netflix_deleted': "✅ تم حذف الحساب بنجاح!",
        'add_icloud': "➕ إضافة حسابات آي كلاود",
        'add_icloud_account_prompt': "🆕 أدخل الحساب (إيميل:باسورد):",
        'add_icloud_photo_prompt': "📸 أرسل صورة للألعاب المتوفرة في الحساب:",
        'add_icloud_text_prompt': "📝 أدخل النص الذي تريده يظهر تحت الصورة:",
        'add_icloud_max_users_prompt': "🧑‍🤝‍🧑 أدخل عدد الأشخاص الذين يمكن أن يصل إليهم الحساب:",
        'add_icloud_success': "✅ تم إضافة حساب iCloud بنجاح!\n━━━━━━━━━━━━━━\n📸 الصورة محفوظة\n📝 النص: {text}\n👥 عدد المستخدمين: {max_users}",
        'view_icloud': "📋 عرض حسابات iCloud",
        'icloud_list_title': "☁️ **حسابات iCloud المضافة**\n━━━━━━━━━━━━━━\nاختر حسابًا لحذفه يدويًا:",
        'icloud_item': "📧 {email}\n📝 {text}\n👥 متبقي {remaining} من {max}",
        'no_icloud': "ℹ️ لا توجد حسابات iCloud مضافة حاليًا.",
        'icloud_deleted': "✅ تم حذف حساب iCloud بنجاح!",
        'icloud_list_msg': "☁️ **قائمة حسابات iCloud**\n━━━━━━━━━━━━━━\nاختر حسابًا للشراء:",
        'icloud_buy_btn': "اضغط للشراء | 4 نقاط",
        'icloud_buy_btn_sold': "تم شراء الحساب بنجاح",
        'manage_channels': "📢 إدارة القنوات الإجبارية",
        'current_channels': "📋 **القنوات الإجبارية الحالية**\n━━━━━━━━━━━━━━\nاختر قناة لحذفها:",
        'no_channels': "ℹ️ لا توجد قنوات إجبارية حاليًا.",
        'add_channel': "➕ إضافة قناة إجبارية",
        'add_channel_prompt': "🆕 أدخل يوزر القناة الجديدة (مثل @ChannelName):",
        'channel_added': "✅ تم إضافة القناة بنجاح!",
        'channel_removed': "✅ تم إزالة القناة بنجاح!",
        'invalid_channel': "❌ يرجى إدخال يوزر قناة صالح (مثل @ChannelName).",
        'telegram_countries_title': "📱 **أرقام تليجرام المميزة**\n━━━━━━━━━━━━━━\n💰 **السعر: 20 نقطة للرقم**\n\n🎯 **اختر نوع الرقم الذي تريده:**\n\n⬇️ اضغط على الدولة لتوليد رقم عشوائي فوراً",
        'telegram_country_btn': "{flag} {name} — {code}",
        'telegram_confirm_title': "🔢 **تأكيد طلب رقم تليجرام**\n━━━━━━━━━━━━━━\n📌 **الدولة المختارة:** {country}\n📞 **مفتاح الدولة:** {code}\n💰 **السعر:** 20 نقطة\n\n💎 **رصيدك الحالي:** {points} نقطة\n\n⚠️ هل أنت متأكد من شراء هذا الرقم؟",
        'telegram_confirm_yes': "✅ نعم، شراء الرقم",
        'telegram_confirm_no': "❌ إلغاء العملية",
        'telegram_processing': "⚡️ جاري توليد رقم تليجرام...\n━━━━━━━━━━━━━━\n⏳ يرجى الانتظار لحظات قليلة",
        'telegram_order_success': "🎉 **تم إنشاء طلبك بنجاح!**\n━━━━━━━━━━━━━━\n📋 **معلومات الطلب:**\n\n🆔 **كود الطلب:** `{order_id}`\n🌍 **الدولة:** {country}\n📅 **التاريخ:** {date}\n⏰ **الوقت:** {time}\n━━━━━━━━━━━━━━\n\n📝 **خطوات الاستلام:**\n1. أرسل كود طلبك إلى: @J_1hz\n2. انتظر الرد خلال 24 ساعة\n3. بعد التحقق من طلبك سيتم تسليمك الرقم\n\n⚠️ **هام:** احفظ كود الطلب جيداً\n🔒 الكود غير قابل للتكرار وفريد لك فقط",
        'telegram_check_order': "🔍 التحقق من طلب رقم التليجرام",
        'telegram_check_prompt': "🔢 **التحقق من طلب الرقم**\n━━━━━━━━━━━━━━\n📝 الرجاء إدخال كود الطلب الذي حصلت عليه:\n\n💡 مثال: RS-123456-ABCDEFGH",
        'telegram_order_not_found': "❌ **لم يتم العثور على الطلب**\n━━━━━━━━━━━━━━\n⚠️ كود الطلب غير صحيح أو منتهي الصلاحية\n\n🔍 تأكد من إدخال الكود بشكل صحيح\n💡 إذا واجهت مشكلة، تواصل مع الدعم",
        'telegram_order_details': "📋 **تفاصيل طلب رقم التليجرام**\n━━━━━━━━━━━━━━\n\n🆔 **كود الطلب:** `{order_id}`\n👤 **يوزر العميل:** {username}\n🌍 **الدولة:** {country}\n📅 **تاريخ الطلب:** {date}\n⏰ **وقت الطلب:** {time}\n💰 **السعر المدفوع:** 20 نقطة\n━━━━━━━━━━━━━━",
        'telegram_order_status_pending': "⏳ قيد الانتظار",
        'telegram_order_status_completed': "✅ مكتمل",
        'telegram_order_status_cancelled': "❌ ملغي",
        'view_members_full': "📊 عرض كامل",
        'view_members_fast': "🚀 عرض سريع",
        'view_stats_only': "📈 إحصائيات فقط",
        'choose_members_view': "👥 **اختر طريقة عرض الأعضاء:**",
        'no_members': "ℹ️ لا يوجد أعضاء في البوت بعد.",
        'members_stats': "📊 **إحصائيات شاملة للأعضاء**\n━━━━━━━━━━━━━━\n\n👥 **إجمالي الأعضاء:** {total}\n🚀 **الأعضاء النشطين:** {active} ({active_percent}%)\n💰 **إجمالي النقاط:** {total_points}\n🛍️ **إجمالي المشتريات:** {total_purchases}\n💸 **إجمالي النقاط المستخدمة:** {total_spent}\n📈 **متوسط النقاط:** {avg_points}\n🏪 **متوسط المشتريات:** {avg_purchases}\n━━━━━━━━━━━━━━\n📅 **آخر تحديث:** {update_time}",
    },
    'en': {
        'welcome_msg': "🦖 Welcome to RexSub 🔥\n━━━━━━━━━━━━━━\nWe're thrilled to have you! This bot is dedicated to providing a variety of premium accounts.\n\n💡 Start collecting points or browse the store now.",
        'main_menu': "🏠 **Main Menu**\n━━━━━━━━━━━━━━\nUse the buttons below to navigate through the bot:",
        'sub_required': "🚫 **Sorry! Joining is mandatory**\n━━━━━━━━━━━━━━\nPlease join our official channels to use the bot:",
        'verify': "✅ Verify Subscription",
        'my_account': "💰 My Account",
        'account_info': "ℹ️ Account Info",
        'earn_points': "👫 Referral",
        'support': "📞 Support",
        'store': "🔥 Store",
        'admin': "⚙️ Admin Panel",
        'acc_info': "💰 Balance: `{pts}` points",
        'account_details': "ℹ️ **Your Account Information**\n━━━━━━━━━━━━━━\n\n💰 **Current Balance**: `{current_points}` points\n\n🛍️ **Purchases Made**: `{purchases}` purchases\n\n👥 **Your Referrals**: `{referrals}` people joined via your link\n\n📊 **Points Spent**: `{spent_points}` points\n\n━━━━━━━━━━━━━━\n🚀 Keep earning points and enjoy the store!",
        'ref_info': "💎 **Rewards System**\n━━━━━━━━━━━━━━\nShare your link and get **1 point** for every friend who joins:\n\n🔗 `{link}`",
        'share_btn': "🚀 Share Link Now",
        'support_info': "📞 **Help & Support Center**\n━━━━━━━━━━━━━━\nIf you face any issues, we are here to help:\n\n👨‍💼 @RexSubSUPPORT\n👤 @J_1hz",
        'transfer_msg': "🎁 **Congratulations! Points Received**\n━━━━━━━━━━━━━━\n**{amount}** points have been added to your account by Admin.\n🚀 You can use them in the store now.",
        'share_text': "🎁 Join with me to get high quality accounts for free ✨",
        'store_msg': "🔁 You Can Exchange Your Points for Many Premium Accounts\n\n💰 Your Balance: `{pts}` Points\n\n🎁 Exchange Points To:\n • 🎬 Netflix — 5 Points\n • ☁️ iCloud Accounts — 4 Points\n • 📱 Telegram Numbers — 20 Points",
        'btn_netflix': "🎬 NETFLIX",
        'btn_icloud': "☁️ ICLOUD ACCOUNTS (click to show accounts)",
        'btn_telegram': "📱 TELEGRAM NUMBERS (click to show numbers)",
        'insufficient_points': "🚫 Sorry, your balance is insufficient for this product!\n\n💰 Current Balance: {current} Points\n🔴 You need {required} Points for this product\n\n💎 Earn more points through the referral system!",
        'success_select': "✅ Product selected successfully!\nProcessing...",
        'generating_msg': "🕒 Generating account...\n━━━━━━━━━━━━━━\nPlease wait a few moments ⏳",
        'account_delivered': "🎉 **Congratulations! Here is your account**\n━━━━━━━━━━━━━━\n📧 **Email**: `{email}`\n🔑 **Password**: `{password}`\n\n🔥 Enjoy! If you face issues, contact support.",
        'add_netflix': "➕ Add Netflix Accounts",
        'add_netflix_prompt': "🆕 Enter new Netflix accounts (email:password, one per line):",
        'add_netflix_success': "✅ Accounts added successfully!",
        'add_netflix_max_users_prompt': "🧑‍🤝‍🧑 Enter max users per account (e.g., 4):",
        'add_netflix_max_users_success': "✅ Max users set successfully!",
        'product_unavailable': "🚫 Sorry, this product is currently unavailable!\n━━━━━━━━━━━━━━",
        'already_received': "🚫 You have already received this account!\n━━━━━━━━━━━━━━\n💡 You can purchase another account if available, or earn points for more options.",
        'remove_admin': "➖ Remove Admin",
        'current_admins': "📋 **Current Admins List**\n━━━━━━━━━━━━━━\nSelect the admin you want to remove:",
        'admin_removed': "✅ Admin removed successfully!",
        'no_admins': "ℹ️ No additional admins currently.",
        'view_netflix': "📋 View Netflix Accounts",
        'netflix_list_title': "📺 **Added Netflix Accounts**\n━━━━━━━━━━━━━━\nSelect an account to delete manually:",
        'netflix_item': "📧 {email}\n👥 Remaining {remaining} of {max}",
        'no_netflix': "ℹ️ No Netflix accounts added yet.",
        'netflix_deleted': "✅ Account deleted successfully!",
        'add_icloud': "➕ Add iCloud Accounts",
        'add_icloud_account_prompt': "🆕 Enter the account (email:password):",
        'add_icloud_photo_prompt': "📸 Send a photo of the available games in the account:",
        'add_icloud_text_prompt': "📝 Enter the text to display under the photo:",
        'add_icloud_max_users_prompt': "🧑‍🤝‍🧑 Enter the number of people this account can reach:",
        'add_icloud_success': "✅ iCloud account added successfully!\n━━━━━━━━━━━━━━\n📸 Photo saved\n📝 Text: {text}\n👥 Max users: {max_users}",
        'view_icloud': "📋 View iCloud Accounts",
        'icloud_list_title': "☁️ **Added iCloud Accounts**\n━━━━━━━━━━━━━━\nSelect an account to delete manually:",
        'icloud_item': "📧 {email}\n📝 {text}\n👥 Remaining {remaining} of {max}",
        'no_icloud': "ℹ️ No iCloud accounts added yet.",
        'icloud_deleted': "✅ iCloud account deleted successfully!",
        'icloud_list_msg': "☁️ **iCloud Accounts List**\n━━━━━━━━━━━━━━\nChoose an account to purchase:",
        'icloud_buy_btn': "Click to Buy | 4 Points",
        'icloud_buy_btn_sold': "Account Purchased Successfully",
        'manage_channels': "📢 Manage Mandatory Channels",
        'current_channels': "📋 **Current Mandatory Channels**\n━━━━━━━━━━━━━━\nSelect a channel to remove:",
        'no_channels': "ℹ️ No mandatory channels currently.",
        'add_channel': "➕ Add Mandatory Channel",
        'add_channel_prompt': "🆕 Enter the new channel username (e.g., @ChannelName):",
        'channel_added': "✅ Channel added successfully!",
        'channel_removed': "✅ Channel removed successfully!",
        'invalid_channel': "❌ Please enter a valid channel username (e.g., @ChannelName).",
        'telegram_countries_title': "📱 **Premium Telegram Numbers**\n━━━━━━━━━━━━━━\n💰 **Price: 20 Points per Number**\n\n🎯 **Choose the type of number you want:**\n\n⬇️ Click on a country to generate random number instantly",
        'telegram_country_btn': "{flag} {name} — {code}",
        'telegram_confirm_title': "🔢 **Confirm Telegram Number Order**\n━━━━━━━━━━━━━━\n📌 **Selected Country:** {country}\n📞 **Country Code:** {code}\n💰 **Price:** 20 Points\n\n💎 **Your Balance:** {points} Points\n\n⚠️ Are you sure you want to buy this number?",
        'telegram_confirm_yes': "✅ Yes, Buy Number",
        'telegram_confirm_no': "❌ Cancel Order",
        'telegram_processing': "⚡️ Generating Telegram Number...\n━━━━━━━━━━━━━━\n⏳ Please wait a few moments",
        'telegram_order_success': "🎉 **Your Order Created Successfully!**\n━━━━━━━━━━━━━━\n📋 **Order Information:**\n\n🆔 **Order Code:** `{order_id}`\n🌍 **Country:** {country}\n📅 **Date:** {date}\n⏰ **Time:** {time}\n━━━━━━━━━━━━━━\n\n📝 **Receiving Steps:**\n1. Send your order code to: @J_1hz\n2. Wait for reply within 24 hours\n3. After verifying your order, you will receive the number\n\n⚠️ **Important:** Save your order code well\n🔒 Code is non-repeatable and unique to you",
        'telegram_copy_code': "📋 Copy Order Code",
        'telegram_check_order': "🔍 Check Telegram Number Order",
        'telegram_check_prompt': "🔢 **Check Number Order**\n━━━━━━━━━━━━━━\n📝 Please enter the order code you received:\n\n💡 Example: RS-123456-ABCDEFGH",
        'telegram_order_not_found': "❌ **Order Not Found**\n━━━━━━━━━━━━━━\n⚠️ Order code is incorrect or expired\n\n🔍 Make sure to enter the code correctly\n💡 If you face issues, contact support",
        'telegram_order_details': "📋 **Telegram Number Order Details**\n━━━━━━━━━━━━━━\n\n🆔 **Order Code:** `{order_id}`\n👤 **Client Username:** {username}\n🌍 **Country:** {country}\n📅 **Order Date:** {date}\n⏰ **Order Time:** {time}\n💰 **Paid Price:** 20 Points\n━━━━━━━━━━━━━━",
        'telegram_copy_details': "📋 Copy Order Details",
        'telegram_order_status_pending': "⏳ Pending",
        'telegram_order_status_completed': "✅ Completed",
        'telegram_order_status_cancelled': "❌ Cancelled",
        'view_members_full': "📊 Full View",
        'view_members_fast': "🚀 Fast View",
        'view_stats_only': "📈 Statistics Only",
        'choose_members_view': "👥 **Choose Members View Method:**",
        'no_members': "ℹ️ No members in the bot yet.",
        'members_stats': "📊 **Comprehensive Member Statistics**\n━━━━━━━━━━━━━━\n\n👥 **Total Members:** {total}\n🚀 **Active Members:** {active} ({active_percent}%)\n💰 **Total Points:** {total_points}\n🛍️ **Total Purchases:** {total_purchases}\n💸 **Total Points Spent:** {total_spent}\n📈 **Average Points:** {avg_points}\n🏪 **Average Purchases:** {avg_purchases}\n━━━━━━━━━━━━━━\n📅 **Last Update:** {update_time}",
    }
}

# --- وظائف البيانات ---
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def is_admin(user_id):
    try:
        if int(user_id) == OWNER_ID: return True
        admins = load_json(ADMINS_FILE, [])
        user_info = bot.get_chat(user_id)
        username = f"@{user_info.username}" if user_info.username else None
        return (username in admins)
    except: return False

def is_subscribed(user_id):
    for ch in MANDATORY_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ['member', 'administrator', 'creator']: return False
        except: return False
    return True

# --- إضافة حقول جديدة للمستخدم ---
def ensure_user_data(user_id):
    data = load_json(DB_FILE, {})
    if user_id not in data:
        data[user_id] = {
            'points': 0, 
            'lang': None, 
            'referred_by': None, 
            'rewarded': False, 
            'purchases': 0, 
            'spent_points': 0,
            'lang_prompt_sent': False,
            'unknown_command_sent': False
        }
    else:
        # إضافة الحقول الجديدة إذا لم تكن موجودة
        if 'lang_prompt_sent' not in data[user_id]:
            data[user_id]['lang_prompt_sent'] = False
        if 'unknown_command_sent' not in data[user_id]:
            data[user_id]['unknown_command_sent'] = False
        if 'purchases' not in data[user_id]:
            data[user_id]['purchases'] = 0
        if 'spent_points' not in data[user_id]:
            data[user_id]['spent_points'] = 0
    save_json(DB_FILE, data)
    return data[user_id]

# --- وظائف حسابات نتفلكس ---
def add_netflix_accounts(accounts_list, max_users):
    accounts = load_json(NETFLIX_FILE, [])
    for acc in accounts_list:
        accounts.append({
            'account': acc,
            'max_users': max_users,
            'remaining_users': max_users,
            'users_received': []
        })
    save_json(NETFLIX_FILE, accounts)

def get_netflix_account(user_id):
    accounts = load_json(NETFLIX_FILE, [])
    available_accounts = [acc for acc in accounts if acc['remaining_users'] > 0 and str(user_id) not in acc['users_received']]
    if not available_accounts:
        return None
    account = random.choice(available_accounts)
    account['remaining_users'] -= 1
    account['users_received'].append(str(user_id))
    if account['remaining_users'] == 0:
        accounts.remove(account)
    save_json(NETFLIX_FILE, accounts)
    return account['account']

def delete_netflix_account(index):
    accounts = load_json(NETFLIX_FILE, [])
    if 0 <= index < len(accounts):
        del accounts[index]
        save_json(NETFLIX_FILE, accounts)
        return True
    return False

# --- وظائف حسابات iCloud ---
def add_icloud_account(account, photo_id, text, max_users):
    accounts = load_json(ICLOUD_FILE, [])
    accounts.append({
        'account': account,
        'photo_id': photo_id,
        'text': text,
        'max_users': max_users,
        'remaining_users': max_users,
        'users_received': []
    })
    save_json(ICLOUD_FILE, accounts)

def get_icloud_account(user_id):
    accounts = load_json(ICLOUD_FILE, [])
    available_accounts = [acc for acc in accounts if acc['remaining_users'] > 0 and str(user_id) not in acc['users_received']]
    if not available_accounts:
        return None
    account = random.choice(available_accounts)
    account['remaining_users'] -= 1
    account['users_received'].append(str(user_id))
    if account['remaining_users'] == 0:
        accounts.remove(account)
    save_json(ICLOUD_FILE, accounts)
    return account['account'], account['photo_id'], account['text']

def delete_icloud_account(index):
    accounts = load_json(ICLOUD_FILE, [])
    if 0 <= index < len(accounts):
        del accounts[index]
        save_json(ICLOUD_FILE, accounts)
        return True
    return False

# ============ وظائف عرض الأعضاء ============

def show_members_list(admin_id):
    """عرض قائمة الأعضاء"""
    data = load_json(DB_FILE, {})
    
    if not data:
        bot.send_message(admin_id, STRINGS['ar']['no_members'])
        return
    
    total_members = len(data)
    members_text = f"👥 **إحصائيات الأعضاء**\n━━━━━━━━━━━━━━\n\n"
    members_text += f"📊 **إجمالي الأعضاء:** {total_members} عضو\n\n"
    members_text += "📋 **قائمة الأعضاء:**\n━━━━━━━━━━━━━━\n\n"
    
    members_list = []
    member_count = 0
    
    for user_id, user_data in data.items():
        try:
            # الحصول على معلومات المستخدم مع معالجة الأخطاء
            try:
                user_info = bot.get_chat(user_id)
                username = f"@{user_info.username}" if user_info.username else "بدون يوزر"
                first_name = user_info.first_name or "غير معروف"
                last_name = f" {user_info.last_name}" if user_info.last_name else ""
                full_name = f"{first_name}{last_name}"
            except Exception as e:
                # إذا فشل الحصول على المعلومات، استخدم البيانات المخزنة
                username = "غير متاح"
                full_name = "مستخدم مجهول"
                print(f"خطأ في جلب معلومات المستخدم {user_id}: {e}")
            
            # الحصول على البيانات من قاعدة البيانات
            points = user_data.get('points', 0)
            purchases = user_data.get('purchases', 0)
            spent_points = user_data.get('spent_points', 0)
            
            # إضافة معلومات العضو
            member_info = f"👤 **{full_name}**\n"
            member_info += f"📱 اليوزر: {username}\n"
            member_info += f"💰 النقاط الحالية: {points}\n"
            member_info += f"🛍️ المشتريات: {purchases}\n"
            member_info += f"💸 النقاط المستخدمة: {spent_points}\n"
            member_info += f"🆔 المعرف: `{user_id}`\n"
            member_info += f"━━━━━━━━━━━━━━\n"
            
            members_list.append(member_info)
            member_count += 1
            
            # إرسال الدفعات كل 5 أعضاء لتجنب تجاوز حد الأحرف
            if len(members_list) >= 5:
                chunk_text = members_text + "\n".join(members_list[:5])
                try:
                    bot.send_message(admin_id, chunk_text, parse_mode="Markdown")
                    time.sleep(0.3)  # تأخير بسيط لتجنب القيود
                except Exception as e:
                    print(f"خطأ في إرسال الرسالة: {e}")
                    # محاولة إرسال رسالة أقصر
                    error_msg = f"👥 الأعضاء من {member_count-4} إلى {member_count}: تم تحميل {len(members_list)} عضو"
                    bot.send_message(admin_id, error_msg)
                
                members_list = members_list[5:] if len(members_list) > 5 else []
                
        except Exception as e:
            print(f"خطأ في معالجة العضو {user_id}: {e}")
            continue
    
    # إرسال الأعضاء المتبقين
    if members_list:
        final_text = "📋 **استكمال قائمة الأعضاء:**\n━━━━━━━━━━━━━━\n\n" + "\n".join(members_list)
        try:
            bot.send_message(admin_id, final_text, parse_mode="Markdown")
        except:
            # إذا كانت الرسالة طويلة جداً، قسمها
            for i in range(0, len(final_text), 4000):
                chunk = final_text[i:i+4000]
                bot.send_message(admin_id, chunk, parse_mode="Markdown")
                time.sleep(0.2)
    
    # إرسال ملخص
    summary = f"✅ **تم تحميل {member_count} من أصل {total_members} عضو**\n"
    summary += f"📊 **نسبة العرض:** {round((member_count/total_members)*100, 2)}%\n"
    summary += "━━━━━━━━━━━━━━\n"
    summary += "💡 **ملاحظة:** قد لا تظهر بعض الأعضاء بسبب قيود التليجرام أو حسابات مغلقة."
    
    bot.send_message(admin_id, summary, parse_mode="Markdown")

def show_members_list_fast(admin_id):
    """عرض قائمة الأعضاء بسرعة باستخدام البيانات المخزنة فقط"""
    data = load_json(DB_FILE, {})
    
    if not data:
        bot.send_message(admin_id, STRINGS['ar']['no_members'])
        return
    
    total_members = len(data)
    
    # حساب الإحصائيات
    total_points = sum(user.get('points', 0) for user in data.values())
    total_purchases = sum(user.get('purchases', 0) for user in data.values())
    total_spent = sum(user.get('spent_points', 0) for user in data.values())
    
    # إرسال الإحصائيات أولاً
    stats_text = f"📊 **إحصائيات الأعضاء**\n━━━━━━━━━━━━━━\n\n"
    stats_text += f"👥 **إجمالي الأعضاء:** {total_members}\n"
    stats_text += f"💰 **إجمالي النقاط:** {total_points}\n"
    stats_text += f"🛍️ **إجمالي المشتريات:** {total_purchases}\n"
    stats_text += f"💸 **إجمالي النقاط المستخدمة:** {total_spent}\n"
    stats_text += f"📈 **متوسط النقاط لكل عضو:** {round(total_points/total_members, 2) if total_members > 0 else 0}\n"
    stats_text += "━━━━━━━━━━━━━━\n"
    
    bot.send_message(admin_id, stats_text, parse_mode="Markdown")
    
    # عرض 20 عضو عشوائي كمثال
    members_list = []
    sample_size = min(20, total_members)
    
    # أخذ عينة عشوائية
    sample_users = random.sample(list(data.items()), sample_size)
    
    for user_id, user_data in sample_users:
        points = user_data.get('points', 0)
        purchases = user_data.get('purchases', 0)
        spent_points = user_data.get('spent_points', 0)
        referrals = len([u for u in data.values() if u.get('referred_by') == user_id])
        
        member_info = f"🆔 `{user_id}`\n"
        member_info += f"💰 النقاط: {points} | 🛍️ المشتريات: {purchases}\n"
        member_info += f"💸 المستخدم: {spent_points} | 👥 أحاله: {referrals}\n"
        member_info += f"━━━━━━━━━━━━━━\n"
        
        members_list.append(member_info)
    
    members_text = f"🎯 **عينة عشوائية ({sample_size} عضو):**\n━━━━━━━━━━━━━━\n\n" + "\n".join(members_list)
    
    # قسمة النص إذا كان طويلاً
    if len(members_text) > 4000:
        parts = [members_text[i:i+4000] for i in range(0, len(members_text), 4000)]
        for i, part in enumerate(parts, 1):
            if i == 1:
                bot.send_message(admin_id, part, parse_mode="Markdown")
            else:
                bot.send_message(admin_id, f"📄 **الجزء {i}:**\n{part}", parse_mode="Markdown")
            time.sleep(0.2)
    else:
        bot.send_message(admin_id, members_text, parse_mode="Markdown")

# --- البداية ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    data = load_json(DB_FILE, {})
  
    command_parts = message.text.split()
    referrer_id = command_parts[1] if len(command_parts) > 1 and command_parts[1].isdigit() else None
    
    if user_id not in data:
        data[user_id] = {
            'points': 0, 
            'lang': None, 
            'referred_by': referrer_id, 
            'rewarded': False, 
            'purchases': 0, 
            'spent_points': 0,
            'lang_prompt_sent': True,
            'unknown_command_sent': False
        }
        save_json(DB_FILE, data)
    
    user_data = data[user_id]
    
    # إذا كان قد اختار اللغة مسبقاً، أظهر القائمة الرئيسية مباشرة
    if user_data.get('lang'):
        lang = user_data['lang']
        bot.send_message(user_id, STRINGS[lang]['welcome_msg'], parse_mode="Markdown")
        time.sleep(1)
        show_main_menu(message.chat.id, lang, user_id)
    else:
        # إذا لم يختر اللغة بعد، أرسل رسالة الاختيار
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 العربية", callback_data='lang_ar'),
                   types.InlineKeyboardButton("🌐 English", callback_data='lang_en'))
        bot.send_message(user_id, "🏮 Welcome to RexSub | اهلاً بك 🦖\nSelect your language / اختر اللغة:", reply_markup=markup)
        
        # ضع علامة أنه أرسل له الرسالة
        user_data['lang_prompt_sent'] = True
        data[user_id] = user_data
        save_json(DB_FILE, data)

# --- عرض القوائم ---
def show_main_menu(chat_id, lang, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    s = STRINGS[lang]
  
    markup.add(s['my_account'], s['account_info'])
    markup.add(s['earn_points'])
    markup.add(s['support'], s['store'])
    if is_admin(user_id): markup.add(s['admin'])
  
    bot.send_message(chat_id, s['main_menu'], reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    user_id = str(message.chat.id)
    data = load_json(DB_FILE, {})
    
    # تجاهل الرسائل التلقائية من التليجرام
    if not message.text:
        return
    
    # تجاهل الأوامر التي تبدأ بـ /
    if message.text.startswith('/'):
        return
    
    # إذا كان المستخدم غير موجود، لا تفعل شيئاً
    if user_id not in data: 
        return
    
    user_data = data[user_id]
    
    # إذا لم يختر اللغة بعد، أرسل رسالة اختيار اللغة مرة واحدة فقط
    if 'lang' not in user_data or not user_data['lang']:
        # تحقق إذا كان قد أرسل له رسالة سابقاً
        if not user_data.get('lang_prompt_sent', False):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌐 العربية", callback_data='lang_ar'),
                       types.InlineKeyboardButton("🌐 English", callback_data='lang_en'))
            bot.send_message(user_id, "🏮 Please select your language / اختر اللغة:", reply_markup=markup)
            # ضع علامة أنه أرسل له الرسالة
            user_data['lang_prompt_sent'] = True
            data[user_id] = user_data
            save_json(DB_FILE, data)
        return
    
    lang = user_data.get('lang', 'ar') or 'ar'
    s = STRINGS[lang]
    
    # التحقق من الاشتراك في القنوات
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ch in MANDATORY_CHANNELS:
            markup.add(types.InlineKeyboardButton(f"🔗 {ch}", url=f"https://t.me/{ch[1:]}"))
        markup.add(types.InlineKeyboardButton(s['verify'], callback_data='verify'))
        bot.send_message(user_id, s['sub_required'], reply_markup=markup, parse_mode="Markdown")
        return
    
    user_data = ensure_user_data(user_id)
    
    # الحصول على جميع نصوص الأزرار باللغتين
    all_button_texts = []
    for lang_code in STRINGS:
        lang_strings = STRINGS[lang_code]
        all_button_texts.extend([
            lang_strings['my_account'],
            lang_strings['account_info'],
            lang_strings['earn_points'],
            lang_strings['support'],
            lang_strings['store'],
            lang_strings['admin']
        ])
    
    all_button_texts = list(set(all_button_texts))
    
    user_text = message.text.strip()
    is_menu_command = user_text in all_button_texts
    
    # إذا كانت الرسالة ليست من أزرار القائمة الرئيسية، أعد عرض القائمة مرة واحدة
    if not is_menu_command:
        # تحقق إذا كان قد أرسل له رسالة "لم أتعرف" سابقاً
        if not user_data.get('unknown_command_sent', False):
            show_main_menu(message.chat.id, lang, user_id)
            bot.send_message(user_id, "🔍 لم أتعرف على طلبك. استخدم الأزرار أدناه للتنقل:")
            user_data['unknown_command_sent'] = True
            data[user_id] = user_data
            save_json(DB_FILE, data)
        return
    
    # إعادة تعيين العلامات عند استخدام أمر صحيح
    user_data['unknown_command_sent'] = False
    data[user_id] = user_data
    save_json(DB_FILE, data)
    
    # إذا كانت الرسالة من أزرار القائمة الرئيسية، قم بمعالجتها
    if is_menu_command:
        if user_text == s['my_account']:
            pts = user_data.get('points', 0)
            bot.send_message(user_id, s['acc_info'].format(pts=pts), parse_mode="Markdown")
        
        elif user_text == s['account_info']:
            current_points = user_data.get('points', 0)
            purchases = user_data.get('purchases', 0)
            referrals = len([u for u in data.values() if u.get('referred_by') == user_id])
            spent_points = user_data.get('spent_points', 0)
            details_text = s['account_details'].format(
                current_points=current_points,
                purchases=purchases,
                referrals=referrals,
                spent_points=spent_points
            )
            bot.send_message(user_id, details_text, parse_mode="Markdown")
        
        elif user_text == s['earn_points']:
            ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
            encoded_link = urllib.parse.quote(ref_link)
            share_url = f"https://t.me/share/url?url={encoded_link}&text={urllib.parse.quote(s['share_text'])}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(s['share_btn'], url=share_url))
            bot.send_message(user_id, s['ref_info'].format(link=ref_link), reply_markup=markup, parse_mode="Markdown")
        
        elif user_text == s['support']:
            bot.send_message(user_id, s['support_info'])
        
        elif user_text == s['store']:
            pts = user_data.get('points', 0)
            store_text = s['store_msg'].format(pts=pts)
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(s['btn_netflix'], callback_data='buy_netflix'))
            markup.add(types.InlineKeyboardButton(s['btn_icloud'], callback_data='buy_icloud'))
            markup.add(types.InlineKeyboardButton(s['btn_telegram'], callback_data='buy_telegram'))
            
            bot.send_message(user_id, store_text, reply_markup=markup)
        
        elif user_text == s['admin']:
            if is_admin(user_id):
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(types.InlineKeyboardButton("➕ تحويل النقاط", callback_data='admin_transfer'))
                markup.add(types.InlineKeyboardButton("👥 عرض الأعضاء", callback_data='view_members'))
                markup.add(types.InlineKeyboardButton(s['add_netflix'], callback_data='add_netflix'))
                markup.add(types.InlineKeyboardButton(s['view_netflix'], callback_data='view_netflix'))
                markup.add(types.InlineKeyboardButton(s['add_icloud'], callback_data='add_icloud'))
                markup.add(types.InlineKeyboardButton(s['view_icloud'], callback_data='view_icloud'))
                markup.add(types.InlineKeyboardButton(s['manage_channels'], callback_data='manage_channels'))
                markup.add(types.InlineKeyboardButton("👤 إضافة مدير", callback_data='add_admin'))
                markup.add(types.InlineKeyboardButton(s['remove_admin'], callback_data='remove_admin'))
                markup.add(types.InlineKeyboardButton(s['telegram_check_order'], callback_data='check_telegram_order'))
                bot.send_message(user_id, "⚙️ **لوحة تحكم الإدارة**", reply_markup=markup, parse_mode="Markdown")

# --- الكولباك (مع كل الميزات) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = str(call.from_user.id)
    data = load_json(DB_FILE, {})
    
    if user_id not in data:
        bot.answer_callback_query(call.id, "❌ يرجى البدء باستخدام الأمر /start أولاً", show_alert=True)
        return
    
    lang = data[user_id].get('lang', 'ar')
    
    if not lang:
        lang = 'ar'
        data[user_id]['lang'] = 'ar'
        data[user_id]['lang_prompt_sent'] = True
        save_json(DB_FILE, data)
    
    s = STRINGS[lang]
    user_data = ensure_user_data(user_id)
    pts = user_data.get('points', 0)
    
    if call.data.startswith('lang_'):
        lang = call.data.split('_')[1]
        data[user_id]['lang'] = lang
        data[user_id]['lang_prompt_sent'] = True
        data[user_id]['unknown_command_sent'] = False
        save_json(DB_FILE, data)
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, STRINGS[lang]['welcome_msg'], parse_mode="Markdown")
        
        time.sleep(1)
        show_main_menu(call.message.chat.id, lang, user_id)
        
    elif call.data == 'verify':
        if is_subscribed(user_id):
            ref_id = data[user_id].get('referred_by')
            if ref_id and not data[user_id].get('rewarded', False):
                if ref_id in data:
                    data[ref_id]['points'] += 1
                    data[user_id]['rewarded'] = True
                    save_json(DB_FILE, data)
                    bot.send_message(ref_id, "🎉 **New Referral!**\nSomeone joined using your link. +1 Point.", parse_mode="Markdown")
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_main_menu(call.message.chat.id, lang, user_id)
        else:
            bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)
        
    elif call.data in ['buy_netflix', 'buy_icloud', 'buy_telegram']:
        if call.data == 'buy_icloud':
            accounts = load_json(ICLOUD_FILE, [])
            if not accounts:
                bot.send_message(user_id, s['product_unavailable'], parse_mode="Markdown")
                return
            bot.send_message(user_id, s['icloud_list_msg'], parse_mode="Markdown")
            for i, acc in enumerate(accounts):
                caption = f"{acc['text']}\n━━━━━━━━━━━━━━"
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(s['icloud_buy_btn'], callback_data=f'purchase_icloud_{i}'))
                bot.send_photo(user_id, acc['photo_id'], caption=caption, reply_markup=markup, parse_mode="Markdown")
            return
        
        elif call.data == 'buy_telegram':
            markup = types.InlineKeyboardMarkup(row_width=2)
            for country in TELEGRAM_COUNTRIES:
                btn_text = s['telegram_country_btn'].format(
                    flag=country['flag'],
                    name=country['name'],
                    code=country['code']
                )
                markup.add(types.InlineKeyboardButton(
                    btn_text,
                    callback_data=f'telegram_country_{country["code"]}'
                ))
            
            bot.send_message(
                user_id,
                s['telegram_countries_title'],
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
        
        required_points = PRODUCT_PRICES[call.data]
        
        if pts >= required_points:
            bot.answer_callback_query(call.id, s['success_select'], show_alert=True)
            loading_msg = bot.send_message(user_id, s['generating_msg'], parse_mode="Markdown")
            time.sleep(3)
            
            if call.data == 'buy_netflix':
                account = get_netflix_account(user_id)
                if account:
                    email, password = account.split(':')
                    user_data['purchases'] += 1
                    user_data['spent_points'] += required_points
                    user_data['points'] -= required_points
                    save_json(DB_FILE, data)
                    bot.delete_message(user_id, loading_msg.message_id)
                    bot.send_message(user_id, s['account_delivered'].format(email=email, password=password), parse_mode="Markdown")
                else:
                    bot.delete_message(user_id, loading_msg.message_id)
                    bot.send_message(user_id, s['product_unavailable'], parse_mode="Markdown")
            else:
                bot.delete_message(user_id, loading_msg.message_id)
                bot.send_message(user_id, s['product_unavailable'], parse_mode="Markdown")
        else:
            msg = s['insufficient_points'].format(current=pts, required=required_points)
            bot.answer_callback_query(call.id, msg, show_alert=True)
    
    elif call.data.startswith('telegram_country_'):
        country_code = call.data.replace('telegram_country_', '')
        
        selected_country = None
        for country in TELEGRAM_COUNTRIES:
            if country['code'] == country_code:
                selected_country = country
                break
        
        if selected_country:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    s['telegram_confirm_yes'],
                    callback_data=f'confirm_telegram_{country_code}'
                ),
                types.InlineKeyboardButton(
                    s['telegram_confirm_no'],
                    callback_data='cancel_telegram'
                )
            )
            
            confirm_text = s['telegram_confirm_title'].format(
                country=f"{selected_country['flag']} {selected_country['name']}",
                code=selected_country['code'],
                points=pts
            )
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=confirm_text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
    
    elif call.data.startswith('confirm_telegram_'):
        country_code = call.data.replace('confirm_telegram_', '')
        
        selected_country = None
        for country in TELEGRAM_COUNTRIES:
            if country['code'] == country_code:
                selected_country = country
                break
        
        if selected_country:
            if pts >= PRODUCT_PRICES['buy_telegram']:
                processing_msg = bot.send_message(
                    user_id,
                    s['telegram_processing'],
                    parse_mode="Markdown"
                )
                time.sleep(2)
                
                phone_number = generate_random_number(country_code)
                
                order_id = generate_order_id()
                
                try:
                    user_info = bot.get_chat(user_id)
                    username = f"@{user_info.username}" if user_info.username else "بدون يوزر"
                except:
                    username = "غير معروف"
                
                order_data = {
                    'order_id': order_id,
                    'user_id': user_id,
                    'username': username,
                    'country': f"{selected_country['flag']} {selected_country['name']}",
                    'country_code': country_code,
                    'phone_number': phone_number,
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'status': 'pending',
                    'price_paid': PRODUCT_PRICES['buy_telegram']
                }
                save_telegram_order(order_data)
                
                user_data['points'] -= PRODUCT_PRICES['buy_telegram']
                user_data['spent_points'] += PRODUCT_PRICES['buy_telegram']
                user_data['purchases'] += 1
                
                data[user_id] = user_data
                save_json(DB_FILE, data)
                
                bot.delete_message(user_id, processing_msg.message_id)
                
                if lang == 'ar':
                    order_text = f"""🎉 <b>تم إنشاء طلبك بنجاح!</b>
━━━━━━━━━━━━━━
📋 <b>معلومات الطلب:</b>

🆔 <b>كود الطلب:</b> <code>{order_id}</code>
🌍 <b>الدولة:</b> {selected_country['flag']} {selected_country['name']}
📅 <b>التاريخ:</b> {datetime.now().strftime("%Y-%m-%d")}
⏰ <b>الوقت:</b> {datetime.now().strftime("%H:%M:%S")}
━━━━━━━━━━━━━━

📝 <b>خطوات الاستلام:</b>
1. أرسل كود طلبك إلى: @J_1hz
2. انتظر الرد خلال 24 ساعة
3. بعد التحقق من طلبك سيتم تسليمك الرقم

⚠️ <b>هام:</b> احفظ كود الطلب جيداً
🔒 الكود غير قابل للتكرار وفريد لك فقط"""
                else:
                    order_text = f"""🎉 <b>Your Order Created Successfully!</b>
━━━━━━━━━━━━━━
📋 <b>Order Information:</b>

🆔 <b>Order Code:</b> <code>{order_id}</code>
🌍 <b>Country:</b> {selected_country['flag']} {selected_country['name']}
📅 <b>Date:</b> {datetime.now().strftime("%Y-%m-%d")}
⏰ <b>Time:</b> {datetime.now().strftime("%H:%M:%S")}
━━━━━━━━━━━━━━

📝 <b>Receiving Steps:</b>
1. Send your order code to: @J_1hz
2. Wait for reply within 24 hours
3. After verifying your order, you will receive the number

⚠️ <b>Important:</b> Save your order code well
🔒 Code is non-repeatable and unique to you"""
                
                bot.send_message(
                    user_id,
                    order_text,
                    parse_mode="HTML"
                )
            else:
                msg = s['insufficient_points'].format(
                    current=pts,
                    required=PRODUCT_PRICES['buy_telegram']
                )
                bot.answer_callback_query(call.id, msg, show_alert=True)
    
    elif call.data == 'cancel_telegram':
        pts = user_data.get('points', 0)
        store_text = s['store_msg'].format(pts=pts)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(s['btn_netflix'], callback_data='buy_netflix'))
        markup.add(types.InlineKeyboardButton(s['btn_icloud'], callback_data='buy_icloud'))
        markup.add(types.InlineKeyboardButton(s['btn_telegram'], callback_data='buy_telegram'))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=store_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    elif call.data == 'check_telegram_order':
        msg = bot.send_message(
            user_id,
            s['telegram_check_prompt'],
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_order_check)
    
    elif call.data.startswith('purchase_icloud_'):
        index = int(call.data.split('_')[2])
        accounts = load_json(ICLOUD_FILE, [])
        if 0 <= index < len(accounts) and pts >= PRODUCT_PRICES['buy_icloud']:
            acc = accounts[index]
            if acc['remaining_users'] > 0 and str(user_id) not in acc['users_received']:
                bot.answer_callback_query(call.id, s['success_select'], show_alert=True)
                loading_msg = bot.send_message(user_id, s['generating_msg'], parse_mode="Markdown")
                time.sleep(3)
                email, password = acc['account'].split(':')
                acc['remaining_users'] -= 1
                acc['users_received'].append(str(user_id))
                if acc['remaining_users'] == 0:
                    accounts.remove(acc)
                save_json(ICLOUD_FILE, accounts)
                user_data['purchases'] += 1
                user_data['spent_points'] += PRODUCT_PRICES['buy_icloud']
                user_data['points'] -= PRODUCT_PRICES['buy_icloud']
                save_json(DB_FILE, data)
                bot.delete_message(user_id, loading_msg.message_id)
                bot.send_message(user_id, s['account_delivered'].format(email=email, password=password), parse_mode="Markdown")
                
                try:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(s['icloud_buy_btn_sold'], callback_data='already_purchased'))
                    
                    caption = f"{acc['text']}\n━━━━━━━━━━━━━━"
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=caption,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                except:
                    pass
            else:
                bot.answer_callback_query(call.id, s['product_unavailable'], show_alert=True)
        else:
            msg = s['insufficient_points'].format(current=pts, required=PRODUCT_PRICES['buy_icloud'])
            bot.answer_callback_query(call.id, msg, show_alert=True)
    
    elif call.data == 'already_purchased':
        bot.answer_callback_query(call.id, "⚠️ لقد قمت بشراء هذا الحساب بالفعل!", show_alert=True)
    
    # ============ وظائف الإدارة ============
    
    elif call.data == 'admin_transfer':
        if is_admin(user_id):
            msg = bot.send_message(user_id, "👤 أدخل معرف المستخدم الذي تريد تحويل النقاط إليه:")
            bot.register_next_step_handler(msg, process_transfer_user)
    
    elif call.data == 'view_members':
        if is_admin(user_id):
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(s['view_members_full'], callback_data='view_members_full'),
                types.InlineKeyboardButton(s['view_members_fast'], callback_data='view_members_fast'),
                types.InlineKeyboardButton(s['view_stats_only'], callback_data='view_stats_only')
            )
            bot.send_message(user_id, s['choose_members_view'], reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == 'view_members_full':
        if is_admin(user_id):
            show_members_list(user_id)
    
    elif call.data == 'view_members_fast':
        if is_admin(user_id):
            show_members_list_fast(user_id)
    
    elif call.data == 'view_stats_only':
        if is_admin(user_id):
            data = load_json(DB_FILE, {})
            if not data:
                bot.send_message(user_id, s['no_members'])
                return
            
            total_members = len(data)
            total_points = sum(user.get('points', 0) for user in data.values())
            total_purchases = sum(user.get('purchases', 0) for user in data.values())
            total_spent = sum(user.get('spent_points', 0) for user in data.values())
            
            # حساب الأعضاء النشطين (نقاط > 0 أو مشتريات > 0)
            active_members = sum(1 for user in data.values() if user.get('points', 0) > 0 or user.get('purchases', 0) > 0)
            active_percent = round((active_members/total_members)*100, 2) if total_members > 0 else 0
            
            stats_text = s['members_stats'].format(
                total=total_members,
                active=active_members,
                active_percent=active_percent,
                total_points=total_points,
                total_purchases=total_purchases,
                total_spent=total_spent,
                avg_points=round(total_points/total_members, 2) if total_members > 0 else 0,
                avg_purchases=round(total_purchases/total_members, 2) if total_members > 0 else 0,
                update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            bot.send_message(user_id, stats_text, parse_mode="Markdown")
    
    elif call.data == 'add_admin':
        if is_admin(user_id):
            msg = bot.send_message(user_id, "👤 أدخل يوزر المدير الجديد (مثل @username):")
            bot.register_next_step_handler(msg, process_add_admin)
    
    elif call.data == 'remove_admin':
        if is_admin(user_id):
            admins = load_json(ADMINS_FILE, [])
            if not admins:
                bot.send_message(user_id, "ℹ️ لا يوجد مدراء إضافيين لإزالتهم.")
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for admin in admins:
                markup.add(types.InlineKeyboardButton(admin, callback_data=f'remove_admin_{admin}'))
            
            bot.send_message(user_id, "📋 اختر المدير الذي تريد إزالته:", reply_markup=markup)
    
    elif call.data.startswith('remove_admin_'):
        if is_admin(user_id):
            admin_to_remove = call.data.replace('remove_admin_', '')
            admins = load_json(ADMINS_FILE, [])
            if admin_to_remove in admins:
                admins.remove(admin_to_remove)
                save_json(ADMINS_FILE, admins)
                bot.send_message(user_id, f"✅ تم إزالة المدير {admin_to_remove} بنجاح!")
            else:
                bot.send_message(user_id, "❌ هذا المدير غير موجود في القائمة.")
    
    elif call.data == 'add_netflix':
        if is_admin(user_id):
            msg = bot.send_message(user_id, "🆕 أدخل حسابات نتفلكس جديدة (إيميل:باسورد، كل حساب في سطر منفصل):")
            bot.register_next_step_handler(msg, process_add_netflix_accounts)
    
    elif call.data == 'view_netflix':
        if is_admin(user_id):
            accounts = load_json(NETFLIX_FILE, [])
            if not accounts:
                bot.send_message(user_id, "ℹ️ لا توجد حسابات نتفلكس مضافة.")
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i, acc in enumerate(accounts):
                email = acc['account'].split(':')[0]
                btn_text = f"📧 {email[:20]}... | 👥 {acc['remaining_users']}/{acc['max_users']}"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'delete_netflix_{i}'))
            
            bot.send_message(user_id, "📺 اختر حساب لحذفه:", reply_markup=markup)
    
    elif call.data.startswith('delete_netflix_'):
        if is_admin(user_id):
            index = int(call.data.replace('delete_netflix_', ''))
            if delete_netflix_account(index):
                bot.send_message(user_id, "✅ تم حذف الحساب بنجاح!")
            else:
                bot.send_message(user_id, "❌ فشل في حذف الحساب.")
    
    elif call.data == 'add_icloud':
        if is_admin(user_id):
            msg = bot.send_message(user_id, "🆕 أدخل حساب iCloud (إيميل:باسورد):")
            bot.register_next_step_handler(msg, process_add_icloud_account)
    
    elif call.data == 'view_icloud':
        if is_admin(user_id):
            accounts = load_json(ICLOUD_FILE, [])
            if not accounts:
                bot.send_message(user_id, "ℹ️ لا توجد حسابات iCloud مضافة.")
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i, acc in enumerate(accounts):
                email = acc['account'].split(':')[0]
                btn_text = f"📧 {email[:20]}... | 👥 {acc['remaining_users']}/{acc['max_users']}"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'delete_icloud_{i}'))
            
            bot.send_message(user_id, "☁️ اختر حساب لحذفه:", reply_markup=markup)
    
    elif call.data.startswith('delete_icloud_'):
        if is_admin(user_id):
            index = int(call.data.replace('delete_icloud_', ''))
            if delete_icloud_account(index):
                bot.send_message(user_id, "✅ تم حذف حساب iCloud بنجاح!")
            else:
                bot.send_message(user_id, "❌ فشل في حذف الحساب.")
    
    elif call.data == 'manage_channels':
        if is_admin(user_id):
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data='add_channel'))
            markup.add(types.InlineKeyboardButton("📋 عرض القنوات", callback_data='view_channels'))
            markup.add(types.InlineKeyboardButton("❌ حذف قناة", callback_data='remove_channel'))
            
            bot.send_message(user_id, "📢 إدارة القنوات الإجبارية:", reply_markup=markup)
    
    elif call.data == 'add_channel':
        if is_admin(user_id):
            msg = bot.send_message(user_id, "🆕 أدخل يوزر القناة الجديدة (مثل @ChannelName):")
            bot.register_next_step_handler(msg, process_add_channel)
    
    elif call.data == 'view_channels':
        if is_admin(user_id):
            channels = MANDATORY_CHANNELS
            if not channels:
                bot.send_message(user_id, "ℹ️ لا توجد قنوات إجبارية.")
                return
            
            channels_text = "📋 **القنوات الإجبارية الحالية:**\n\n"
            for i, channel in enumerate(channels, 1):
                channels_text += f"{i}. {channel}\n"
            
            bot.send_message(user_id, channels_text, parse_mode="Markdown")
    
    elif call.data == 'remove_channel':
        if is_admin(user_id):
            channels = MANDATORY_CHANNELS
            if not channels:
                bot.send_message(user_id, "ℹ️ لا توجد قنوات لإزالتها.")
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for channel in channels:
                markup.add(types.InlineKeyboardButton(channel, callback_data=f'remove_channel_{channel}'))
            
            bot.send_message(user_id, "❌ اختر القناة التي تريد إزالتها:", reply_markup=markup)
    
    elif call.data.startswith('remove_channel_'):
        if is_admin(user_id):
            channel_to_remove = call.data.replace('remove_channel_', '')
            channels = MANDATORY_CHANNELS.copy()
            if channel_to_remove in channels:
                channels.remove(channel_to_remove)
                save_mandatory_channels(channels)
                bot.send_message(user_id, f"✅ تم إزالة القناة {channel_to_remove} بنجاح!")
            else:
                bot.send_message(user_id, "❌ هذه القناة غير موجودة في القائمة.")

# ============ وظائف معالجة الخطوات ============

def process_transfer_user(message):
    admin_id = str(message.chat.id)
    target_user = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    msg = bot.send_message(admin_id, "💰 أدخل عدد النقاط التي تريد تحويلها:")
    bot.register_next_step_handler(msg, lambda m: process_transfer_amount(m, target_user))

def process_transfer_amount(message, target_user):
    admin_id = str(message.chat.id)
    amount = message.text.strip()
    
    if not amount.isdigit():
        bot.send_message(admin_id, "❌ الرجاء إدخال رقم صحيح.")
        return
    
    amount = int(amount)
    
    data = load_json(DB_FILE, {})
    user_found = None
    
    if target_user.isdigit():
        if target_user in data:
            user_found = target_user
    
    else:
        for user_id, user_data in data.items():
            try:
                user_info = bot.get_chat(user_id)
                if user_info.username and f"@{user_info.username}" == target_user:
                    user_found = user_id
                    break
            except:
                continue
    
    if not user_found:
        bot.send_message(admin_id, "❌ لم يتم العثور على المستخدم.")
        return
    
    if user_found not in data:
        data[user_found] = {'points': 0, 'lang': 'ar', 'referred_by': None, 'rewarded': False, 'purchases': 0, 'spent_points': 0, 'lang_prompt_sent': False, 'unknown_command_sent': False}
    
    data[user_found]['points'] += amount
    save_json(DB_FILE, data)
    
    try:
        bot.send_message(user_found, f"🎁 **مبروك! استلمت نقاط جديدة**\n━━━━━━━━━━━━━━\nتمت إضافة **{amount}** نقطة إلى حسابك من قبل الإدارة.\n🚀 يمكنك استخدامها الآن في المتجر.", parse_mode="Markdown")
    except:
        pass
    
    bot.send_message(admin_id, f"✅ تم تحويل {amount} نقطة إلى المستخدم بنجاح!")

def process_add_admin(message):
    admin_id = str(message.chat.id)
    new_admin = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    if not new_admin.startswith('@'):
        bot.send_message(admin_id, "❌ الرجاء إدخال يوزر يبدأ بـ @")
        return
    
    admins = load_json(ADMINS_FILE, [])
    if new_admin in admins:
        bot.send_message(admin_id, "❌ هذا المدير موجود بالفعل.")
        return
    
    admins.append(new_admin)
    save_json(ADMINS_FILE, admins)
    bot.send_message(admin_id, f"✅ تم إضافة المدير {new_admin} بنجاح!")

def process_add_netflix_accounts(message):
    admin_id = str(message.chat.id)
    accounts_text = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    accounts_list = [acc.strip() for acc in accounts_text.split('\n') if ':' in acc]
    
    if not accounts_list:
        bot.send_message(admin_id, "❌ الرجاء إدخال حسابات بصيغة صحيحة.")
        return
    
    msg = bot.send_message(admin_id, "🧑‍🤝‍🧑 أدخل عدد المستخدمين المسموح لكل حساب (مثال: 4):")
    bot.register_next_step_handler(msg, lambda m: process_netflix_max_users(m, accounts_list))

def process_netflix_max_users(message, accounts_list):
    admin_id = str(message.chat.id)
    max_users = message.text.strip()
    
    if not max_users.isdigit():
        bot.send_message(admin_id, "❌ الرجاء إدخال رقم صحيح.")
        return
    
    max_users = int(max_users)
    add_netflix_accounts(accounts_list, max_users)
    bot.send_message(admin_id, f"✅ تم إضافة {len(accounts_list)} حساب نتفلكس بنجاح!")

def process_add_icloud_account(message):
    admin_id = str(message.chat.id)
    account = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    if ':' not in account:
        bot.send_message(admin_id, "❌ الرجاء إدخال حساب بصيغة صحيحة (إيميل:باسورد).")
        return
    
    msg = bot.send_message(admin_id, "📸 أرسل صورة للألعاب المتوفرة في الحساب:")
    bot.register_next_step_handler(msg, lambda m: process_icloud_photo(m, account))

def process_icloud_photo(message, account):
    admin_id = str(message.chat.id)
    
    if not is_admin(admin_id):
        return
    
    if not message.photo:
        bot.send_message(admin_id, "❌ الرجاء إرسال صورة.")
        return
    
    photo_id = message.photo[-1].file_id
    msg = bot.send_message(admin_id, "📝 أدخل النص الذي تريده يظهر تحت الصورة:")
    bot.register_next_step_handler(msg, lambda m: process_icloud_text(m, account, photo_id))

def process_icloud_text(message, account, photo_id):
    admin_id = str(message.chat.id)
    text = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    msg = bot.send_message(admin_id, "🧑‍🤝‍🧑 أدخل عدد الأشخاص الذين يمكن أن يصل إليهم الحساب:")
    bot.register_next_step_handler(msg, lambda m: process_icloud_max_users(m, account, photo_id, text))

def process_icloud_max_users(message, account, photo_id, text):
    admin_id = str(message.chat.id)
    max_users = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    if not max_users.isdigit():
        bot.send_message(admin_id, "❌ الرجاء إدخال رقم صحيح.")
        return
    
    max_users = int(max_users)
    add_icloud_account(account, photo_id, text, max_users)
    bot.send_message(admin_id, f"✅ تم إضافة حساب iCloud بنجاح!\n📝 النص: {text}\n👥 عدد المستخدمين: {max_users}")

def process_add_channel(message):
    admin_id = str(message.chat.id)
    channel = message.text.strip()
    
    if not is_admin(admin_id):
        return
    
    if not channel.startswith('@'):
        bot.send_message(admin_id, "❌ الرجاء إدخال يوزر قناة يبدأ بـ @")
        return
    
    channels = MANDATORY_CHANNELS.copy()
    if channel in channels:
        bot.send_message(admin_id, "❌ هذه القناة موجودة بالفعل.")
        return
    
    channels.append(channel)
    save_mandatory_channels(channels)
    bot.send_message(admin_id, f"✅ تم إضافة القناة {channel} بنجاح!")

def process_order_check(message):
    user_id = str(message.chat.id)
    order_code = message.text.strip()
    
    data = load_json(DB_FILE, {})
    lang = data[user_id].get('lang', 'ar') or 'ar'
    s = STRINGS[lang]
    
    order = get_telegram_order(order_code)
    
    if order:
        if lang == 'ar':
            order_text = f"""📋 <b>تفاصيل طلب رقم التليجرام</b>
━━━━━━━━━━━━━━

🆔 <b>كود الطلب:</b> <code>{order['order_id']}</code>
👤 <b>يوزر العميل:</b> {order.get('username', 'غير معروف')}
🌍 <b>الدولة:</b> {order['country']}
📅 <b>تاريخ الطلب:</b> {order['date']}
⏰ <b>وقت الطلب:</b> {order['time']}
💰 <b>السعر المدفوع:</b> 20 نقطة
━━━━━━━━━━━━━━"""
        else:
            order_text = f"""📋 <b>Telegram Number Order Details</b>
━━━━━━━━━━━━━━

🆔 <b>Order Code:</b> <code>{order['order_id']}</code>
👤 <b>Client Username:</b> {order.get('username', 'Unknown')}
🌍 <b>Country:</b> {order['country']}
📅 <b>Order Date:</b> {order['date']}
⏰ <b>Order Time:</b> {order['time']}
💰 <b>Paid Price:</b> 20 Points
━━━━━━━━━━━━━━"""
        
        bot.send_message(
            user_id,
            order_text,
            parse_mode="HTML"
        )
    else:
        bot.send_message(
            user_id,
            s['telegram_order_not_found'],
            parse_mode="Markdown"
        )

# --- تشغيل البوت ---
print("🚀 RexSub Bot is starting...")
print(f"📱 Token: {API_TOKEN[:10]}...")
print("✅ Bot configured for Railway deployment")
print("🛡️ Anti-spam protection activated")

if __name__ == "__main__":
    try:
        print("🔧 Starting infinity polling...")
        bot.infinity_polling(timeout=60, long_polling_timeout=20)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Restarting in 10 seconds...")
        time.sleep(10)
