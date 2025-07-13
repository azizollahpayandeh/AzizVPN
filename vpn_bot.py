import telebot
from telebot import types
import os
import time
import json
from datetime import datetime

# تنظیمات اولیه
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
CARD_NUMBER = os.getenv("CARD_NUMBER")


# فایل‌های ذخیره‌سازی
DATA_FILES = {
    'users': 'users_data.json',
    'blocked': 'blocked_users.json',
    'configs': 'configs_data.json',
    'discount': 'discount_data.json',
    'orders': 'orders_data.json'
}

# ایجاد نمونه ربات
bot = telebot.TeleBot(BOT_TOKEN)

# حافظه موقت برای ذخیره اطلاعات سفارش
user_data = {}

# دیتابیس ساده برای ذخیره اطلاعات
users_db = {}
blocked_users = set()
configs_db = {}
discount_percentage = 0  # درصد تخفیف عمومی
orders_db = {}  # ذخیره سفارشات

# تابع‌های ذخیره‌سازی و بارگذاری داده‌ها
def save_data():
    """ذخیره تمام داده‌ها در فایل‌های JSON"""
    try:
        # ذخیره اطلاعات کاربران
        with open(DATA_FILES['users'], 'w', encoding='utf-8') as f:
            json.dump(users_db, f, ensure_ascii=False, indent=2)
        
        # ذخیره کاربران مسدود
        with open(DATA_FILES['blocked'], 'w', encoding='utf-8') as f:
            json.dump(list(blocked_users), f, ensure_ascii=False, indent=2)
        
        # ذخیره کانفیگ‌ها
        with open(DATA_FILES['configs'], 'w', encoding='utf-8') as f:
            json.dump(configs_db, f, ensure_ascii=False, indent=2)
        
        # ذخیره تخفیف
        with open(DATA_FILES['discount'], 'w', encoding='utf-8') as f:
            json.dump({'discount_percentage': discount_percentage}, f, ensure_ascii=False, indent=2)
        
        # ذخیره سفارشات
        with open(DATA_FILES['orders'], 'w', encoding='utf-8') as f:
            json.dump(orders_db, f, ensure_ascii=False, indent=2)
        
        print("✅ تمام داده‌ها با موفقیت ذخیره شدند.")
    except Exception as e:
        print(f"❌ خطا در ذخیره داده‌ها: {e}")

def load_data():
    """بارگذاری تمام داده‌ها از فایل‌های JSON"""
    global users_db, blocked_users, configs_db, discount_percentage, orders_db
    
    try:
        # بارگذاری اطلاعات کاربران
        if os.path.exists(DATA_FILES['users']):
            with open(DATA_FILES['users'], 'r', encoding='utf-8') as f:
                users_db = json.load(f)
                # تبدیل کلیدهای string به int
                users_db = {int(k): v for k, v in users_db.items()}
        
        # بارگذاری کاربران مسدود
        if os.path.exists(DATA_FILES['blocked']):
            with open(DATA_FILES['blocked'], 'r', encoding='utf-8') as f:
                blocked_list = json.load(f)
                blocked_users = set(int(x) for x in blocked_list)
        
        # بارگذاری کانفیگ‌ها
        if os.path.exists(DATA_FILES['configs']):
            with open(DATA_FILES['configs'], 'r', encoding='utf-8') as f:
                configs_db = json.load(f)
        
        # بارگذاری تخفیف
        if os.path.exists(DATA_FILES['discount']):
            with open(DATA_FILES['discount'], 'r', encoding='utf-8') as f:
                discount_data = json.load(f)
                discount_percentage = discount_data.get('discount_percentage', 0)
        
        # بارگذاری سفارشات
        if os.path.exists(DATA_FILES['orders']):
            with open(DATA_FILES['orders'], 'r', encoding='utf-8') as f:
                orders_db = json.load(f)
                # تبدیل کلیدهای string به int
                orders_db = {int(k): v for k, v in orders_db.items()}
        
        print("✅ تمام داده‌ها با موفقیت بارگذاری شدند.")
        print(f"📊 آمار بارگذاری شده:")
        print(f"   👥 کاربران: {len(users_db)}")
        print(f"   🚫 مسدودها: {len(blocked_users)}")
        print(f"   🔐 کانفیگ‌ها: {len(configs_db)}")
        print(f"   💰 تخفیف: {discount_percentage}%")
        print(f"   📦 سفارشات: {len(orders_db)}")
        
    except Exception as e:
        print(f"❌ خطا در بارگذاری داده‌ها: {e}")

# بارگذاری داده‌ها در شروع ربات
load_data()

# تعریف قیمت‌ها (به تومان)
prices = {
    "30GB": {
        "1month": 40000,

    },
    "50GB": {
        "1month": 60000,

    },
    "70GB": {
        "1month": 90000,

    },
    "100GB": {
        "1month": 120000,

    },
    "150GB": {
        "1month": 180000,

    },
    
}

# دستور شروع
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    # بررسی مسدودیت کاربر
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    # ثبت کاربر در دیتابیس
    if user_id not in users_db:
        users_db[user_id] = {
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'orders': [],
            'total_spent': 0
        }
        save_data()  # ذخیره تغییرات
    
    # پاک کردن اطلاعات قبلی کاربر اگر وجود داشته باشد
    if user_id in user_data:
        user_data[user_id] = {}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('🛒 خرید فیلترشکن')
    btn2 = types.KeyboardButton('👤 حساب من')
    btn3 = types.KeyboardButton('🔐 کانفیگ‌های من')
    btn4 = types.KeyboardButton('📞 پشتیبانی')
    markup.add(btn1, btn2, btn3, btn4)
    
    # اگر کاربر ادمین است، دکمه مدیریت را اضافه کن
    if user_id == ADMIN_ID:
        admin_btn = types.KeyboardButton('⚙️ پنل مدیریت')
        markup.add(admin_btn)
        bot.send_message(message.chat.id, f"🔐 شما به عنوان ادمین شناسایی شدید. آیدی شما: {user_id}")
    
    bot.send_message(message.chat.id, 
                     "👋 سلام به ربات فروش فیلترشکن AzizVPN خوش آمدید!\n\n"
                     "لطفا یکی از گزینه‌های زیر را انتخاب کنید:", 
                     reply_markup=markup)

# پاسخ به دکمه‌های اصلی
@bot.message_handler(func=lambda message: message.text in ['🛒 خرید فیلترشکن', '👤 حساب من', '🔐 کانفیگ‌های من', '📞 پشتیبانی', '⚙️ پنل مدیریت'])
def main_menu_handler(message):
    if message.text == '🛒 خرید فیلترشکن':
        show_data_plans(message)
    elif message.text == '👤 حساب من':
        show_user_account(message)
    elif message.text == '🔐 کانفیگ‌های من':
        show_user_configs(message)
    elif message.text == '📞 پشتیبانی':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back = types.KeyboardButton('🔙 بازگشت')
        markup.add(back)
        
        bot.send_message(message.chat.id, 
                         "📞 پشتیبانی:\n\n"
                         "لطفا پیام خود را ارسال کنید تا برای پشتیبانی ارسال شود.\n"
                         "همکاران ما در اسرع وقت به شما پاسخ خواهند داد.",
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_support_message)
    elif message.text == '⚙️ پنل مدیریت' and message.from_user.id == ADMIN_ID:
        show_admin_panel(message)

# پاسخ به دکمه‌های پنل مدیریت
@bot.message_handler(func=lambda message: message.text in ['👥 مدیریت کاربران', '📊 آمار ربات', '🔐 مدیریت کانفیگ‌ها', '📢 پیام همگانی', '💰 مدیریت تخفیف', '🚫 مدیریت مسدودیت', '📞 پیام‌های پشتیبانی', '🔄 تست ارسال به ادمین'])
def admin_panel_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '👥 مدیریت کاربران':
        manage_users(message)
    elif message.text == '📊 آمار ربات':
        bot_statistics(message)
    elif message.text == '🔐 مدیریت کانفیگ‌ها':
        manage_configs(message)
    elif message.text == '📢 پیام همگانی':
        broadcast_message_menu(message)
    elif message.text == '💰 مدیریت تخفیف':
        manage_discount(message)
    elif message.text == '🚫 مدیریت مسدودیت':
        manage_blocked_users(message)
    elif message.text == '📞 پیام‌های پشتیبانی':
        show_support_info(message)
    elif message.text == '🔄 تست ارسال به ادمین':
        test_admin_message(message)

