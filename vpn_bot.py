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

# تنظیمات اضافی برای بهبود تجربه کاربری
MAX_RETRIES = 3  # حداکثر تلاش برای ورود اطلاعات
SESSION_TIMEOUT = 300  # زمان انقضای جلسه (5 دقیقه)

# فایل‌های ذخیره‌سازی
DATA_FILES = {
    'users': 'users_data.json',
    'blocked': 'blocked_users.json',
    'configs': 'configs_data.json',
    'discount': 'discount_data.json',
    'orders': 'orders_data.json',
    'representation': 'representation_requests.json'
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

# حافظه موقت برای سفارشات در انتظار تأیید
pending_orders = {}  # {order_id: {user_id, order_info}}

# مدیریت جلسات کاربران
user_sessions = {}  # {user_id: {'step': 'current_step', 'data': {}, 'timestamp': time.time()}}

# ذخیره پیام‌های پشتیبانی برای پاسخ آسان
support_messages = {}  # {message_id: {'user_id': int, 'message_text': str, 'timestamp': str}}

# درخواست‌های نمایندگی در انتظار تأیید
representation_requests = {}  # {request_id: {'user_id': int, 'user_info': dict, 'timestamp': str}}

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
        
        # ذخیره درخواست‌های نمایندگی
        with open(DATA_FILES['representation'], 'w', encoding='utf-8') as f:
            json.dump(representation_requests, f, ensure_ascii=False, indent=2)
        
        print("✅ تمام داده‌ها با موفقیت ذخیره شدند.")
    except Exception as e:
        print(f"❌ خطا در ذخیره داده‌ها: {e}")

def load_data():
    """بارگذاری تمام داده‌ها از فایل‌های JSON"""
    global users_db, blocked_users, configs_db, discount_percentage, orders_db, representation_requests
    
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
        
        # بارگذاری درخواست‌های نمایندگی
        if os.path.exists(DATA_FILES['representation']):
            with open(DATA_FILES['representation'], 'r', encoding='utf-8') as f:
                representation_requests = json.load(f)
        else:
            representation_requests = {}
        
        print("✅ تمام داده‌ها با موفقیت بارگذاری شدند.")
        print(f"📊 آمار بارگذاری شده:")
        print(f"   👥 کاربران: {len(users_db)}")
        print(f"   🚫 مسدودها: {len(blocked_users)}")
        print(f"   🔐 کانفیگ‌ها: {len(configs_db)}")
        print(f"   💰 تخفیف: {discount_percentage}%")
        print(f"   📦 سفارشات: {len(orders_db)}")
        print(f"   🏢 درخواست‌های نمایندگی: {len(representation_requests)}")
        
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
    user_name = message.from_user.first_name or "کاربر"
    
    # بررسی مسدودیت کاربر
    if user_id in blocked_users:
        bot.send_message(message.chat.id, 
                        "❌ شما از استفاده از این ربات مسدود شده‌اید.\n"
                        "لطفا با پشتیبانی تماس بگیرید.")
        return
    
    # شروع جلسه جدید
    start_user_session(user_id, 'main_menu')
    
    # ثبت کاربر در دیتابیس
    if user_id not in users_db:
        users_db[user_id] = {
            'first_name': user_name,
            'username': message.from_user.username or '',
            'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'orders': [],
            'total_spent': 0,
            'configs': [],
            'is_representative': False,  # وضعیت نمایندگی
            'representative_discount': 0,  # درصد تخفیف نمایندگی
            'representation_date': None  # تاریخ تأیید نمایندگی
        }
        save_data()
        print(f"New user registered: {user_id} ({user_name})")
    
    # ارسال پیام خوش‌آمدگویی
    send_welcome_message(message.chat.id, user_name)

@bot.message_handler(commands=['help'])
def help_command(message):
    """دستور راهنما"""
    help_text = """
📚 راهنمای استفاده از ربات

🔹 دستورات اصلی:
/start - شروع ربات و نمایش منوی اصلی
/help - نمایش این راهنما

🔹 مراحل خرید:
1. روی «🛒 خرید فیلترشکن» کلیک کنید
2. حجم داده مورد نظر را انتخاب کنید
3. مدت زمان اشتراک را انتخاب کنید
4. نام کاربری دلخواه وارد کنید
5. قیمت را بررسی و تأیید کنید
6. مبلغ را پرداخت کنید
7. رسید را ارسال کنید
8. منتظر تأیید ادمین بمانید

🔹 سایر امکانات:
• 👤 حساب من - مشاهده اطلاعات حساب
• 🔐 کانفیگ‌های من - دانلود کانفیگ‌های خریداری شده
• 📞 پشتیبانی - ارتباط با پشتیبانی

💡 نکات مهم:
• تمام پرداخت‌ها امن و محافظت شده هستند
• کانفیگ‌ها پس از تأیید پرداخت ارسال می‌شوند
• در صورت مشکل با پشتیبانی تماس بگیرید
    """
    
    markup = create_main_menu()
    bot.send_message(message.chat.id, help_text, reply_markup=markup)

# پاسخ به دکمه‌های اصلی
@bot.message_handler(func=lambda message: message.text in ['🛒 خرید فیلترشکن', '👤 حساب من', '🔐 کانفیگ‌های من', '📞 پشتیبانی', '🏢 درخواست نمایندگی', '⚙️ پنل مدیریت'])
def main_menu_handler(message):
    user_id = message.from_user.id
    
    # بررسی مسدودیت
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    # به‌روزرسانی جلسه
    update_user_session(user_id, 'main_menu')
    
    if message.text == '🛒 خرید فیلترشکن':
        # پاک کردن اطلاعات قبلی
        if user_id in user_data:
            user_data[user_id] = {}
        
        update_user_session(user_id, 'buying', {'retry_count': 0})
        show_data_plans(message)
        
    elif message.text == '👤 حساب من':
        show_user_account(message)
        
    elif message.text == '🔐 کانفیگ‌های من':
        show_user_configs(message)
        
    elif message.text == '📞 پشتیبانی':
        update_user_session(user_id, 'support')
        markup = create_back_button()
        bot.send_message(message.chat.id, 
                        "📞 پشتیبانی\n\n"
                        "برای ارتباط با پشتیبانی، پیام خود را ارسال کنید.\n"
                        "کارشناسان ما در اسرع وقت پاسخ شما را خواهند داد.",
                        reply_markup=markup)
        bot.register_next_step_handler(message, process_support_message)
        
    elif message.text == '🏢 درخواست نمایندگی':
        show_representation_request(message)
        
    elif message.text == '⚙️ پنل مدیریت':
        if user_id == ADMIN_ID:
            show_admin_panel(message)
        else:
            bot.send_message(message.chat.id, "⛔️ شما دسترسی به این بخش را ندارید.")

# نمایش درخواست نمایندگی
def show_representation_request(message):
    """نمایش صفحه درخواست نمایندگی"""
    user_id = message.from_user.id
    
    # بررسی مسدودیت
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    # بررسی اینکه آیا کاربر قبلاً نماینده است
    if user_id in users_db and users_db[user_id].get('is_representative', False):
        markup = create_main_menu()
        bot.send_message(message.chat.id, 
                        "🏢 شما قبلاً نماینده تأیید شده‌اید!\n\n"
                        f"🎯 درصد تخفیف شما: {users_db[user_id].get('representative_discount', 0)}%\n"
                        f"📅 تاریخ تأیید: {users_db[user_id].get('representation_date', 'نامشخص')}\n\n"
                        "💡 این تخفیف در تمام خریدهای شما اعمال می‌شود.",
                        reply_markup=markup)
        return
    
    update_user_session(user_id, 'representation_request')
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    yes_btn = types.KeyboardButton('✅ بله')
    no_btn = types.KeyboardButton('❌ خیر')
    back_btn = types.KeyboardButton('🔙 بازگشت')
    home_btn = types.KeyboardButton('🏠 منوی اصلی')
    markup.add(yes_btn, no_btn, back_btn, home_btn)
    
    representation_info = """
🏢 درخواست نمایندگی

آیا می‌خواهید برای نمایندگی درخواست کنید؟

🎯 مزایای نمایندگی:
• تخفیف ویژه روی تمام خریدها
• قیمت‌های مخصوص نمایندگان
• پشتیبانی ویژه
• امکان فروش به مشتریان

📋 شرایط نمایندگی:
• حداقل 3 خرید موفق
• فعالیت منظم در ربات
• رعایت قوانین و مقررات

💡 پس از تأیید، تخفیف مخصوص به حساب شما اعمال خواهد شد.
    """
    
    bot.send_message(message.chat.id, representation_info, reply_markup=markup)

# پردازش درخواست نمایندگی
@bot.message_handler(func=lambda message: message.text in ['✅ بله', '❌ خیر'])
def process_representation_request(message):
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    if message.text == '❌ خیر':
        markup = create_main_menu()
        bot.send_message(message.chat.id, 
                        "❌ درخواست نمایندگی لغو شد.\n"
                        "در صورت نیاز، می‌توانید دوباره درخواست دهید.",
                        reply_markup=markup)
        return
    
    elif message.text == '✅ بله':
        # ارسال درخواست به ادمین
        send_representation_request_to_admin(message)
        return

# ارسال درخواست نمایندگی به ادمین
def send_representation_request_to_admin(message):
    user_id = message.from_user.id
    
    # اطلاعات کاربر
    user_info = users_db.get(user_id, {})
    user_name = user_info.get('first_name', 'نامشخص')
    username = user_info.get('username', 'نامشخص')
    join_date = user_info.get('join_date', 'نامشخص')
    total_orders = len(user_info.get('orders', []))
    total_spent = user_info.get('total_spent', 0)
    
    # ایجاد شناسه درخواست (کوتاه‌تر برای جلوگیری از محدودیت callback_data)
    timestamp = int(time.time()) % 1000000
    request_id = f"{user_id}_{timestamp}"
    
    # ذخیره درخواست
    representation_requests[request_id] = {
        'user_id': user_id,
        'user_info': {
            'first_name': user_name,
            'username': username,
            'join_date': join_date,
            'total_orders': total_orders,
            'total_spent': total_spent
        },
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # ذخیره داده‌ها
    save_data()
    
    # پیام به ادمین
    admin_msg = f"""
🏢 درخواست نمایندگی جدید:

👤 اطلاعات کاربر:
• نام: {user_name}
• یوزرنیم: @{username}
• آیدی: `{user_id}`
• تاریخ عضویت: {join_date}
• تعداد سفارشات: {total_orders}
• کل هزینه: {total_spent:,} تومان

📅 تاریخ درخواست: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

آیا می‌خواهید این کاربر را نماینده کنید؟
    """
    
    # ایجاد دکمه‌های تأیید/رد
    markup = types.InlineKeyboardMarkup(row_width=2)
    approve_btn = types.InlineKeyboardButton("✅ تأیید نمایندگی", callback_data=f"app_rep_{request_id}")
    reject_btn = types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"rej_rep_{request_id}")
    markup.add(approve_btn, reject_btn)
    
    try:
        sent = bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown", reply_markup=markup)
        
        if sent:
            # تأیید به کاربر
            markup = create_main_menu()
            bot.send_message(message.chat.id, 
                           "✅ درخواست نمایندگی شما با موفقیت ارسال شد!\n\n"
                           "📞 ادمین درخواست شما را بررسی خواهد کرد.\n"
                           "🔔 پس از بررسی، نتیجه به شما اطلاع داده خواهد شد.\n\n"
                           "🙏 از صبر شما متشکریم.",
                           reply_markup=markup)
            
            print(f"Representation request sent to admin from user {user_id}")
        else:
            bot.send_message(message.chat.id, 
                           "❌ خطا در ارسال درخواست.\n"
                           "لطفا دوباره تلاش کنید.")
    
    except Exception as e:
        print(f"Error sending representation request: {e}")
        bot.send_message(message.chat.id, 
                        "❌ خطا در ارسال درخواست نمایندگی.\n"
                        "لطفا با پشتیبانی تماس بگیرید.")

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
    
    # بررسی مسدودیت
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    if user_id not in users_db:
        bot.send_message(message.chat.id, "❌ اطلاعات کاربری یافت نشد.")
        return
    
    user = users_db[user_id]
    orders = user.get('orders', [])
    total_spent = user.get('total_spent', 0)
    join_date = user.get('join_date', 'نامشخص')
    
    # محاسبه آمار
    total_orders = len(orders)
    active_configs = len(user.get('configs', []))
    
    # نمایش اطلاعات حساب
    account_info = f"""
👤 حساب کاربری شما

📊 اطلاعات شخصی:
• نام: {user.get('first_name', 'نامشخص')}
• یوزرنیم: @{user.get('username', 'نامشخص')}
• تاریخ عضویت: {join_date}

"""
    
    # نمایش وضعیت نمایندگی
    if user.get('is_representative', False):
        representative_discount = user.get('representative_discount', 0)
        representation_date = user.get('representation_date', 'نامشخص')
        account_info += f"""🏢 وضعیت نمایندگی:
• وضعیت: ✅ نماینده تأیید شده
• درصد تخفیف: {representative_discount}%
• تاریخ تأیید: {representation_date}

"""
    
    account_info += f"""📈 آمار خرید:
• تعداد سفارشات: {total_orders} عدد
• کل هزینه: {total_spent:,} تومان
• کانفیگ‌های فعال: {active_configs} عدد

"""
    
    if total_orders > 0:
        account_info += "📋 آخرین سفارشات:\n"
        for i, order in enumerate(orders[-3:], 1):  # نمایش 3 سفارش آخر
            data_plan = order.get('data_plan', '')
            # تبدیل فرمت داده
            if 'GB' in data_plan:
                data_plan_text = data_plan.replace('GB', ' گیگابایت')
            else:
                data_plan_text = data_plan
            
            duration = order.get('duration', '')
            price = order.get('price', 0)
            order_time = order.get('order_time', 'نامشخص')
            
            duration_text = {
                '1month': '1 ماهه'
            }.get(duration, duration)
            
            account_info += f"• {i}. {data_plan_text} - {duration_text} - {price:,} تومان\n"
            account_info += f"  �� {order_time}\n\n"
    
    markup = create_main_menu()
    bot.send_message(message.chat.id, account_info, reply_markup=markup)

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
        if data_plan.endswith('GB'):
            # برای حجم‌های دلخواه (مثل 45GB, 67GB, etc.)
            data_plan_fa = f"{data_plan.replace('GB', '')} گیگابایت"
        else:
            # برای سایر موارد
            data_plan_fa = data_plan
        
        if duration == '1month':
            duration_fa = '1 ماهه'
        else:
            duration_fa = '1 ماهه'  # همه مدت‌ها به 1 ماهه تبدیل می‌شوند
        
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
        
        # ایجاد دکمه Reply
        markup = types.InlineKeyboardMarkup(row_width=1)
        reply_btn = types.InlineKeyboardButton("💬 پاسخ", callback_data=f"reply_{user_id}")
        markup.add(reply_btn)
        
        # ارسال به ادمین با دکمه Reply
        sent = bot.send_message(ADMIN_ID, support_msg, reply_markup=markup)
        
        if sent:
            # ذخیره پیام پشتیبانی برای پاسخ آسان
            support_messages[sent.message_id] = {
                'user_id': user_id,
                'message_text': clean_message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_name': user_name,
                'username': username
            }
            
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
    """نمایش پلن‌های حجم داده با طراحی بهتر"""
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    update_user_session(user_id, 'selecting_data_plan')
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    
    # فقط گزینه حجم دلخواه
    btn_custom = types.KeyboardButton('📝 حجم دلخواه')
    
    back_btn = types.KeyboardButton('🔙 بازگشت')
    home_btn = types.KeyboardButton('🏠 منوی اصلی')
    
    markup.add(btn_custom, back_btn, home_btn)
    
    plans_text = """
📊 انتخاب حجم داده

لطفا حجم مورد نظر خود را وارد کنید:

💡 قیمت هر گیگابایت: 3,000 تومان
💡 حداقل حجم: 30 گیگابایت
💡 حداکثر حجم: 150 گیگابایت

📝 روی "حجم دلخواه" کلیک کنید و حجم مورد نظر خود را وارد کنید.
    """
    
    bot.send_message(message.chat.id, plans_text, reply_markup=markup)

# پردازش انتخاب حجم داده
@bot.message_handler(func=lambda message: message.text == '📝 حجم دلخواه')
def process_data_plan(message):
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    # ایجاد حافظه موقت برای کاربر
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # درخواست حجم دلخواه از کاربر
    update_user_session(user_id, 'entering_custom_volume')
    markup = create_back_button()
    
    custom_volume_text = """
📝 حجم دلخواه

لطفا حجم مورد نظر خود را به گیگابایت وارد کنید:

💡 مثال: 50 (برای 50 گیگابایت)
💡 قیمت هر گیگابایت: 3,000 تومان
💡 حداقل حجم: 30 گیگابایت
💡 حداکثر حجم: 150 گیگابایت

📝 فقط عدد وارد کنید (بدون واحد):
    """
    
    bot.send_message(message.chat.id, custom_volume_text, reply_markup=markup)
    bot.register_next_step_handler(message, process_custom_volume)

# پردازش حجم دلخواه
def process_custom_volume(message):
    """پردازش حجم دلخواه وارد شده توسط کاربر"""
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    if message.text == '🔙 بازگشت':
        show_data_plans(message)
        return
    
    try:
        # تبدیل متن به عدد
        volume = float(message.text)
        
        # بررسی محدودیت‌ها
        if volume < 30:
            bot.send_message(message.chat.id, 
                           "❌ حداقل حجم 30 گیگابایت است.\n"
                           "لطفا دوباره وارد کنید:")
            bot.register_next_step_handler(message, process_custom_volume)
            return
        
        if volume > 150:
            bot.send_message(message.chat.id, 
                           "❌ حداکثر حجم 150 گیگابایت است.\n"
                           "لطفا دوباره وارد کنید:")
            bot.register_next_step_handler(message, process_custom_volume)
            return
        
        # ذخیره حجم دلخواه
        user_data[user_id]['custom_volume'] = int(volume)
        user_data[user_id]['data_plan'] = f"{int(volume)}GB"
        update_user_session(user_id, 'data_selected', {'data_plan': f"{int(volume)}GB", 'custom_volume': int(volume)})
        
        # نمایش تأیید و ادامه به مرحله بعدی
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        continue_btn = types.KeyboardButton('⏭️ ادامه')
        back_btn = types.KeyboardButton('🔙 بازگشت')
        markup.add(continue_btn, back_btn)
        
        confirmation_text = f"""
✅ حجم انتخاب شده: {int(volume)} گیگابایت

💰 قیمت پایه: {int(volume) * 3000:,} تومان
💡 قیمت هر گیگابایت: 3,000 تومان

⏭️ برای ادامه و انتخاب مدت زمان، روی "ادامه" کلیک کنید:
        """
        
        bot.send_message(message.chat.id, confirmation_text, reply_markup=markup)
        bot.register_next_step_handler(message, handle_volume_confirmation)
        
    except ValueError:
        bot.send_message(message.chat.id, 
                        "❌ لطفا یک عدد معتبر وارد کنید.\n"
                        "مثال: 50")
        bot.register_next_step_handler(message, process_custom_volume)

def handle_volume_confirmation(message):
    """پردازش تأیید حجم و ادامه به مرحله بعدی"""
    user_id = message.from_user.id
    
    if message.text == '⏭️ ادامه':
        # نمایش مدت زمان‌های اشتراک
        show_duration_plans(message)
    elif message.text == '🔙 بازگشت':
        show_data_plans(message)
    else:
        bot.send_message(message.chat.id, "❌ لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        bot.register_next_step_handler(message, handle_volume_confirmation)

# نمایش پلن‌های زمانی
def show_duration_plans(message):
    """نمایش پلن‌های مدت زمان با طراحی بهتر"""
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    update_user_session(user_id, 'selecting_duration')
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    
    # فقط گزینه 1 ماهه
    btn_1month = types.KeyboardButton('⏱ 1 ماهه')
    
    back_btn = types.KeyboardButton('🔙 بازگشت')
    home_btn = types.KeyboardButton('🏠 منوی اصلی')
    
    markup.add(btn_1month, back_btn, home_btn)
    
    duration_text = """
⏱ انتخاب مدت زمان اشتراک

لطفا مدت زمان مورد نظر خود را انتخاب کنید:

🔹 1 ماهه - مناسب برای استفاده کوتاه مدت

💡 نکته: مدت زمان اشتراک 1 ماهه است.
    """
    
    bot.send_message(message.chat.id, duration_text, reply_markup=markup)

# پردازش انتخاب مدت زمان
@bot.message_handler(func=lambda message: message.text == '⏱ 1 ماهه')
def process_duration_plan(message):
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    # ذخیره مدت زمان انتخاب شده (فقط 1 ماهه)
    user_data[user_id]['duration'] = '1month'
    update_user_session(user_id, 'duration_selected', {'duration': '1month'})
    
    # درخواست نام کاربری
    ask_username(message)

# درخواست نام کاربری
def ask_username(message):
    """درخواست نام کاربری با طراحی بهتر"""
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    update_user_session(user_id, 'entering_username')
    
    markup = create_back_button()
    
    username_text = """
👤 نام کاربری

لطفا نام کاربری مورد نظر خود را وارد کنید:

📝 قوانین نام کاربری:
• فقط حروف انگلیسی، اعداد و خط تیره
• حداقل 3 کاراکتر و حداکثر 20 کاراکتر
• نباید با عدد شروع شود
• مثال: user123, my-vpn, test_user

💡 نکته: این نام کاربری برای اتصال به سرور استفاده خواهد شد.
    """
    
    bot.send_message(message.chat.id, username_text, reply_markup=markup)
    bot.register_next_step_handler(message, process_username)

# پردازش نام کاربری
def process_username(message):
    """پردازش نام کاربری با اعتبارسنجی بهتر"""
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    # بررسی دکمه‌های بازگشت
    if message.text in ['🔙 بازگشت', '🏠 منوی اصلی']:
        if message.text == '🔙 بازگشت':
            show_duration_plans(message)
        else:
            start(message)
        return
    
    username = message.text.strip()
    
    # اعتبارسنجی نام کاربری
    import re
    username_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{2,19}$')
    
    if not username_pattern.match(username):
        # افزایش شمارنده تلاش
        session = get_user_session(user_id)
        retry_count = session.get('data', {}).get('username_retry', 0) + 1
        
        if retry_count >= MAX_RETRIES:
            bot.send_message(message.chat.id, 
                           "❌ تعداد تلاش‌های شما به پایان رسید.\n"
                           "لطفا دوباره از منوی اصلی شروع کنید.")
            clear_user_session(user_id)
            start(message)
            return
        
        update_user_session(user_id, 'entering_username', {'username_retry': retry_count})
        
        error_text = f"""
❌ نام کاربری نامعتبر است!

📝 قوانین نام کاربری:
• فقط حروف انگلیسی، اعداد و خط تیره
• حداقل 3 کاراکتر و حداکثر 20 کاراکتر
• باید با حرف شروع شود
• مثال: user123, my-vpn, test_user

🔄 تلاش {retry_count} از {MAX_RETRIES}
        """
        
        markup = create_back_button()
        bot.send_message(message.chat.id, error_text, reply_markup=markup)
        bot.register_next_step_handler(message, process_username)
        return
    
    # ذخیره نام کاربری
    user_data[user_id]['username'] = username
    update_user_session(user_id, 'username_entered', {'username': username})
    
    # نمایش قیمت نهایی
    show_final_price(message)

# محاسبه و نمایش قیمت نهایی
def show_final_price(message):
    """نمایش قیمت نهایی با طراحی بهتر"""
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    if user_id not in user_data or 'data_plan' not in user_data[user_id] or 'duration' not in user_data[user_id] or 'username' not in user_data[user_id]:
        bot.send_message(message.chat.id, "❌ اطلاعات ناقص است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    # محاسبه قیمت پایه
    data_plan = user_data[user_id]['data_plan']
    duration = user_data[user_id]['duration']
    username = user_data[user_id]['username']
    
    # استخراج حجم داده (به گیگابایت)
    if 'custom_volume' in user_data[user_id]:
        # حجم دلخواه
        data_gb = user_data[user_id]['custom_volume']
    else:
        # حجم از پیش تعریف شده
        data_gb = int(data_plan.replace('GB', ''))
    
    # قیمت هر گیگابایت: 3000 تومان
    price_per_gb = 3000
    
    # محاسبه قیمت پایه بر اساس حجم (بدون ضریب مدت زمان)
    base_price = data_gb * price_per_gb
    total_price = base_price
    
    # اعمال تخفیف عمومی
    general_discount_amount = int(total_price * discount_percentage / 100)
    price_after_general_discount = total_price - general_discount_amount
    
    # اعمال تخفیف نمایندگی (اگر کاربر نماینده است)
    representative_discount_amount = 0
    final_price = price_after_general_discount
    
    if user_id in users_db and users_db[user_id].get('is_representative', False):
        representative_discount = users_db[user_id].get('representative_discount', 0)
        representative_discount_amount = int(price_after_general_discount * representative_discount / 100)
        final_price = price_after_general_discount - representative_discount_amount
    
    # ذخیره قیمت‌ها
    user_data[user_id]['base_price'] = total_price
    user_data[user_id]['general_discount_amount'] = general_discount_amount
    user_data[user_id]['representative_discount_amount'] = representative_discount_amount
    user_data[user_id]['price'] = final_price
    user_data[user_id]['data_gb'] = data_gb
    
    update_user_session(user_id, 'price_shown')
    
    # تبدیل به متن فارسی
    data_plan_text = f"{data_gb} گیگابایت"
    duration_text = "1 ماهه"
    
    # نمایش اطلاعات سفارش
    order_summary = f"""
📋 خلاصه سفارش شما

👤 نام کاربری: `{username}`
📊 حجم داده: {data_plan_text}
⏱ مدت زمان: {duration_text}

💰 قیمت‌گذاری:
• قیمت پایه ({data_gb} گیگ × {price_per_gb:,} تومان): {total_price:,} تومان
"""
    
    if discount_percentage > 0:
        order_summary += f"• تخفیف عمومی ({discount_percentage}%): {general_discount_amount:,} تومان\n"
    
    if representative_discount_amount > 0:
        representative_discount = users_db[user_id].get('representative_discount', 0)
        order_summary += f"• تخفیف نمایندگی ({representative_discount}%): {representative_discount_amount:,} تومان\n"
    
    order_summary += f"""
• قیمت نهایی: {final_price:,} تومان

✅ آیا می‌خواهید این سفارش را تکمیل کنید؟
"""
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    confirm_btn = types.KeyboardButton('✅ تأیید و پرداخت')
    cancel_btn = types.KeyboardButton('❌ انصراف')
    back_btn = types.KeyboardButton('🔙 بازگشت')
    home_btn = types.KeyboardButton('🏠 منوی اصلی')
    markup.add(confirm_btn, cancel_btn, back_btn, home_btn)
    
    bot.send_message(message.chat.id, order_summary, reply_markup=markup, parse_mode="Markdown")

# پردازش تأیید پرداخت
@bot.message_handler(func=lambda message: message.text in ['✅ تأیید و پرداخت', '❌ انصراف'])
def process_payment_confirmation(message):
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    if message.text == '❌ انصراف':
        markup = create_main_menu()
        bot.send_message(message.chat.id, 
                        "❌ سفارش شما لغو شد.\n"
                        "در صورت نیاز، می‌توانید دوباره خرید کنید.",
                        reply_markup=markup)
        clear_user_session(user_id)
        return
    
    # بررسی وجود اطلاعات سفارش
    if user_id not in user_data or 'price' not in user_data[user_id]:
        bot.send_message(message.chat.id, "❌ اطلاعات سفارش ناقص است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    update_user_session(user_id, 'payment_confirmed')
    
    # نمایش اطلاعات پرداخت
    price = user_data[user_id]['price']
    data_gb = user_data[user_id].get('data_gb', int(user_data[user_id]['data_plan'].replace('GB', '')))
    duration = user_data[user_id]['duration']
    username = user_data[user_id]['username']
    
    duration_text = {
        '1month': '1 ماهه',
        '3month': '3 ماهه',
        '6month': '6 ماهه',
        '1year': '1 ساله'
    }.get(duration, duration)
    
    payment_info = f"""
💳 اطلاعات پرداخت

📋 خلاصه سفارش:
• نام کاربری: `{username}`
• حجم داده: {data_gb} گیگابایت
• مدت زمان: {duration_text}
• مبلغ: {price:,} تومان

🏦 اطلاعات کارت:
• شماره: `{CARD_NUMBER}`
• به نام: علی خلیلی ابکوه

📸 پس از پرداخت:
1. روی دکمه «📤 ارسال رسید پرداخت» کلیک کنید
2. تصویر رسید را ارسال کنید
3. منتظر تأیید بمانید

⚠️ نکات مهم:
• حتماً شماره کارت را درست وارد کنید
• رسید پرداخت را واضح و کامل ارسال کنید
• در صورت مشکل با پشتیبانی تماس بگیرید
    """
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    receipt_btn = types.KeyboardButton('📤 ارسال رسید پرداخت')
    cancel_btn = types.KeyboardButton('❌ انصراف')
    back_btn = types.KeyboardButton('🔙 بازگشت')
    home_btn = types.KeyboardButton('🏠 منوی اصلی')
    
    markup.add(receipt_btn, cancel_btn, back_btn, home_btn)
    
    bot.send_message(message.chat.id, payment_info, parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(message, process_receipt_option)

# پردازش انتخاب ارسال رسید
@bot.message_handler(func=lambda message: message.text in ['📤 ارسال رسید پرداخت', '❌ انصراف', '🔙 بازگشت', '🏠 منوی اصلی'])
def process_receipt_option(message):
    user_id = message.from_user.id
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, "⏰ جلسه شما منقضی شده است. لطفا دوباره شروع کنید.")
        start(message)
        return
    
    if message.text == '❌ انصراف':
        markup = create_main_menu()
        bot.send_message(message.chat.id, 
                        "❌ سفارش شما لغو شد.\n"
                        "در صورت نیاز، می‌توانید دوباره خرید کنید.",
                        reply_markup=markup)
        clear_user_session(user_id)
        return
    
    elif message.text == '🔙 بازگشت':
        show_final_price(message)
        return
    
    elif message.text == '🏠 منوی اصلی':
        start(message)
        return
    
    elif message.text != '📤 ارسال رسید پرداخت':
        bot.send_message(message.chat.id, "❌ لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        return
    
    update_user_session(user_id, 'uploading_receipt')
    
    markup = create_back_button()
    
    receipt_instruction = """
📤 ارسال رسید پرداخت

لطفا تصویر رسید پرداخت خود را ارسال کنید:

📸 نکات مهم:
• تصویر باید واضح و خوانا باشد
• شماره تراکنش و مبلغ باید مشخص باشد
• تاریخ و زمان پرداخت باید قابل مشاهده باشد
• فرمت‌های قابل قبول: JPG, PNG, PDF

⚠️ توجه: پس از ارسال رسید، منتظر تأیید ادمین بمانید.
    """
    
    bot.send_message(message.chat.id, receipt_instruction, reply_markup=markup)
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
        data_gb = user_data[user_id].get('data_gb', int(user_data[user_id]['data_plan'].replace('GB', '')))
        duration = user_data[user_id]['duration']
        if duration == '1month':
            duration_text = '1 ماهه'
        else:
            duration_text = '1 ماهه'  # همه مدت‌ها به 1 ماهه تبدیل می‌شوند
        
        username = user_data[user_id]['username']
        price = user_data[user_id]['price']
        base_price = user_data[user_id].get('base_price', price)
        general_discount_amount = user_data[user_id].get('general_discount_amount', 0)
        representative_discount_amount = user_data[user_id].get('representative_discount_amount', 0)
        
        # ایجاد شناسه سفارش
        order_id = f"order_{user_id}_{int(time.time())}"
        
        # ذخیره اطلاعات سفارش در انتظار تأیید
        pending_orders[order_id] = {
            'user_id': user_id,
            'data_plan': f"{data_gb} گیگابایت",
            'duration': duration_text,
            'username': username,
            'price': price,
            'base_price': base_price,
            'general_discount_amount': general_discount_amount,
            'representative_discount_amount': representative_discount_amount,
            'order_time': user_data[user_id]['order_time']
        }
        
        # ارسال اطلاعات سفارش به ادمین با دکمه‌های تأیید/لغو
        admin_msg = (
            f"🔔 سفارش جدید:\n\n"
            f"🆔 آیدی کاربر: `{user_id}`\n"
            f"👤 نام کاربری: `{username}`\n"
            f"📊 حجم: {data_gb} گیگابایت\n"
            f"⏱ مدت: {duration_text}\n"
        )
        
        # نمایش اطلاعات قیمت‌گذاری
        admin_msg += f"💰 قیمت پایه: {base_price:,} تومان\n"
        
        if general_discount_amount > 0:
            admin_msg += f"🎯 تخفیف عمومی ({discount_percentage}%): {general_discount_amount:,} تومان\n"
        
        if representative_discount_amount > 0:
            representative_discount = users_db[user_id].get('representative_discount', 0)
            admin_msg += f"🏢 تخفیف نمایندگی ({representative_discount}%): {representative_discount_amount:,} تومان\n"
        
        admin_msg += f"💳 مبلغ نهایی: {price:,} تومان\n"
        admin_msg += f"🕒 زمان سفارش: {user_data[user_id]['order_time']}\n\n"
        admin_msg += f"لطفا تأیید یا رد کنید:"
        
        # ایجاد دکمه‌های تأیید و لغو
        markup = types.InlineKeyboardMarkup(row_width=2)
        approve_btn = types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{order_id}")
        reject_btn = types.InlineKeyboardButton("❌ لغو", callback_data=f"reject_{order_id}")
        markup.add(approve_btn, reject_btn)
        
        sent = bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown", reply_markup=markup)
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

# دستور ارسال کانفیگ توسط ادمین (غیرفعال شده - جایگزین شده با دکمه‌های تأیید/لغو)
# @bot.message_handler(commands=['send_config'])
# def send_config_command(message):
#     user_id = message.from_user.id
#     
#     # بررسی دسترسی ادمین
#     if user_id != ADMIN_ID:
#         bot.send_message(message.chat.id, "⛔️ شما دسترسی به این دستور را ندارید.")
#         print(f"Unauthorized access to send_config: User ID {user_id}, Admin ID {ADMIN_ID}")
#         return
#     
#     # بررسی فرمت دستور
#     command_parts = message.text.split()
#     if len(command_parts) != 2:
#         bot.send_message(message.chat.id, "❌ فرمت صحیح: `/send_config [chat_id]`", parse_mode="Markdown")
#         return
#     
#     try:
#         target_user_id = int(command_parts[1])
#         
#         # درخواست فایل کانفیگ
#         bot.send_message(message.chat.id, 
#                          f"📁 لطفا فایل کانفیگ برای کاربر `{target_user_id}` را ارسال کنید:",
#                          parse_mode="Markdown")
#         
#         # ثبت مرحله بعدی
#         bot.register_next_step_handler(message, lambda msg: process_config_file(msg, target_user_id))
#         
#     except ValueError:
#         bot.send_message(message.chat.id, "❌ شناسه کاربر باید عددی باشد.")

# دستور ارسال دستی کانفیگ (برای موارد خاص)
@bot.message_handler(commands=['manual_config'])
def manual_config_command(message):
    user_id = message.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔️ شما دسترسی به این دستور را ندارید.")
        return
    
    # بررسی فرمت دستور
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.send_message(message.chat.id, "❌ فرمت صحیح: `/manual_config [chat_id]`", parse_mode="Markdown")
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
def process_config_file(message, target_user_id, order_id=None):
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
                        "`/reply 123456789 سلام، مشکل شما حل شد`\n\n"
                        "💡 پیشنهاد: از دکمه «💬 پاسخ» در پیام‌های پشتیبانی استفاده کنید.",
                        parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(command_parts[1])
        reply_text = command_parts[2]
        
        # ارسال پاسخ به کاربر
        try:
            reply_msg = f"""
📞 پاسخ پشتیبانی:

{reply_text}

---
💬 پشتیبانی AzizVPN
            """
            
            sent = bot.send_message(target_user_id, reply_msg)
            
            if sent:
                # تأیید ارسال به ادمین
                bot.send_message(ADMIN_ID, 
                               f"✅ پاسخ با موفقیت به کاربر `{target_user_id}` ارسال شد.\n\n"
                               f"💬 پاسخ:\n{reply_text}",
                               parse_mode="Markdown")
                
                # حذف پیام پشتیبانی از حافظه
                for msg_id, msg_data in list(support_messages.items()):
                    if msg_data['user_id'] == target_user_id:
                        del support_messages[msg_id]
                        break
                
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
    
    # شمارش پیام‌های در انتظار
    pending_count = len(support_messages)
    
    support_info = f"""
📞 مدیریت پیام‌های پشتیبانی:

🆕 سیستم جدید پاسخ آسان:
• هر پیام پشتیبانی دارای دکمه «💬 پاسخ» است
• با کلیک روی دکمه، می‌توانید مستقیماً پاسخ دهید
• نیازی به تایپ دستور نیست

📊 آمار فعلی:
• پیام‌های در انتظار: {pending_count} عدد

📝 روش‌های پاسخ:
1️⃣ دکمه «💬 پاسخ» (پیشنهادی)
2️⃣ دستور `/reply [user_id] [پیام]`

💡 نکات مهم:
• پیام‌های پشتیبانی به صورت مستقیم ارسال می‌شوند
• پس از پاسخ، پیام از لیست انتظار حذف می‌شود
• آیدی کاربر در هر پیام قابل مشاهده است
    """
    
    bot.send_message(message.chat.id, support_info)

# نمایش اطلاعات پیام‌های پشتیبانی
def show_support_info(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    # شمارش پیام‌های پشتیبانی در انتظار
    pending_count = len(support_messages)
    
    support_info = f"""
📞 مدیریت پیام‌های پشتیبانی:

🆕 سیستم جدید پاسخ آسان:
• هر پیام پشتیبانی دارای دکمه «💬 پاسخ» است
• با کلیک روی دکمه، می‌توانید مستقیماً پاسخ دهید
• نیازی به تایپ دستور نیست

📊 آمار فعلی:
• پیام‌های در انتظار: {pending_count} عدد

📝 روش‌های پاسخ:
1️⃣ دکمه «💬 پاسخ» (پیشنهادی)
2️⃣ دستور `/reply [user_id] [پیام]`

💡 نکات مهم:
• پیام‌های پشتیبانی به صورت مستقیم ارسال می‌شوند
• پس از پاسخ، پیام از لیست انتظار حذف می‌شود
• آیدی کاربر در هر پیام قابل مشاهده است
    """
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    list_btn = types.KeyboardButton('📋 لیست پیام‌ها')
    back_btn = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(list_btn, back_btn)
    
    bot.send_message(message.chat.id, support_info, reply_markup=markup)

# نمایش لیست پیام‌های پشتیبانی در انتظار
def show_pending_support_messages(message):
    """نمایش لیست پیام‌های پشتیبانی در انتظار"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if not support_messages:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_btn = types.KeyboardButton('🔙 بازگشت به پنل')
        markup.add(back_btn)
        
        bot.send_message(message.chat.id, 
                        "📭 هیچ پیام پشتیبانی در انتظار وجود ندارد.",
                        reply_markup=markup)
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back_btn = types.KeyboardButton('🔙 بازگشت به پنل')
    markup.add(back_btn)
    
    messages_list = f"📋 لیست پیام‌های پشتیبانی در انتظار ({len(support_messages)} عدد):\n\n"
    
    for i, (msg_id, msg_data) in enumerate(support_messages.items(), 1):
        user_id = msg_data['user_id']
        user_name = msg_data['user_name']
        username = msg_data['username']
        timestamp = msg_data['timestamp']
        message_text = msg_data['message_text'][:100] + "..." if len(msg_data['message_text']) > 100 else msg_data['message_text']
        
        messages_list += f"{i}. 👤 {user_name} (@{username})\n"
        messages_list += f"   🆔 آیدی: {user_id}\n"
        messages_list += f"   📅 تاریخ: {timestamp}\n"
        messages_list += f"   💬 پیام: {message_text}\n\n"
    
    messages_list += "💡 برای پاسخ، روی دکمه «💬 پاسخ» در پیام اصلی کلیک کنید."
    
    bot.send_message(message.chat.id, messages_list, reply_markup=markup)

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
        if data_plan.endswith('GB'):
            # برای حجم‌های دلخواه (مثل 45GB, 67GB, etc.)
            data_plan_fa = f"{data_plan.replace('GB', '')} گیگابایت"
        else:
            # برای سایر موارد
            data_plan_fa = data_plan
        
        if duration == '1month':
            duration_fa = '1 ماهه'
        else:
            duration_fa = '1 ماهه'  # همه مدت‌ها به 1 ماهه تبدیل می‌شوند
        
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
        if data_plan.endswith('GB'):
            # برای حجم‌های دلخواه (مثل 45GB, 67GB, etc.)
            data_plan_fa = f"{data_plan.replace('GB', '')} گیگابایت"
        else:
            # برای سایر موارد
            data_plan_fa = data_plan
        
        if duration == '1month':
            duration_fa = '1 ماهه'
        else:
            duration_fa = '1 ماهه'  # همه مدت‌ها به 1 ماهه تبدیل می‌شوند
        
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

# پردازش دکمه‌های تأیید/رد نمایندگی
@bot.callback_query_handler(func=lambda call: call.data.startswith(('app_rep_', 'rej_rep_')))
def handle_representation_approval(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔️ شما دسترسی به این عملیات را ندارید.")
        return
    
    # پارس کردن callback_data به درستی
    if call.data.startswith('app_rep_'):
        action = 'approve'
        request_id = call.data.replace('app_rep_', '')
    elif call.data.startswith('rej_rep_'):
        action = 'reject'
        request_id = call.data.replace('rej_rep_', '')
    else:
        bot.answer_callback_query(call.id, "❌ داده callback نامعتبر است.")
        return
    
    if request_id not in representation_requests:
        bot.answer_callback_query(call.id, "❌ درخواست نمایندگی یافت نشد.")
        return
    
    request_data = representation_requests[request_id]
    user_id = request_data['user_id']
    user_info = request_data['user_info']
    
    if action == 'approve':
        # درخواست درصد تخفیف از ادمین
        discount_instruction = f"""
🏢 تأیید نمایندگی

👤 کاربر: {user_info['first_name']} (@{user_info['username']})
🆔 آیدی: `{user_id}`
📅 تاریخ عضویت: {user_info['join_date']}
📦 تعداد سفارشات: {user_info['total_orders']}
💰 کل هزینه: {user_info['total_spent']:,} تومان

📝 لطفا درصد تخفیف نمایندگی را وارد کنید (مثال: 10, 20, 50):
        """
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        cancel_btn = types.KeyboardButton('❌ انصراف')
        markup.add(cancel_btn)
        
        # ارسال پیام جدید برای دریافت درصد تخفیف
        bot.send_message(call.message.chat.id, discount_instruction, parse_mode="Markdown", reply_markup=markup)
        
        # ثبت مرحله بعدی برای دریافت درصد تخفیف
        bot.register_next_step_handler(call.message, lambda msg: process_representation_discount(msg, user_id, request_id))
        
        # به‌روزرسانی پیام اصلی
        bot.edit_message_text(
            f"✅ درخواست نمایندگی تأیید شد!\n\n"
            f"👤 کاربر: {user_info['first_name']} (@{user_info['username']})\n"
            f"🆔 آیدی: `{user_id}`\n\n"
            f"📝 لطفا درصد تخفیف را وارد کنید:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
    elif action == 'reject':
        # رد درخواست نمایندگی
        bot.edit_message_text(
            f"❌ درخواست نمایندگی رد شد!\n\n"
            f"👤 کاربر: {user_info['first_name']} (@{user_info['username']})\n"
            f"🆔 آیدی: `{user_id}`\n\n"
            f"📅 تاریخ رد: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
        # ارسال پیام رد به کاربر
        try:
            bot.send_message(user_id, 
                           "❌ درخواست نمایندگی شما رد شد.\n\n"
                           "💡 می‌توانید در آینده دوباره درخواست دهید.")
        except Exception as e:
            print(f"Error sending rejection message to user {user_id}: {e}")
        
        # حذف درخواست از لیست
        if request_id in representation_requests:
            del representation_requests[request_id]
            save_data()
        
    bot.answer_callback_query(call.id)

# پردازش دکمه Reply برای پیام‌های پشتیبانی
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def handle_support_reply(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔️ شما دسترسی به این عملیات را ندارید.")
        return
    
    user_id = int(call.data.split('_')[1])
    
    # بررسی وجود پیام پشتیبانی
    support_msg = None
    for msg_id, msg_data in support_messages.items():
        if msg_data['user_id'] == user_id:
            support_msg = msg_data
            break
    
    if not support_msg:
        bot.answer_callback_query(call.id, "❌ پیام پشتیبانی یافت نشد.")
        return
    
    # درخواست پیام پاسخ از ادمین
    reply_instruction = f"""
💬 پاسخ به پیام پشتیبانی

👤 کاربر: {support_msg['user_name']} (@{support_msg['username']})
🆔 آیدی: {user_id}
📅 تاریخ پیام: {support_msg['timestamp']}

💬 پیام کاربر:
{support_msg['message_text']}

📝 لطفا پیام پاسخ خود را بنویسید:
    """
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    cancel_btn = types.KeyboardButton('❌ انصراف')
    markup.add(cancel_btn)
    
    bot.send_message(call.message.chat.id, reply_instruction, reply_markup=markup)
    
    # ثبت مرحله بعدی برای دریافت پیام پاسخ
    bot.register_next_step_handler(call.message, lambda msg: process_admin_reply(msg, user_id))
    
    bot.answer_callback_query(call.id)

# تابع‌های کمکی برای مدیریت جلسات
def start_user_session(user_id, step='start'):
    """شروع جلسه جدید برای کاربر"""
    user_sessions[user_id] = {
        'step': step,
        'data': {},
        'timestamp': time.time()
    }

def update_user_session(user_id, step=None, data=None):
    """به‌روزرسانی جلسه کاربر"""
    if user_id not in user_sessions:
        start_user_session(user_id)
    
    if step:
        user_sessions[user_id]['step'] = step
    if data:
        user_sessions[user_id]['data'].update(data)
    
    user_sessions[user_id]['timestamp'] = time.time()

def get_user_session(user_id):
    """دریافت اطلاعات جلسه کاربر"""
    return user_sessions.get(user_id)

def clear_user_session(user_id):
    """پاک کردن جلسه کاربر"""
    if user_id in user_sessions:
        del user_sessions[user_id]

def is_session_valid(user_id):
    """بررسی اعتبار جلسه کاربر"""
    session = get_user_session(user_id)
    if not session:
        return False
    
    # بررسی انقضای جلسه
    if time.time() - session['timestamp'] > SESSION_TIMEOUT:
        clear_user_session(user_id)
        return False
    
    return True

# تابع‌های کمکی برای بهبود تجربه کاربری
def create_main_menu():
    """ایجاد منوی اصلی با طراحی بهتر"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buy_btn = types.KeyboardButton('🛒 خرید فیلترشکن')
    account_btn = types.KeyboardButton('👤 حساب من')
    configs_btn = types.KeyboardButton('🔐 کانفیگ‌های من')
    support_btn = types.KeyboardButton('📞 پشتیبانی')
    representation_btn = types.KeyboardButton('🏢 درخواست نمایندگی')
    admin_btn = types.KeyboardButton('⚙️ پنل مدیریت')
    
    markup.add(buy_btn, account_btn, configs_btn, support_btn, representation_btn)
    if ADMIN_ID:  # فقط برای ادمین نمایش داده شود
        markup.add(admin_btn)
    
    return markup

def create_back_button():
    """ایجاد دکمه بازگشت"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back_btn = types.KeyboardButton('🔙 بازگشت')
    home_btn = types.KeyboardButton('🏠 منوی اصلی')
    markup.add(back_btn, home_btn)
    return markup

def send_welcome_message(chat_id, user_name):
    """ارسال پیام خوش‌آمدگویی بهبود یافته"""
    welcome_text = f"""
🎉 سلام {user_name} عزیز!

به ربات فیلترشکن خوش آمدید! 🌟

�� برای شروع خرید، روی دکمه «🛒 خرید فیلترشکن» کلیک کنید
🔹 برای مشاهده حساب کاربری، روی «👤 حساب من» کلیک کنید
🔹 برای دریافت کانفیگ‌های خریداری شده، روی «🔐 کانفیگ‌های من» کلیک کنید
🔹 در صورت بروز مشکل، روی «📞 پشتیبانی» کلیک کنید

💡 نکته: تمام پرداخت‌ها امن و محافظت شده هستند.
    """
    
    markup = create_main_menu()
    bot.send_message(chat_id, welcome_text, reply_markup=markup)

# مدیریت خطاهای عمومی
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """مدیریت تمام پیام‌های غیرمنتظره"""
    user_id = message.from_user.id
    
    # بررسی مسدودیت
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "❌ شما از استفاده از این ربات مسدود شده‌اید.")
        return
    
    # بررسی اعتبار جلسه
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, 
                        "⏰ جلسه شما منقضی شده است.\n"
                        "لطفا دوباره شروع کنید.")
        start(message)
        return
    
    # پیام راهنما برای پیام‌های غیرمنتظره
    help_text = """
❓ پیام شما قابل تشخیص نیست.

🔹 برای استفاده از ربات:
• از دکمه‌های موجود استفاده کنید
• یا دستور /start را ارسال کنید
• یا دستور /help را برای راهنما ارسال کنید

💡 نکته: ربات فقط از دکمه‌ها و دستورات مشخص شده پشتیبانی می‌کند.
    """
    
    markup = create_main_menu()
    bot.send_message(message.chat.id, help_text, reply_markup=markup)

# تابع برای پاکسازی جلسات منقضی شده
def cleanup_expired_sessions():
    """پاکسازی جلسات منقضی شده"""
    current_time = time.time()
    expired_sessions = []
    
    for user_id, session in user_sessions.items():
        if current_time - session['timestamp'] > SESSION_TIMEOUT:
            expired_sessions.append(user_id)
    
    for user_id in expired_sessions:
        clear_user_session(user_id)
    
    if expired_sessions:
        print(f"Cleaned up {len(expired_sessions)} expired sessions")

# پردازش پاسخ ادمین به پیام پشتیبانی
def process_admin_reply(message, target_user_id):
    """پردازش پاسخ ادمین به پیام پشتیبانی"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '❌ انصراف':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_btn = types.KeyboardButton('🔙 بازگشت به پنل')
        markup.add(back_btn)
        
        bot.send_message(message.chat.id, 
                        "❌ پاسخ لغو شد.",
                        reply_markup=markup)
        return
    
    reply_text = message.text
    
    try:
        # ارسال پاسخ به کاربر
        admin_reply = f"""
📞 پاسخ پشتیبانی:

{reply_text}

---
💬 پشتیبانی AzizVPN
        """
        
        sent = bot.send_message(target_user_id, admin_reply)
        
        if sent:
            # تأیید ارسال به ادمین
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            back_btn = types.KeyboardButton('🔙 بازگشت به پنل')
            markup.add(back_btn)
            
            bot.send_message(message.chat.id, 
                           f"✅ پاسخ شما با موفقیت به کاربر `{target_user_id}` ارسال شد.",
                           parse_mode="Markdown",
                           reply_markup=markup)
            
            # حذف پیام پشتیبانی از حافظه
            for msg_id, msg_data in list(support_messages.items()):
                if msg_data['user_id'] == target_user_id:
                    del support_messages[msg_id]
                    break
            
            print(f"Admin reply sent to user {target_user_id}")
        else:
            bot.send_message(message.chat.id, 
                           f"❌ خطا در ارسال پاسخ به کاربر `{target_user_id}`.",
                           parse_mode="Markdown")
    
    except Exception as e:
        error_msg = f"❌ خطا در ارسال پاسخ: {str(e)}"
        bot.send_message(message.chat.id, error_msg)
        print(f"Error sending admin reply to user {target_user_id}: {e}")

# پاسخ به دکمه‌های مدیریت پشتیبانی
@bot.message_handler(func=lambda message: message.text == '📋 لیست پیام‌ها')
def support_list_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    show_pending_support_messages(message)

# پردازش درصد تخفیف نمایندگی
def process_representation_discount(message, user_id, request_id):
    """پردازش درصد تخفیف نمایندگی"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == '❌ انصراف':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_btn = types.KeyboardButton('🔙 بازگشت به پنل')
        markup.add(back_btn)
        
        bot.send_message(message.chat.id, 
                        "❌ تأیید نمایندگی لغو شد.",
                        reply_markup=markup)
        return
    
    try:
        discount_percent = int(message.text)
        
        if discount_percent < 0 or discount_percent > 100:
            bot.send_message(message.chat.id, 
                           "❌ درصد تخفیف باید بین 0 تا 100 باشد.\n"
                           "لطفا دوباره وارد کنید:")
            bot.register_next_step_handler(message, lambda msg: process_representation_discount(msg, user_id, request_id))
            return
        
        # تأیید نمایندگی و اعمال تخفیف
        if user_id in users_db:
            users_db[user_id]['is_representative'] = True
            users_db[user_id]['representative_discount'] = discount_percent
            users_db[user_id]['representation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data()
        
        # ارسال پیام تأیید به کاربر
        try:
            approval_msg = f"""
🎉 تبریک! نمایندگی شما تأیید شد!

🏢 وضعیت: نماینده تأیید شده
🎯 درصد تخفیف: {discount_percent}%
📅 تاریخ تأیید: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

💡 این تخفیف در تمام خریدهای شما اعمال خواهد شد.
            """
            
            bot.send_message(user_id, approval_msg)
        except Exception as e:
            print(f"Error sending approval message to user {user_id}: {e}")
        
        # تأیید به ادمین
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_btn = types.KeyboardButton('🔙 بازگشت به پنل')
        markup.add(back_btn)
        
        bot.send_message(message.chat.id, 
                        f"✅ نمایندگی کاربر `{user_id}` با موفقیت تأیید شد!\n\n"
                        f"🎯 درصد تخفیف: {discount_percent}%\n"
                        f"📅 تاریخ تأیید: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="Markdown",
                        reply_markup=markup)
        
        # حذف درخواست از لیست
        if request_id in representation_requests:
            del representation_requests[request_id]
            save_data()
        
        print(f"Representation approved for user {user_id} with {discount_percent}% discount")
        
    except ValueError:
        bot.send_message(message.chat.id, 
                        "❌ لطفا یک عدد معتبر وارد کنید.\n"
                        "مثال: 10, 20, 50")
        bot.register_next_step_handler(message, lambda msg: process_representation_discount(msg, user_id, request_id))

# پردازش دکمه‌های تأیید/لغو سفارش
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_order_approval(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔️ شما دسترسی به این عملیات را ندارید.")
        return
    
    action, order_id = call.data.split('_', 1)
    
    if order_id not in pending_orders:
        bot.answer_callback_query(call.id, "❌ سفارش یافت نشد.")
        return
    
    order_info = pending_orders[order_id]
    user_id = order_info['user_id']
    
    if action == 'approve':
        # تأیید سفارش - درخواست فایل کانفیگ
        bot.edit_message_text(
            f"✅ سفارش تأیید شد!\n\n"
            f"🆔 آیدی کاربر: `{user_id}`\n"
            f"👤 نام کاربری: `{order_info['username']}`\n"
            f"📊 حجم: {order_info['data_plan']}\n"
            f"⏱ مدت: {order_info['duration']}\n"
            f"💰 مبلغ: {order_info['price']:,} تومان\n\n"
            f"📁 لطفا فایل کانفیگ را ارسال کنید:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
        # ثبت مرحله بعدی برای دریافت فایل کانفیگ
        bot.register_next_step_handler(call.message, lambda msg: process_config_file(msg, user_id, order_id))
        
        # ارسال پیام تأیید به کاربر
        try:
            bot.send_message(user_id, 
                           "✅ سفارش شما تأیید شد!\n\n"
                           "فایل کانفیگ در حال آماده‌سازی است و به زودی برای شما ارسال خواهد شد.\n\n"
                           "🙏 از صبر شما متشکریم.")
        except Exception as e:
            print(f"Error sending approval message to user {user_id}: {e}")
    
    elif action == 'reject':
        # رد سفارش و مسدود کردن کاربر
        bot.edit_message_text(
            f"❌ سفارش رد شد!\n\n"
            f"🆔 آیدی کاربر: `{user_id}`\n"
            f"👤 نام کاربری: `{order_info['username']}`\n"
            f"📊 حجم: {order_info['data_plan']}\n"
            f"⏱ مدت: {order_info['duration']}\n"
            f"💰 مبلغ: {order_info['price']:,} تومان\n\n"
            f"🚫 کاربر مسدود شد.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
        # مسدود کردن کاربر
        blocked_users.add(user_id)
        save_data()
        
        # ارسال پیام رد به کاربر
        try:
            bot.send_message(user_id, 
                           "❌ سفارش شما رد شد!\n\n"
                           "اطلاعات ارسالی شما صحیح نبوده است.\n"
                           "لطفا با پشتیبانی تماس بگیرید.")
        except Exception as e:
            print(f"Error sending rejection message to user {user_id}: {e}")
    
    # حذف سفارش از لیست انتظار
    del pending_orders[order_id]
    
    bot.answer_callback_query(call.id)

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
    print(f"�� آیدی ادمین: {ADMIN_ID}")
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