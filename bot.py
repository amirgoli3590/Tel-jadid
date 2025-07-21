import telebot
import json
import datetime
import threading
import os
from admin_panel import admin_handler

TOKEN = "7150163966:AAGpnIy0ztrk7fOci9MRCh_IbcktS8YI5NA"
CHANNEL_USERNAME = "@amiramir3590"
ADMIN_ID = 7536757725
DB_FILE = "database.json"

bot = telebot.TeleBot(TOKEN)

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"users": {}, "categories": {}}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

def has_access(user_id):
    user = db["users"].get(str(user_id))
    if not user:
        return False
    expire_date = datetime.datetime.strptime(user["expire_date"], "%Y-%m-%d")
    return datetime.datetime.now() <= expire_date

def notify_expiring_users():
    while True:
        now = datetime.datetime.now()
        for uid, data in db["users"].items():
            expire_date = datetime.datetime.strptime(data["expire_date"], "%Y-%m-%d")
            if (expire_date - now).days == 1 and not data.get("notified"):
                try:
                    bot.send_message(int(uid), "⏳ اشتراک شما فردا منقضی می‌شود. لطفاً تمدید کنید.")
                    db["users"][uid]["notified"] = True
                    save_db(db)
                except Exception:
                    pass
        threading.Event().wait(86400)

threading.Thread(target=notify_expiring_users, daemon=True).start()

@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.chat.id)
    if uid not in db["users"]:
        start_date = datetime.datetime.now()
        expire_date = start_date + datetime.timedelta(days=7)
        db["users"][uid] = {
            "username": message.from_user.username,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "expire_date": expire_date.strftime("%Y-%m-%d"),
            "is_premium": False,
            "notified": False,
        }
        save_db(db)
        bot.send_message(uid, "🎉 خوش آمدید! ۷ روز دسترسی رایگان دارید.")
    else:
        bot.send_message(uid, "👋 خوش آمدید.")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📂 دسته‌بندی‌ها", "🛒 خرید اشتراک")
    if int(uid) == ADMIN_ID:
        markup.row("🔧 پنل مدیریت")
    bot.send_message(uid, "لطفا از منو گزینه‌ای انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📂 دسته‌بندی‌ها")
def show_categories(message):
    uid = str(message.chat.id)
    if not has_access(uid):
        bot.send_message(uid, "⛔ اشتراک شما منقضی شده است. لطفا اشتراک خود را تمدید کنید.")
        return
    if not db["categories"]:
        bot.send_message(uid, "📂 هنوز دسته‌بندی‌ای اضافه نشده است.")
        return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in db["categories"].keys():
        markup.row(cat)
    markup.row("🔙 بازگشت")
    bot.send_message(uid, "📂 یک دسته‌بندی انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in db["categories"].keys())
def show_episodes(message):
    uid = str(message.chat.id)
    category = message.text
    episodes = db["categories"][category]
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for ep in episodes.keys():
        markup.row(ep)
    markup.row("🔙 بازگشت")
    bot.send_message(uid, f"🎬 قسمت‌های {category}:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in eps for eps in db["categories"].values()))
def send_video(message):
    uid = str(message.chat.id)
    if not has_access(uid):
        bot.send_message(uid, "⛔ اشتراک شما منقضی شده است.")
        return
    for category, episodes in db["categories"].items():
        if message.text in episodes:
            file_id = episodes[message.text]
            sent_msg = bot.send_video(uid, file_id)
            bot.send_message(uid, "🎥 این ویدیو ۳۰ ثانیه بعد حذف خواهد شد، لطفا ذخیره کنید.")
            threading.Timer(30, lambda: bot.delete_message(uid, sent_msg.message_id)).start()
            break

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت")
def back(message):
    start(message)

@bot.message_handler(func=lambda m: m.text == "🔧 پنل مدیریت")
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        admin_handler(bot, message, db, save_db)
    else:
        bot.send_message(message.chat.id, "⚠️ شما دسترسی به پنل مدیریت ندارید.")

print("🤖 ربات آماده است.")
bot.polling()