# نمایش حساب کاربری
def show_user_account(message):
    user_id = message.from_user.id
    if user_id in users_db:
        user = users_db[user_id]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back = types.KeyboardButton('🔙 بازگشت')
        markup.add(back)
        
        bot.send_message(message.chat.id, 
                         f"👤 حساب کاربری شما:\n\n"
                         f"🆔 آیدی: `{user_id}`\n"
                         f"👤 نام: {user.get('first_name', 'نامشخص')}\n"
                         f"📅 تاریخ عضویت: {user.get('join_date', 'نامشخص')}\n"
                         f"📦 تعداد سفارشات: {len(user.get('orders', []))}\n"
                         f"💰 کل هزینه: {user.get('total_spent', 0):,} تومان",
                         parse_mode="Markdown",
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ اطلاعات کاربری یافت نشد.")

# نمایش کانفیگ‌های کاربر
def show_user_configs(message):
    user_id = message.from_user.id
    
    # بررسی مسدودیت کاربر
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    if user_id not in users_db:
        bot.send_message(message.chat.id, "❌ ابتدا باید در ربات ثبت نام کنید.")
        return
    
    user = users_db[user_id]
    orders = user.get('orders', [])
    
    if not orders:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back = types.KeyboardButton('🔙 بازگشت')
        markup.add(back)
        
        bot.send_message(message.chat.id, 
                        "🔐 کانفیگ‌های من:\n\n"
                        "📭 شما هنوز هیچ کانفیگی خریداری نکرده‌اید.\n"
                        "برای خرید کانفیگ، روی دکمه '🛒 خرید فیلترشکن' کلیک کنید.",
                        reply_markup=markup)
        return
    
    # نمایش کانفیگ‌های کاربر
    configs_info = "🔐 کانفیگ‌های من:\n\n"
    
    for i, order in enumerate(orders, 1):
        username = order.get('username', 'نامشخص')
        data_plan = order.get('data_plan', 'نامشخص')
        duration = order.get('duration', 'نامشخص')
        price = order.get('price', 0)
        order_time = order.get('order_time', 'نامشخص')
        
        # تبدیل نام‌های انگلیسی به فارسی
        if data_plan == '30GB':
            data_plan_fa = '30 گیگابایت'
        elif data_plan == '50GB':
            data_plan_fa = '50 گیگابایت'
        elif data_plan == '70GB':
            data_plan_fa = '70 گیگابایت'
        elif data_plan == '100GB':
            data_plan_fa = '100 گیگابایت'
        elif data_plan == '150GB':
            data_plan_fa = '150 گیگابایت'
        else:
            data_plan_fa = data_plan
        
        if duration == '1month':
            duration_fa = '1 ماهه'
        else:
            duration_fa = duration
        
        configs_info += f"📦 سفارش {i}:\n"
        configs_info += f"👤 نام کاربری: `{username}`\n"
        configs_info += f"📊 حجم: {data_plan_fa}\n"
        configs_info += f"⏱ مدت: {duration_fa}\n"
        configs_info += f"💰 قیمت: {price:,} تومان\n"
        configs_info += f"📅 تاریخ: {order_time}\n"
        configs_info += f"🔐 کانفیگ: در دسترس\n\n"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📥 دانلود کانفیگ')
    btn2 = types.KeyboardButton('📋 اطلاعات کامل')
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(btn1, btn2, back)
    
    bot.send_message(message.chat.id, 
                    configs_info + 
                    "💡 برای دانلود کانفیگ، روی دکمه '📥 دانلود کانفیگ' کلیک کنید.",
                    parse_mode="Markdown",
                    reply_markup=markup)

# پردازش پیام پشتیبانی
def process_support_message(message):
    user_id = message.from_user.id
    
    # بررسی مسدودیت کاربر
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    if message.text == '🔙 بازگشت':
        start(message)
        return
    
    # اطلاعات کاربر
    user_info = users_db.get(user_id, {})
    user_name = user_info.get('first_name', 'نامشخص')
    username = user_info.get('username', 'نامشخص')
    
    # ارسال پیام به ادمین
    try:
        # پاک کردن تمام کاراکترهای مشکل‌ساز از متن پیام
        import re
        clean_message = re.sub(r'[`*_\[\]()~>#+=|{}.!-]', '', message.text)
        
        support_msg = (
            f"📞 پیام پشتیبانی جدید:\n\n"
            f"👤 نام: {user_name}\n"
            f"🆔 آیدی: {user_id}\n"
            f"📝 یوزرنیم: @{username}\n"
            f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"💬 پیام:\n{clean_message}"
        )
        
        # ارسال به ادمین بدون parse_mode
        sent = bot.send_message(ADMIN_ID, support_msg)
        
        if sent:
            # تأیید ارسال به کاربر
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت')
            markup.add(back)
            
            bot.send_message(message.chat.id, 
                           "✅ پیام شما با موفقیت ارسال شد!\n\n"
                           "📞 همکاران ما در اسرع وقت به شما پاسخ خواهند داد.\n"
                           "🙏 از صبر و شکیبایی شما متشکریم.",
                           reply_markup=markup)
            
            print(f"Support message sent to admin from user {user_id}")
        else:
            bot.send_message(message.chat.id, 
                           "❌ خطا در ارسال پیام.\n"
                           "لطفا دوباره تلاش کنید.")
    
    except Exception as e:
        print(f"Error sending support message: {e}")
        bot.send_message(message.chat.id, 
                        "❌ خطا در ارسال پیام به پشتیبانی.\n"
                        "لطفا با ادمین تماس بگیرید.")

# نمایش پنل مدیریت
def show_admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('👥 مدیریت کاربران')
    btn2 = types.KeyboardButton('📊 آمار ربات')
    btn3 = types.KeyboardButton('🔐 مدیریت کانفیگ‌ها')
    btn4 = types.KeyboardButton('📢 پیام همگانی')
    btn5 = types.KeyboardButton('💰 مدیریت تخفیف')
    btn6 = types.KeyboardButton('🚫 مدیریت مسدودیت')
    btn7 = types.KeyboardButton('📞 پیام‌های پشتیبانی')
    btn8 = types.KeyboardButton('🔄 تست ارسال به ادمین')
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, back)
    
    bot.send_message(message.chat.id, 
                     "⚙️ پنل مدیریت:\n\n"
                     f"🆔 آیدی عددی ادمین: `{ADMIN_ID}`\n"
                     f"👤 یوزرنیم ادمین: {ADMIN_USERNAME}\n"
                     f"💳 شماره کارت: `{CARD_NUMBER}`\n"
                     f"👥 تعداد کاربران: {len(users_db)}\n"
                     f"🚫 کاربران مسدود: {len(blocked_users)}\n"
                     f"💰 تخفیف فعلی: {discount_percentage}%",
                     parse_mode="Markdown",
                     reply_markup=markup)

# مدیریت کاربران
@bot.message_handler(func=lambda message: message.text == '👥 مدیریت کاربران')
def manage_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📋 لیست کاربران')
    btn2 = types.KeyboardButton('🔍 جستجوی کاربر')
    btn3 = types.KeyboardButton('📊 آمار کاربران')
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(btn1, btn2, btn3, back)
    
    bot.send_message(message.chat.id, 
                     "👥 مدیریت کاربران:\n\n"
                     f"📊 تعداد کل کاربران: {len(users_db)}\n"
                     f"🚫 کاربران مسدود: {len(blocked_users)}\n"
                     f"✅ کاربران فعال: {len(users_db) - len(blocked_users)}",
                     reply_markup=markup)

# لیست کاربران
@bot.message_handler(func=lambda message: message.text == '📋 لیست کاربران')
def list_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if not users_db:
        bot.send_message(message.chat.id, "📭 هیچ کاربری ثبت نشده است.")
        return
    
    user_list = "📋 لیست کاربران:\n\n"
    for i, (user_id, user_data) in enumerate(list(users_db.items())[:20], 1):  # حداکثر 20 کاربر
        status = "🚫 مسدود" if user_id in blocked_users else "✅ فعال"
        user_list += f"{i}. آیدی: `{user_id}` | {status}\n"
        user_list += f"   نام: {user_data.get('first_name', 'نامشخص')}\n"
        user_list += f"   سفارشات: {len(user_data.get('orders', []))}\n\n"
    
    if len(users_db) > 20:
        user_list += f"... و {len(users_db) - 20} کاربر دیگر"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, user_list, parse_mode="Markdown", reply_markup=markup)

