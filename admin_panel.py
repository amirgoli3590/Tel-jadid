import telebot

def admin_handler(bot, message, db, save_db):
    uid = message.chat.id

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ افزودن دسته‌بندی", "➖ حذف دسته‌بندی")
    markup.row("➕ افزودن قسمت", "➖ حذف قسمت")
    markup.row("📤 ارسال پیام به همه")
    markup.row("🔙 بازگشت")

    bot.send_message(uid, "پنل مدیریت - یک گزینه انتخاب کنید:", reply_markup=markup)

    @bot.message_handler(func=lambda m: m.chat.id == uid)
    def handle_admin_commands(msg):
        text = msg.text
        if text == "➕ افزودن دسته‌بندی":
            bot.send_message(uid, "نام دسته‌بندی جدید را ارسال کنید:")
            bot.register_next_step_handler(msg, add_category)
        elif text == "➖ حذف دسته‌بندی":
            if not db["categories"]:
                bot.send_message(uid, "هیچ دسته‌بندی‌ای موجود نیست.")
                return
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            for cat in db["categories"].keys():
                markup.row(cat)
            markup.row("🔙 بازگشت")
            bot.send_message(uid, "کدام دسته‌بندی را می‌خواهید حذف کنید؟", reply_markup=markup)
            bot.register_next_step_handler(msg, delete_category)
        elif text == "➕ افزودن قسمت":
            bot.send_message(uid, "ابتدا نام دسته‌بندی را ارسال کنید:")
            bot.register_next_step_handler(msg, add_episode_category)
        elif text == "➖ حذف قسمت":
            bot.send_message(uid, "ابتدا نام دسته‌بندی را ارسال کنید:")
            bot.register_next_step_handler(msg, delete_episode_category)
        elif text == "📤 ارسال پیام به همه":
            bot.send_message(uid, "متن پیام برای ارسال به همه کاربران را بفرستید:")
            bot.register_next_step_handler(msg, broadcast_message)
        elif text == "🔙 بازگشت":
            bot.send_message(uid, "بازگشت به منوی اصلی.")
            bot.clear_step_handler_by_chat_id(uid)
            start_message = "لطفا از منو انتخاب کنید."
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("📂 دسته‌بندی‌ها", "🛒 خرید اشتراک")
            if uid == ADMIN_ID:
                markup.row("🔧 پنل مدیریت")
            bot.send_message(uid, start_message, reply_markup=markup)
        else:
            bot.send_message(uid, "گزینه نامعتبر است. دوباره تلاش کنید.")

    def add_category(msg):
        cat_name = msg.text
        if cat_name in db["categories"]:
            bot.send_message(uid, "این دسته‌بندی قبلاً وجود دارد.")
        else:
            db["categories"][cat_name] = {}
            save_db(db)
            bot.send_message(uid, f"دسته‌بندی '{cat_name}' اضافه شد.")

    def delete_category(msg):
        cat_name = msg.text
        if cat_name in db["categories"]:
            db["categories"].pop(cat_name)
            save_db(db)
            bot.send_message(uid, f"دسته‌بندی '{cat_name}' حذف شد.")
        else:
            bot.send_message(uid, "این دسته‌بندی وجود ندارد.")

    def add_episode_category(msg):
        category = msg.text
        if category not in db["categories"]:
            bot.send_message(uid, "این دسته‌بندی وجود ندارد. دوباره ارسال کنید:")
            bot.register_next_step_handler(msg, add_episode_category)
            return
        bot.send_message(uid, "نام قسمت جدید را ارسال کنید:")
        bot.register_next_step_handler(msg, lambda m: add_episode_name(m, category))

    def add_episode_name(msg, category):
        episode_name = msg.text
        bot.send_message(uid, "آیدی فایل ویدیو را ارسال کنید:")
        bot.register_next_step_handler(msg, lambda m: add_episode_fileid(m, category, episode_name))

    def add_episode_fileid(msg, category, episode_name):
        file_id = msg.text
        db["categories"][category][episode_name] = file_id
        save_db(db)
        bot.send_message(uid, f"قسمت '{episode_name}' به دسته '{category}' اضافه شد.")

    def delete_episode_category(msg):
        category = msg.text
        if category not in db["categories"]:
            bot.send_message(uid, "این دسته‌بندی وجود ندارد. دوباره ارسال کنید:")
            bot.register_next_step_handler(msg, delete_episode_category)
            return
        if not db["categories"][category]:
            bot.send_message(uid, "هیچ قسمتی در این دسته‌بندی وجود ندارد.")
            return
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for ep in db["categories"][category].keys():
            markup.row(ep)
        markup.row("🔙 بازگشت")
        bot.send_message(uid, "کدام قسمت را می‌خواهید حذف کنید؟", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: delete_episode(m, category))

    def delete_episode(msg, category):
        episode_name = msg.text
        if episode_name in db["categories"][category]:
            db["categories"][category].pop(episode_name)
            save_db(db)
            bot.send_message(uid, f"قسمت '{episode_name}' حذف شد.")
        else:
            bot.send_message(uid, "قسمت وجود ندارد.")

    def broadcast_message(msg):
        text = msg.text
        count = 0
        for user_id in db["users"].keys():
            try:
                bot.send_message(int(user_id), text)
                count += 1
            except Exception:
                continue
        bot.send_message(uid, f"پیام به {count} کاربر ارسال شد.")