# مدیریت کانفیگ‌ها
@bot.message_handler(func=lambda message: message.text == '🔐 مدیریت کانفیگ‌ها')
def manage_configs(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📁 آپلود کانفیگ')
    btn2 = types.KeyboardButton('📋 لیست کانفیگ‌ها')
    btn3 = types.KeyboardButton('🗑️ حذف کانفیگ')
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(btn1, btn2, btn3, back)
    
    bot.send_message(message.chat.id, 
                     "🔐 مدیریت کانفیگ‌ها:\n\n"
                     f"📁 تعداد کانفیگ‌ها: {len(configs_db)}\n"
                     "برای آپلود کانفیگ جدید، فایل را ارسال کنید.",
                     reply_markup=markup)

# آپلود کانفیگ
@bot.message_handler(content_types=['document'], func=lambda message: message.from_user.id == ADMIN_ID)
def upload_config(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    file_id = message.document.file_id
    file_name = message.document.file_name
    config_id = f"config_{len(configs_db) + 1}"
    
    configs_db[config_id] = {
        'file_id': file_id,
        'file_name': file_name,
        'upload_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'uploader_id': message.from_user.id
    }
    save_data()  # ذخیره تغییرات
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     f"✅ کانفیگ با موفقیت آپلود شد!\n\n"
                     f"🆔 شناسه: `{config_id}`\n"
                     f"📁 نام فایل: {file_name}\n"
                     f"📅 تاریخ آپلود: {configs_db[config_id]['upload_date']}",
                     parse_mode="Markdown",
                     reply_markup=markup)

# پیام همگانی
@bot.message_handler(func=lambda message: message.text == '📢 پیام همگانی')
def broadcast_message_menu(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     "📢 ارسال پیام همگانی:\n\n"
                     "لطفا پیام خود را ارسال کنید تا برای تمام کاربران ارسال شود.\n"
                     "برای لغو، گزینه بازگشت را انتخاب کنید.",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_broadcast_message)

# پردازش پیام همگانی
def process_broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔙 بازگشت به پنل':
        show_admin_panel(message)
        return
    
    # ارسال پیام به تمام کاربران
    success_count = 0
    failed_count = 0
    
    for user_id in users_db.keys():
        if user_id not in blocked_users:
            try:
                bot.send_message(user_id, 
                               f"📢 پیام همگانی از ادمین:\n\n{message.text}")
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to send broadcast to {user_id}: {e}")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     f"📢 پیام همگانی ارسال شد!\n\n"
                     f"✅ موفق: {success_count}\n"
                     f"❌ ناموفق: {failed_count}\n"
                     f"📊 کل کاربران: {len(users_db) - len(blocked_users)}",
                     reply_markup=markup)

# مدیریت تخفیف
@bot.message_handler(func=lambda message: message.text == '💰 مدیریت تخفیف')
def manage_discount(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('➕ افزایش تخفیف')
    btn2 = types.KeyboardButton('➖ کاهش تخفیف')
    btn3 = types.KeyboardButton('❌ حذف تخفیف')
    btn4 = types.KeyboardButton('📊 وضعیت تخفیف')
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(btn1, btn2, btn3, btn4, back)
    
    bot.send_message(message.chat.id, 
                     f"💰 مدیریت تخفیف:\n\n"
                     f"🎯 تخفیف فعلی: {discount_percentage}%\n"
                     f"💡 برای تغییر تخفیف، یکی از گزینه‌ها را انتخاب کنید.",
                     reply_markup=markup)

# افزایش تخفیف
@bot.message_handler(func=lambda message: message.text == '➕ افزایش تخفیف')
def increase_discount(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     "➕ افزایش تخفیف:\n\n"
                     "لطفا درصد تخفیف جدید را وارد کنید (مثلاً: 10 برای 10% تخفیف):",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_discount_change, 'increase')

# کاهش تخفیف
@bot.message_handler(func=lambda message: message.text == '➖ کاهش تخفیف')
def decrease_discount(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     "➖ کاهش تخفیف:\n\n"
                     "لطفا درصد تخفیف جدید را وارد کنید (مثلاً: 5 برای 5% تخفیف):",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_discount_change, 'decrease')

# پردازش تغییر تخفیف
def process_discount_change(message, action):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔙 بازگشت':
        manage_discount(message)
        return
    
    try:
        new_discount = int(message.text)
        if 0 <= new_discount <= 100:
            global discount_percentage
            discount_percentage = new_discount
            save_data()  # ذخیره تغییرات
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت به پنل')
            markup.add(back)
            
            bot.send_message(message.chat.id, 
                           f"✅ تخفیف با موفقیت تغییر یافت!\n\n"
                           f"🎯 تخفیف جدید: {discount_percentage}%\n"
                           f"💰 این تخفیف روی تمام سفارشات اعمال می‌شود.",
                           reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ درصد تخفیف باید بین 0 تا 100 باشد.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفا یک عدد معتبر وارد کنید.")

# مدیریت مسدودیت
@bot.message_handler(func=lambda message: message.text == '🚫 مدیریت مسدودیت')
def manage_blocked_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🚫 مسدود کردن کاربر')
    btn2 = types.KeyboardButton('✅ آزاد کردن کاربر')
    btn3 = types.KeyboardButton('📋 لیست مسدودها')
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(btn1, btn2, btn3, back)
    
    bot.send_message(message.chat.id, 
                     "🚫 مدیریت مسدودیت:\n\n"
                     f"🚫 کاربران مسدود: {len(blocked_users)}\n"
                     f"✅ کاربران آزاد: {len(users_db) - len(blocked_users)}",
                     reply_markup=markup)

# مسدود کردن کاربر
@bot.message_handler(func=lambda message: message.text == '🚫 مسدود کردن کاربر')
def block_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     "🚫 مسدود کردن کاربر:\n\n"
                     "لطفا آیدی عددی کاربری که می‌خواهید مسدود کنید را وارد کنید:",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_block_user)

# پردازش مسدود کردن کاربر
def process_block_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔙 بازگشت':
        manage_blocked_users(message)
        return
    
    try:
        user_id = int(message.text)
        if user_id in users_db:
            blocked_users.add(user_id)
            save_data()  # ذخیره تغییرات
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت به پنل')
            markup.add(back)
            
            bot.send_message(message.chat.id, 
                           f"✅ کاربر با آیدی `{user_id}` با موفقیت مسدود شد!",
                           parse_mode="Markdown",
                           reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ کاربر با این آیدی یافت نشد.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفا یک آیدی معتبر وارد کنید.")

# آزاد کردن کاربر
@bot.message_handler(func=lambda message: message.text == '✅ آزاد کردن کاربر')
def unblock_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     "✅ آزاد کردن کاربر:\n\n"
                     "لطفا آیدی عددی کاربری که می‌خواهید آزاد کنید را وارد کنید:",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_unblock_user)

# پردازش آزاد کردن کاربر
def process_unblock_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔙 بازگشت':
        manage_blocked_users(message)
        return
    
    try:
        user_id = int(message.text)
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            save_data()  # ذخیره تغییرات
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت به پنل')
            markup.add(back)
            
            bot.send_message(message.chat.id, 
                           f"✅ کاربر با آیدی `{user_id}` با موفقیت آزاد شد!",
                           parse_mode="Markdown",
                           reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ این کاربر مسدود نیست.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفا یک آیدی معتبر وارد کنید.")

# آمار ربات
@bot.message_handler(func=lambda message: message.text == '📊 آمار ربات')
def bot_statistics(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    total_orders = sum(len(user.get('orders', [])) for user in users_db.values())
    total_revenue = sum(user.get('total_spent', 0) for user in users_db.values())
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     f"📊 آمار ربات:\n\n"
                     f"👥 تعداد کاربران: {len(users_db)}\n"
                     f"🚫 کاربران مسدود: {len(blocked_users)}\n"
                     f"✅ کاربران فعال: {len(users_db) - len(blocked_users)}\n"
                     f"📦 کل سفارشات: {total_orders}\n"
                     f"💰 کل درآمد: {total_revenue:,} تومان\n"
                     f"🎯 تخفیف فعلی: {discount_percentage}%",
                     reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🔄 تست ارسال به ادمین')
def test_admin_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        # ارسال پیام تست به ادمین
        test_msg = f"🔔 این یک پیام تست است.\n\n" \
                  f"🕒 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                  f"✅ اگر این پیام را دریافت کرده‌اید، تنظیمات ادمین صحیح است."
        
        sent_msg = bot.send_message(ADMIN_ID, test_msg)
        
        if sent_msg:
            bot.send_message(message.chat.id, 
                            "✅ پیام تست با موفقیت ارسال شد.\n\n"
                            f"پیام به آیدی {ADMIN_ID} ارسال شد.")
            print(f"Test message sent to admin ID: {ADMIN_ID}")
        else:
            bot.send_message(message.chat.id, "❌ خطا در ارسال پیام تست.")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال پیام تست: {str(e)}")
        print(f"Error sending test message to admin: {e}")

# نمایش پلن‌های حجمی
def show_data_plans(message):
    user_id = message.from_user.id
    
    # بررسی مسدودیت کاربر
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    # ایجاد حافظه موقت برای کاربر اگر وجود نداشته باشد
    if user_id not in user_data:
        user_data[user_id] = {}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn1 = types.KeyboardButton('30 گیگابایت')
    btn2 = types.KeyboardButton('50 گیگابایت')
    btn3 = types.KeyboardButton('70 گیگابایت')
    btn4 = types.KeyboardButton('100 گیگابایت')
    btn5 = types.KeyboardButton('150 گیگابایت')
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(btn1, btn2, btn3, btn4, btn5, back)
    
    bot.send_message(message.chat.id, 
                     "🔄 لطفا حجم مورد نظر خود را انتخاب کنید:", 
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_data_plan)

# پردازش انتخاب حجم
def process_data_plan(message):
    if message.text == '🔙 بازگشت':
        start(message)
        return
    
    user_id = message.from_user.id
    
    if message.text not in ['30 گیگابایت', '50 گیگابایت', '70 گیگابایت', '100 گیگابایت', '150 گیگابایت']:
        bot.send_message(message.chat.id, "❌ لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        show_data_plans(message)
        return
    
    # ذخیره حجم انتخاب شده
    if message.text == '30 گیگابایت':
        user_data[user_id]['data_plan'] = '30GB'
    elif message.text == '50 گیگابایت':
        user_data[user_id]['data_plan'] = '50GB'
    elif message.text == '70 گیگابایت':
        user_data[user_id]['data_plan'] = '70GB'
    elif message.text == '100 گیگابایت':
        user_data[user_id]['data_plan'] = '100GB'
    elif message.text == '150 گیگابایت':
        user_data[user_id]['data_plan'] = '150GB'
    
    # نمایش زمان‌های اشتراک
    show_duration_plans(message)

# نمایش پلن‌های زمانی
def show_duration_plans(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn1 = types.KeyboardButton('1 ماهه')
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(btn1, back)
    
    bot.send_message(message.chat.id, 
                     "⏱ لطفا مدت زمان اشتراک را انتخاب کنید:", 
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_duration_plan)

# پردازش انتخاب مدت زمان
def process_duration_plan(message):
    if message.text == '🔙 بازگشت':
        show_data_plans(message)
        return
    
    user_id = message.from_user.id
    
    if message.text not in ['1 ماهه']:
        bot.send_message(message.chat.id, "❌ لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        show_duration_plans(message)
        return
    
    # ذخیره زمان انتخاب شده
    if message.text == '1 ماهه':
        user_data[user_id]['duration'] = '1month'
    
    # درخواست نام کاربری
    ask_username(message)

# درخواست نام کاربری
def ask_username(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                     "👤 لطفا نام کاربری دلخواه خود را وارد کنید:\n"
                     "(فقط از حروف انگلیسی و اعداد استفاده کنید)", 
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_username)

# پردازش نام کاربری
def process_username(message):
    if message.text == '🔙 بازگشت':
        show_duration_plans(message)
        return
    
    user_id = message.from_user.id
    username = message.text.strip()
    
    # بررسی معتبر بودن نام کاربری
    if not username.isalnum():
        bot.send_message(message.chat.id, "❌ نام کاربری فقط می‌تواند شامل حروف انگلیسی و اعداد باشد.")
        ask_username(message)
        return
    
    # ذخیره نام کاربری
    user_data[user_id]['username'] = username
    
    # محاسبه و نمایش قیمت نهایی
    show_final_price(message)

# محاسبه و نمایش قیمت نهایی
def show_final_price(message):
    user_id = message.from_user.id
    data_plan = user_data[user_id]['data_plan']
    duration = user_data[user_id]['duration']
    username = user_data[user_id]['username']
    
    # محاسبه قیمت
    base_price = prices[data_plan][duration]
    
    # اعمال تخفیف
    if discount_percentage > 0:
        discount_amount = (base_price * discount_percentage) // 100
        final_price = base_price - discount_amount
    else:
        final_price = base_price
        discount_amount = 0
    
    user_data[user_id]['price'] = final_price
    user_data[user_id]['base_price'] = base_price
    user_data[user_id]['discount_amount'] = discount_amount
    
    # تبدیل کدهای داخلی به متن قابل نمایش
    data_text = data_plan.replace('GB', ' گیگابایت')
    duration_text = duration.replace('month', ' ماهه')
    if duration == '1month':
        duration_text = '1 ماهه'
    
    # نمایش خلاصه سفارش
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    confirm = types.KeyboardButton('✅ تأیید و پرداخت')
    cancel = types.KeyboardButton('❌ انصراف')
    markup.add(confirm, cancel)
    
    price_text = f"🧾 خلاصه سفارش شما:\n\n"
    price_text += f"حجم: {data_text}\n"
    price_text += f"مدت: {duration_text}\n"
    price_text += f"نام کاربری: {username}\n\n"
    
    if discount_percentage > 0:
        price_text += f"💰 قیمت اصلی: {base_price:,} تومان\n"
        price_text += f"🎯 تخفیف: {discount_percentage}% ({discount_amount:,} تومان)\n"
        price_text += f"💳 مبلغ قابل پرداخت: {final_price:,} تومان\n\n"
    else:
        price_text += f"💳 مبلغ قابل پرداخت: {final_price:,} تومان\n\n"
    
    price_text += f"در صورت تأیید، گزینه «تأیید و پرداخت» را انتخاب کنید."
    
    bot.send_message(message.chat.id, price_text, reply_markup=markup)
    bot.register_next_step_handler(message, process_payment_confirmation)

# پردازش تأیید پرداخت
def process_payment_confirmation(message):
    if message.text == '❌ انصراف':
        bot.send_message(message.chat.id, "❌ سفارش شما لغو شد.")
        start(message)
        return
    
    if message.text != '✅ تأیید و پرداخت':
        bot.send_message(message.chat.id, "❌ لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        # نمایش مجدد صفحه تأیید
        show_final_price(message)
        return
    
    # نمایش اطلاعات پرداخت
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    send_receipt = types.KeyboardButton('📝 ارسال رسید پرداخت')
    cancel = types.KeyboardButton('❌ انصراف')
    markup.add(send_receipt, cancel)
    
    bot.send_message(message.chat.id, 
                     f"💳 لطفا مبلغ {user_data[message.from_user.id]['price']:,} تومان را به شماره کارت زیر واریز کنید:\n\n"
                     f"`{CARD_NUMBER}`\n"
                     f"به نام: پاینده \n\n"
                     f"پس از پرداخت، گزینه «ارسال رسید پرداخت» را انتخاب کنید و تصویر رسید را ارسال نمایید.",
                     parse_mode="Markdown",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_receipt_option)

# پردازش انتخاب ارسال رسید
def process_receipt_option(message):
    if message.text == '❌ انصراف':
        bot.send_message(message.chat.id, "❌ سفارش شما لغو شد.")
        start(message)
        return
    
    if message.text != '📝 ارسال رسید پرداخت':
        bot.send_message(message.chat.id, "❌ لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        # بازگشت به مرحله قبل
        process_payment_confirmation(message)
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    cancel = types.KeyboardButton('❌ انصراف')
    markup.add(cancel)
    
    bot.send_message(message.chat.id, 
                     "🧾 لطفا تصویر رسید پرداخت خود را ارسال کنید.",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_receipt)

# پردازش رسید پرداخت
@bot.message_handler(content_types=['photo'])
def process_receipt(message):
    if hasattr(message, 'text') and message.text == '❌ انصراف':
        bot.send_message(message.chat.id, "❌ سفارش شما لغو شد.")
        start(message)
        return
    
    user_id = message.from_user.id
    
    # ذخیره اطلاعات رسید
    user_data[user_id]['receipt_id'] = message.id
    user_data[user_id]['order_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ثبت سفارش در دیتابیس کاربر
    if user_id in users_db:
        order_info = {
            'data_plan': user_data[user_id]['data_plan'],
            'duration': user_data[user_id]['duration'],
            'username': user_data[user_id]['username'],
            'price': user_data[user_id]['price'],
            'order_time': user_data[user_id]['order_time'],
            'receipt_id': user_data[user_id]['receipt_id']
        }
        users_db[user_id]['orders'].append(order_info)
        users_db[user_id]['total_spent'] += user_data[user_id]['price']
        save_data()  # ذخیره تغییرات
    
    # ارسال رسید به ادمین
    try:
        # فوروارد رسید به ادمین
        forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.id)
        print(f"Receipt forwarded to admin: {ADMIN_ID}, forward status: {forwarded != None}")
        
        # اطلاعات سفارش
        data_plan = user_data[user_id]['data_plan'].replace('GB', ' گیگابایت')
        duration = user_data[user_id]['duration']
        if duration == '1month':
            duration_text = '1 ماهه'
        
        username = user_data[user_id]['username']
        price = user_data[user_id]['price']
        base_price = user_data[user_id].get('base_price', price)
        discount_amount = user_data[user_id].get('discount_amount', 0)
        
        # ارسال اطلاعات سفارش به ادمین
        admin_msg = (
            f"🔔 سفارش جدید:\n\n"
            f"🆔 آیدی کاربر: `{user_id}`\n"
            f"👤 نام کاربری: `{username}`\n"
            f"📊 حجم: {data_plan}\n"
            f"⏱ مدت: {duration_text}\n"
        )
        
        if discount_percentage > 0:
            admin_msg += f"💰 قیمت اصلی: {base_price:,} تومان\n"
            admin_msg += f"🎯 تخفیف: {discount_percentage}% ({discount_amount:,} تومان)\n"
            admin_msg += f"💳 مبلغ نهایی: {price:,} تومان\n"
        else:
            admin_msg += f"💰 مبلغ: {price:,} تومان\n"
        
        admin_msg += f"🕒 زمان سفارش: {user_data[user_id]['order_time']}\n\n"
        admin_msg += f"برای ارسال کانفیگ از دستور زیر استفاده کنید:\n"
        admin_msg += f"`/send_config {user_id}`"
        
        sent = bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        print(f"Order info sent to admin: {ADMIN_ID}, send status: {sent != None}")
        
        # ارسال پیام تشکر به کاربر
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        home = types.KeyboardButton('🏠 بازگشت به منوی اصلی')
        markup.add(home)
        
        bot.send_message(message.chat.id, 
                        "✅ با تشکر از پرداخت شما!\n\n"
                        "رسید پرداخت شما با موفقیت دریافت شد و در حال بررسی است.\n"
                        "پس از تأیید پرداخت، فایل کانفیگ برای شما ارسال خواهد شد.\n\n"
                        "🙏 از صبر و شکیبایی شما متشکریم.",
                        reply_markup=markup)
    
    except Exception as e:
        print(f"Error sending receipt to admin: {e}")
        bot.send_message(message.chat.id, 
                        "❌ خطا در ارسال رسید به ادمین.\n"
                        "لطفا با پشتیبانی تماس بگیرید.")

# پاسخ به دکمه‌های مدیریت کاربران
@bot.message_handler(func=lambda message: message.text in ['🔍 جستجوی کاربر', '📊 آمار کاربران'])
def user_management_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔍 جستجوی کاربر':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back = types.KeyboardButton('🔙 بازگشت')
        markup.add(back)
        
        bot.send_message(message.chat.id, 
                        "🔍 جستجوی کاربر:\n\n"
                        "لطفا آیدی عددی کاربر را وارد کنید:",
                        reply_markup=markup)
        bot.register_next_step_handler(message, search_user)
    
    elif message.text == '📊 آمار کاربران':
        active_users = len(users_db) - len(blocked_users)
        total_orders = sum(len(user.get('orders', [])) for user in users_db.values())
        total_revenue = sum(user.get('total_spent', 0) for user in users_db.values())
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back = types.KeyboardButton('🔙 بازگشت')
        markup.add(back)
        
        bot.send_message(message.chat.id, 
                        f"📊 آمار کاربران:\n\n"
                        f"👥 کل کاربران: {len(users_db)}\n"
                        f"✅ کاربران فعال: {active_users}\n"
                        f"🚫 کاربران مسدود: {len(blocked_users)}\n"
                        f"📦 کل سفارشات: {total_orders}\n"
                        f"💰 کل درآمد: {total_revenue:,} تومان",
                        reply_markup=markup)

# جستجوی کاربر
def search_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔙 بازگشت':
        manage_users(message)
        return
    
    try:
        user_id = int(message.text)
        if user_id in users_db:
            user = users_db[user_id]
            status = "🚫 مسدود" if user_id in blocked_users else "✅ فعال"
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت')
            markup.add(back)
            
            bot.send_message(message.chat.id, 
                           f"👤 اطلاعات کاربر:\n\n"
                           f"🆔 آیدی: `{user_id}`\n"
                           f"👤 نام: {user.get('first_name', 'نامشخص')}\n"
                           f"📅 تاریخ عضویت: {user.get('join_date', 'نامشخص')}\n"
                           f"📦 تعداد سفارشات: {len(user.get('orders', []))}\n"
                           f"💰 کل هزینه: {user.get('total_spent', 0):,} تومان\n"
                           f"📊 وضعیت: {status}",
                           parse_mode="Markdown",
                           reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ کاربر با این آیدی یافت نشد.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفا یک آیدی معتبر وارد کنید.")

# پاسخ به دکمه‌های مدیریت کانفیگ‌ها
@bot.message_handler(func=lambda message: message.text in ['📋 لیست کانفیگ‌ها', '🗑 حذف کانفیگ'])
def config_management_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '📋 لیست کانفیگ‌ها':
        if not configs_db:
            bot.send_message(message.chat.id, "📭 هیچ کانفیگی آپلود نشده است.")
        else:
            config_list = "📋 لیست کانفیگ‌ها:\n\n"
            for i, (config_id, config_info) in enumerate(configs_db.items(), 1):
                config_list += f"{i}. {config_info['name']}\n"
                config_list += f"   آپلود شده در: {config_info['upload_date']}\n\n"
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت به پنل')
            markup.add(back)
            
            bot.send_message(message.chat.id, config_list, reply_markup=markup)
    
    elif message.text == '🗑 حذف کانفیگ':
        if not configs_db:
            bot.send_message(message.chat.id, "📭 هیچ کانفیگی برای حذف وجود ندارد.")
        else:
            config_list = "🗑 حذف کانفیگ:\n\n"
            for i, (config_id, config_info) in enumerate(configs_db.items(), 1):
                config_list += f"{i}. {config_info['name']}\n"
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت به پنل')
            markup.add(back)
            
            bot.send_message(message.chat.id, 
                           config_list + "\nلطفا شماره کانفیگی که می‌خواهید حذف کنید را وارد کنید:",
                           reply_markup=markup)
            bot.register_next_step_handler(message, process_delete_config)

# پردازش حذف کانفیگ
def process_delete_config(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔙 بازگشت به پنل':
        show_admin_panel(message)
        return
    
    try:
        config_index = int(message.text) - 1
        config_ids = list(configs_db.keys())
        
        if 0 <= config_index < len(config_ids):
            config_id = config_ids[config_index]
            config_name = configs_db[config_id]['name']
            del configs_db[config_id]
            save_data()  # ذخیره تغییرات
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back = types.KeyboardButton('🔙 بازگشت به پنل')
            markup.add(back)
            
            bot.send_message(message.chat.id, 
                           f"✅ کانفیگ '{config_name}' با موفقیت حذف شد!",
                           reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ شماره کانفیگ نامعتبر است.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفا یک شماره معتبر وارد کنید.")

# پاسخ به دکمه بازگشت به منوی اصلی
@bot.message_handler(func=lambda message: message.text == '🏠 بازگشت به منوی اصلی')
def back_to_home(message):
    start(message)

# پاسخ به دکمه‌های بازگشت عمومی
@bot.message_handler(func=lambda message: message.text in ['🔙 بازگشت'])
def general_back_handler(message):
    if message.text == '🔙 بازگشت':
        # بازگشت به منوی اصلی
        start(message)

# پاسخ به دکمه‌های بازگشت در بخش‌های مختلف پنل مدیریت
@bot.message_handler(func=lambda message: message.text in ['🔙 بازگشت به پنل'])
def admin_back_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '🔙 بازگشت به پنل':
        show_admin_panel(message)

# دستور ارسال کانفیگ توسط ادمین
@bot.message_handler(commands=['send_config'])
def send_config_command(message):
    user_id = message.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔️ شما دسترسی به این دستور را ندارید.")
        print(f"Unauthorized access to send_config: User ID {user_id}, Admin ID {ADMIN_ID}")
        return
    
    # بررسی فرمت دستور
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.send_message(message.chat.id, "❌ فرمت صحیح: `/send_config [chat_id]`", parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(command_parts[1])
        
        # درخواست فایل کانفیگ
        bot.send_message(message.chat.id, 
                         f"📁 لطفا فایل کانفیگ برای کاربر `{target_user_id}` را ارسال کنید:",
                         parse_mode="Markdown")
        
        # ثبت مرحله بعدی
        bot.register_next_step_handler(message, lambda msg: process_config_file(msg, target_user_id))
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ شناسه کاربر باید عددی باشد.")

# پردازش فایل کانفیگ ارسالی توسط ادمین
def process_config_file(message, target_user_id):
    # بررسی دسترسی ادمین
    if message.from_user.id != ADMIN_ID:
        print(f"Unauthorized access to process_config_file: User ID {message.from_user.id}, Admin ID {ADMIN_ID}")
        return
    
    # بررسی نوع پیام
    if message.content_type not in ['document', 'text']:
        bot.send_message(message.chat.id, "❌ لطفا یک فایل یا متن کانفیگ ارسال کنید.")
        return
    
    try:
        # ارسال کانفیگ به کاربر
        if message.content_type == 'document':
            file_id = message.document.file_id
            caption = "🔐 فایل کانفیگ فیلترشکن شما\n\nبا تشکر از خرید شما"
            
            # ارسال فایل به کاربر
            sent = bot.send_document(target_user_id, file_id, caption=caption)
            print(f"Config file sent to user {target_user_id}, status: {sent != None}")
            
            # تأیید ارسال به ادمین
            bot.send_message(ADMIN_ID, f"✅ فایل کانفیگ با موفقیت به کاربر `{target_user_id}` ارسال شد.", parse_mode="Markdown")
            
        elif message.content_type == 'text':
            config_text = message.text
            
            # ارسال متن کانفیگ به کاربر
            sent = bot.send_message(target_user_id, 
                             f"🔐 کانفیگ فیلترشکن شما:\n\n`{config_text}`\n\nبا تشکر از خرید شما",
                             parse_mode="Markdown")
            print(f"Config text sent to user {target_user_id}, status: {sent != None}")
            
            # تأیید ارسال به ادمین
            bot.send_message(ADMIN_ID, f"✅ متن کانفیگ با موفقیت به کاربر `{target_user_id}` ارسال شد.", parse_mode="Markdown")
    
    except Exception as e:
        error_msg = f"❌ خطا در ارسال کانفیگ: {str(e)}"
        bot.send_message(ADMIN_ID, error_msg)
        print(error_msg)

# دستور برای تنظیم آیدی ادمین
@bot.message_handler(commands=['setadmin'])
def set_admin_command(message):
    # فقط ادمین فعلی می‌تواند ادمین جدید تعیین کند
    if message.from_user.id != ADMIN_ID:
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.send_message(message.chat.id, "❌ فرمت صحیح: `/setadmin [chat_id]`", parse_mode="Markdown")
        return
    
    try:
        new_admin_id = int(command_parts[1])
        bot.send_message(message.chat.id, 
                        f"⚠️ برای تغییر آیدی ادمین، کد زیر را در فایل vpn_bot.py تغییر دهید:\n\n"
                        f"`ADMIN_ID = {new_admin_id}`")
    except ValueError:
        bot.send_message(message.chat.id, "❌ آیدی ادمین باید عددی باشد.")

# دستور ذخیره دستی داده‌ها
@bot.message_handler(commands=['save'])
def save_data_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        save_data()
        bot.send_message(message.chat.id, "✅ داده‌ها با موفقیت ذخیره شدند.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ذخیره داده‌ها: {e}")

# دستور بارگذاری مجدد داده‌ها
@bot.message_handler(commands=['load'])
def load_data_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        load_data()
        bot.send_message(message.chat.id, "✅ داده‌ها با موفقیت بارگذاری شدند.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در بارگذاری داده‌ها: {e}")

# دستور نمایش آمار داده‌ها
@bot.message_handler(commands=['stats'])
def data_stats_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    stats_msg = f"📊 آمار داده‌ها:\n\n"
    stats_msg += f"👥 کاربران: {len(users_db)}\n"
    stats_msg += f"🚫 مسدودها: {len(blocked_users)}\n"
    stats_msg += f"🔐 کانفیگ‌ها: {len(configs_db)}\n"
    stats_msg += f"💰 تخفیف: {discount_percentage}%\n"
    stats_msg += f"📦 سفارشات: {len(orders_db)}\n\n"
    
    # بررسی فایل‌های ذخیره‌سازی
    for name, filename in DATA_FILES.items():
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            stats_msg += f"📁 {name}: {file_size} bytes\n"
        else:
            stats_msg += f"❌ {name}: فایل وجود ندارد\n"
    
    bot.send_message(message.chat.id, stats_msg)

# دستور پاسخ به پیام پشتیبانی
@bot.message_handler(commands=['reply'])
def reply_support_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    command_parts = message.text.split(maxsplit=2)
    if len(command_parts) != 3:
        bot.send_message(message.chat.id, 
                        "❌ فرمت صحیح: `/reply [user_id] [پیام پاسخ]`\n\n"
                        "مثال:\n"
                        "`/reply 123456789 سلام، مشکل شما حل شد`",
                        parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(command_parts[1])
        reply_text = command_parts[2]
        
        # ارسال پاسخ به کاربر
        try:
            reply_msg = (
                f"📞 پاسخ پشتیبانی:\n\n"
                f"💬 {reply_text}\n\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"👨‍💼 پشتیبانی AzizVPN"
            )
            
            sent = bot.send_message(target_user_id, reply_msg)
            
            if sent:
                # تأیید ارسال به ادمین
                bot.send_message(ADMIN_ID, 
                               f"✅ پاسخ با موفقیت به کاربر `{target_user_id}` ارسال شد.\n\n"
                               f"💬 پاسخ:\n{reply_text}",
                               parse_mode="Markdown")
                print(f"Support reply sent to user {target_user_id}")
            else:
                bot.send_message(ADMIN_ID, 
                               f"❌ خطا در ارسال پاسخ به کاربر `{target_user_id}`")
        
        except Exception as e:
            bot.send_message(ADMIN_ID, 
                           f"❌ خطا در ارسال پاسخ: {str(e)}")
            print(f"Error sending support reply: {e}")
    
    except ValueError:
        bot.send_message(message.chat.id, "❌ آیدی کاربر باید عددی باشد.")

# دستور مشاهده پیام‌های پشتیبانی اخیر
@bot.message_handler(commands=['support'])
def support_messages_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    bot.send_message(message.chat.id, 
                    "📞 برای مشاهده پیام‌های پشتیبانی، لطفا از دستور زیر استفاده کنید:\n\n"
                    "`/reply [user_id] [پیام پاسخ]`\n\n"
                    "مثال:\n"
                    "`/reply 123456789 سلام، مشکل شما حل شد`\n\n"
                    "💡 پیام‌های پشتیبانی به صورت مستقیم به شما ارسال می‌شوند.",
                    parse_mode="Markdown")

# نمایش اطلاعات پیام‌های پشتیبانی
def show_support_info(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(back)
    
    support_info = (
        "📞 مدیریت پیام‌های پشتیبانی:\n\n"
        "💡 پیام‌های پشتیبانی به صورت مستقیم به شما ارسال می‌شوند.\n\n"
        "📝 دستورات موجود:\n"
        "• `/reply [user_id] [پیام پاسخ]` - پاسخ به کاربر\n"
        "• `/support` - راهنمای دستورات\n\n"
        "📋 مثال:\n"
        "`/reply 123456789 سلام، مشکل شما حل شد`\n\n"
        "⚠️ توجه: آیدی کاربر از پیام‌های پشتیبانی قابل مشاهده است."
    )
    
    bot.send_message(message.chat.id, support_info, parse_mode="Markdown", reply_markup=markup)

# پاسخ به دکمه‌های کانفیگ کاربر
@bot.message_handler(func=lambda message: message.text in ['📥 دانلود کانفیگ', '📋 اطلاعات کامل'])
def user_config_buttons_handler(message):
    user_id = message.from_user.id
    
    if message.text == '📥 دانلود کانفیگ':
        show_download_options(message)
    elif message.text == '📋 اطلاعات کامل':
        show_detailed_config_info(message)

# پاسخ به دکمه‌های دانلود کانفیگ
@bot.message_handler(func=lambda message: message.text in ['📄 دانلود فایل', '📋 کپی متن'])
def config_download_buttons_handler(message):
    user_id = message.from_user.id
    
    if message.text == '📄 دانلود فایل':
        download_config_file(message)
    elif message.text == '📋 کپی متن':
        copy_config_text(message)

# دانلود فایل کانفیگ
def download_config_file(message):
    user_id = message.from_user.id
    
    if user_id not in user_data or 'current_config' not in user_data[user_id]:
        bot.send_message(message.chat.id, "❌ کانفیگی برای دانلود یافت نشد.")
        return
    
    config_data = user_data[user_id]['current_config']
    username = config_data['username']
    data_plan = config_data['data_plan']
    
    # تولید کانفیگ خالص
    pure_config = generate_pure_vless_config(username, data_plan, "1month")
    filename = config_data['filename']
    
    try:
        # ایجاد فایل موقت
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(pure_config)
            temp_file_path = temp_file.name
        
        # ارسال فایل
        with open(temp_file_path, 'rb') as file:
            bot.send_document(
                message.chat.id,
                file,
                caption=f"🔐 کانفیگ AzizVPN\n\n"
                       f"👤 نام کاربری: {username}\n"
                       f"📊 حجم: {data_plan}\n"
                       f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                       f"💡 این کانفیگ را در نرم‌افزار V2rayNG استفاده کنید.",
                filename=filename
            )
        
        # حذف فایل موقت
        os.unlink(temp_file_path)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back = types.KeyboardButton('🔙 بازگشت')
        markup.add(back)
        
        bot.send_message(message.chat.id, 
                        "✅ فایل کانفیگ با موفقیت دانلود شد!\n\n"
                        "📱 برای استفاده:\n"
                        "1. فایل را در نرم‌افزار V2rayNG باز کنید\n"
                        "2. روی دکمه 'Start' کلیک کنید\n"
                        "3. از فیلترشکن لذت ببرید!",
                        reply_markup=markup)
        
    except Exception as e:
        print(f"Error downloading config file: {e}")
        bot.send_message(message.chat.id, 
                        "❌ خطا در دانلود فایل کانفیگ.\n"
                        "لطفا دوباره تلاش کنید.")

# کپی متن کانفیگ
def copy_config_text(message):
    user_id = message.from_user.id
    
    if user_id not in user_data or 'current_config' not in user_data[user_id]:
        bot.send_message(message.chat.id, "❌ کانفیگی برای کپی یافت نشد.")
        return
    
    config_data = user_data[user_id]['current_config']
    username = config_data['username']
    data_plan = config_data['data_plan']
    
    # تولید کانفیگ خالص
    pure_config = generate_pure_vless_config(username, data_plan, "1month")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                    "📋 کانفیگ برای کپی:\n\n"
                    f"`{pure_config}`\n\n"
                    "💡 این کانفیگ را کپی کرده و در نرم‌افزار V2rayNG استفاده کنید.",
                    parse_mode="Markdown",
                    reply_markup=markup)

# نمایش گزینه‌های دانلود
def show_download_options(message):
    user_id = message.from_user.id
    
    if user_id not in users_db:
        bot.send_message(message.chat.id, "❌ ابتدا باید در ربات ثبت نام کنید.")
        return
    
    user = users_db[user_id]
    orders = user.get('orders', [])
    
    if not orders:
        bot.send_message(message.chat.id, "❌ شما هیچ کانفیگی برای دانلود ندارید.")
        return
    
    # ایجاد دکمه‌ها برای هر سفارش
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    
    for i, order in enumerate(orders, 1):
        username = order.get('username', 'نامشخص')
        data_plan = order.get('data_plan', 'نامشخص')
        duration = order.get('duration', 'نامشخص')
        
        # تبدیل نام‌های انگلیسی به فارسی
        if data_plan == '30GB':
            data_plan_fa = '30 گیگابایت'
        elif data_plan == '50GB':
            data_plan_fa = '50 گیگابایت'
        elif data_plan == '70GB':
            data_plan_fa = '70 گیگابایت'
        elif data_plan == '100GB':
            data_plan_fa = '100 گیگابایت'
        elif data_plan == '150GB':
            data_plan_fa = '150 گیگابایت'
        else:
            data_plan_fa = data_plan
        
        if duration == '1month':
            duration_fa = '1 ماهه'
        else:
            duration_fa = duration
        
        btn_text = f"📥 {username} - {data_plan_fa} - {duration_fa}"
        markup.add(types.KeyboardButton(btn_text))
    
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, 
                    "📥 دانلود کانفیگ:\n\n"
                    "لطفا کانفیگی که می‌خواهید دانلود کنید را انتخاب کنید:",
                    reply_markup=markup)
    bot.register_next_step_handler(message, process_config_download)

# پردازش دانلود کانفیگ
def process_config_download(message):
    user_id = message.from_user.id
    
    if message.text == '🔙 بازگشت':
        show_user_configs(message)
        return
    
    if user_id not in users_db:
        bot.send_message(message.chat.id, "❌ ابتدا باید در ربات ثبت نام کنید.")
        return
    
    user = users_db[user_id]
    orders = user.get('orders', [])
    
    if not orders:
        bot.send_message(message.chat.id, "❌ شما هیچ کانفیگی برای دانلود ندارید.")
        return
    
    # پیدا کردن سفارش انتخاب شده
    selected_order = None
    for i, order in enumerate(orders, 1):
        username = order.get('username', 'نامشخص')
        data_plan = order.get('data_plan', 'نامشخص')
        duration = order.get('duration', 'نامشخص')
        
        # تبدیل نام‌های انگلیسی به فارسی
        if data_plan == '30GB':
            data_plan_fa = '30 گیگابایت'
        elif data_plan == '50GB':
            data_plan_fa = '50 گیگابایت'
        elif data_plan == '70GB':
            data_plan_fa = '70 گیگابایت'
        elif data_plan == '100GB':
            data_plan_fa = '100 گیگابایت'
        elif data_plan == '150GB':
            data_plan_fa = '150 گیگابایت'
        else:
            data_plan_fa = data_plan
        
        if duration == '1month':
            duration_fa = '1 ماهه'
        else:
            duration_fa = duration
        
        btn_text = f"📥 {username} - {data_plan_fa} - {duration_fa}"
        
        if message.text == btn_text:
            selected_order = order
            break
    
    if not selected_order:
        bot.send_message(message.chat.id, "❌ کانفیگ انتخاب شده یافت نشد.")
        show_download_options(message)
        return
    
    # نمایش اطلاعات کانفیگ و گزینه دانلود
    username = selected_order.get('username', 'نامشخص')
    data_plan = selected_order.get('data_plan', 'نامشخص')
    duration = selected_order.get('duration', 'نامشخص')
    price = selected_order.get('price', 0)
    order_time = selected_order.get('order_time', 'نامشخص')
    
    # ایجاد کانفیگ بر اساس اطلاعات سفارش
    config_content = generate_config_content(username, data_plan, duration)
    
    config_info = (
        f"🔐 کانفیگ انتخاب شده:\n\n"
        f"👤 نام کاربری: `{username}`\n"
        f"📊 حجم: {data_plan}\n"
        f"⏱ مدت: {duration}\n"
        f"💰 قیمت: {price:,} تومان\n"
        f"📅 تاریخ خرید: {order_time}\n\n"
        f"📥 کانفیگ شما:\n"
        f"```\n{config_content}\n```\n\n"
        f"💡 این کانفیگ مخصوص شما است و فقط برای استفاده شخصی می‌باشد."
    )
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📄 دانلود فایل')
    btn2 = types.KeyboardButton('📋 کپی متن')
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(btn1, btn2, back)
    
    # ذخیره کانفیگ در حافظه موقت برای دانلود
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['current_config'] = {
        'content': config_content,
        'filename': f"AzizVPN_{username}_{data_plan}.txt",
        'username': username,
        'data_plan': data_plan
    }
    
    bot.send_message(message.chat.id, config_info, parse_mode="Markdown", reply_markup=markup)

# نمایش اطلاعات کامل کانفیگ
def show_detailed_config_info(message):
    user_id = message.from_user.id
    
    if user_id not in users_db:
        bot.send_message(message.chat.id, "❌ ابتدا باید در ربات ثبت نام کنید.")
        return
    
    user = users_db[user_id]
    orders = user.get('orders', [])
    
    if not orders:
        bot.send_message(message.chat.id, "❌ شما هیچ کانفیگی ندارید.")
        return
    
    detailed_info = "📋 اطلاعات کامل کانفیگ‌های شما:\n\n"
    
    total_spent = 0
    total_orders = len(orders)
    
    for i, order in enumerate(orders, 1):
        username = order.get('username', 'نامشخص')
        data_plan = order.get('data_plan', 'نامشخص')
        duration = order.get('duration', 'نامشخص')
        price = order.get('price', 0)
        order_time = order.get('order_time', 'نامشخص')
        receipt_id = order.get('receipt_id', 'نامشخص')
        
        total_spent += price
        
        detailed_info += f"📦 سفارش {i}:\n"
        detailed_info += f"   👤 نام کاربری: `{username}`\n"
        detailed_info += f"   📊 حجم: {data_plan}\n"
        detailed_info += f"   ⏱ مدت: {duration}\n"
        detailed_info += f"   💰 قیمت: {price:,} تومان\n"
        detailed_info += f"   📅 تاریخ: {order_time}\n"
        detailed_info += f"   🆔 شناسه رسید: {receipt_id}\n"
        detailed_info += f"   🔐 وضعیت: فعال\n\n"
    
    detailed_info += f"📊 آمار کلی:\n"
    detailed_info += f"   📦 تعداد سفارشات: {total_orders}\n"
    detailed_info += f"   💰 کل هزینه: {total_spent:,} تومان\n"
    detailed_info += f"   📅 آخرین خرید: {orders[-1].get('order_time', 'نامشخص')}\n\n"
    detailed_info += f"💡 برای دانلود کانفیگ‌ها، از بخش '📥 دانلود کانفیگ' استفاده کنید."
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back = types.KeyboardButton('🔙 بازگشت')
    markup.add(back)
    
    bot.send_message(message.chat.id, detailed_info, parse_mode="Markdown", reply_markup=markup)

# تولید محتوای کانفیگ بر اساس اطلاعات سفارش
def generate_config_content(username, data_plan, duration):
    """تولید محتوای کانفیگ VLESS بر اساس اطلاعات سفارش"""
    
    import hashlib
    import uuid
    
    # تولید UUID منحصر به فرد بر اساس نام کاربری و اطلاعات سفارش
    seed = f"{username}_{data_plan}_{duration}"
    unique_id = hashlib.md5(seed.encode()).hexdigest()
    
    # تولید UUID بر اساس seed
    uuid_obj = uuid.uuid5(uuid.NAMESPACE_DNS, seed)
    uuid_str = str(uuid_obj)
    
    # تنظیمات سرور VLESS
    server_config = {
        'server': '151.101.195.8',
        'port': '80',
        'uuid': uuid_str,
        'path': '/azizdevspacefastley?ed=2560',
        'host': 'azizdevspace.global.ssl.fastly.net',
        'security': 'none',
        'type': 'xhttp'
    }
    
    # تولید کانفیگ VLESS
    config_content = f"""🔐 کانفیگ فیلترشکن شما:

vless://{server_config['uuid']}@{server_config['server']}:{server_config['port']}?type={server_config['type']}&path={server_config['path']}&host={server_config['host']}&mode=auto&security={server_config['security']}#AzizVPN-{username}

📋 اطلاعات کانفیگ:
👤 نام کاربری: {username}
📊 حجم: {data_plan}
⏱ مدت: {duration}
🌐 سرور: {server_config['server']}
🔌 پورت: {server_config['port']}
🔑 UUID: {server_config['uuid']}
🔒 امنیت: {server_config['security']}

💡 راهنمای استفاده:
1. این کانفیگ را در نرم‌افزار V2rayNG کپی کنید
2. روی دکمه "Start" کلیک کنید
3. از فیلترشکن لذت ببرید!

📞 پشتیبانی: @azizVPN"""
    
    return config_content

# تولید کانفیگ VLESS خالص (فقط کانفیگ)
def generate_pure_vless_config(username, data_plan, duration):
    """تولید کانفیگ VLESS خالص بدون اطلاعات اضافی"""
    
    import hashlib
    import uuid
    
    # تولید UUID منحصر به فرد بر اساس نام کاربری و اطلاعات سفارش
    seed = f"{username}_{data_plan}_{duration}"
    unique_id = hashlib.md5(seed.encode()).hexdigest()
    
    # تولید UUID بر اساس seed
    uuid_obj = uuid.uuid5(uuid.NAMESPACE_DNS, seed)
    uuid_str = str(uuid_obj)
    
    # تنظیمات سرور VLESS
    server_config = {
        'server': '151.101.195.8',
        'port': '80',
        'uuid': uuid_str,
        'path': '/azizdevspacefastley?ed=2560',
        'host': 'azizdevspace.global.ssl.fastly.net',
        'security': 'none',
        'type': 'xhttp'
    }
    
    # تولید کانفیگ VLESS خالص
    pure_config = f"vless://{server_config['uuid']}@{server_config['server']}:{server_config['port']}?type={server_config['type']}&path={server_config['path']}&host={server_config['host']}&mode=auto&security={server_config['security']}#AzizVPN-{username}"
    
    return pure_config

if __name__ == "__main__":
    import time
    import threading
    
    # حذف webhook قبل از شروع polling
    try:
        bot.remove_webhook()
        print("✅ Webhook حذف شد.")
        time.sleep(2)  # انتظار 2 ثانیه
    except Exception as e:
        print(f"⚠️ خطا در حذف webhook: {e}")
    
    print("🤖 ربات در حال شروع است...")
    print(f"🔐 آیدی ادمین: {ADMIN_ID}")
    print(f"💳 شماره کارت: {CARD_NUMBER}")
    
    # تابع auto-save
    def auto_save():
        while True:
            try:
                time.sleep(300)  # ذخیره هر 5 دقیقه
                save_data()
                print("💾 داده‌ها به صورت خودکار ذخیره شدند.")
            except Exception as e:
                print(f"❌ خطا در auto-save: {e}")
    
    # شروع auto-save در thread جداگانه
    auto_save_thread = threading.Thread(target=auto_save, daemon=True)
    auto_save_thread.start()
    print("💾 سیستم auto-save فعال شد.")
    
    # شروع polling
    try:
        print("🔄 شروع polling...")
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        print(f"❌ خطا در polling: {e}")
        print("🔄 تلاش مجدد در 5 ثانیه...")
        time.sleep(5)
        bot.polling(none_stop=True, interval=1, timeout=60) 