import os
from dotenv import load_dotenv
from telegram import Update, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_mentor import AIMentor

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

mentor = AIMentor()

def track_user(update: Update):
    user = update.effective_user
    if user:
        mentor.db.upsert_user(
            user_id=user.id,
            username=user.username or "بدون_یوزرنیم",
            first_name=user.first_name or "کاربر"
        )

async def post_init(application: Application):
    # ۱. منوی عمومی برای همه کاربران (بدون دستور ادمین)
    public_commands = [
        BotCommand("start", "شروع و راهنمای بات 🚀"),
        BotCommand("stats", "کارنامه و مباحث تمرین‌شده 📊"),
        BotCommand("reset", "پاک کردن حافظه چت فعلی 🔄"),
    ]
    await application.bot.set_my_commands(public_commands, scope=BotCommandScopeDefault())

    # ۲. منوی اختصاصی فقط برای اکانت ادمین (شامل دستور /users)
    if ADMIN_ID != 0:
        admin_commands = public_commands + [
            BotCommand("users", "پنل مدیریت کاربران (ویژه ادمین) 👥"),
        ]
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=ADMIN_ID)
            )
        except Exception as e:
            print(f"خطا در تنظیم منوی ادمین (ابتدا یک بار به بات پیام دهید): {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)
    welcome_text = (
        "سلام همکار! من منتور شخصی تو هستم. 🚀\n\n"
        "هر مبحثی از پایتون، OOP، SQL، لینوکس یا Git رو که می‌خوای با هم کار کنیم بگو.\n"
        "📊 با دستور /stats می‌تونی کارنامه و لیست مباحثی که تا الان یاد گرفتی رو ببینی.\n"
        "🔄 با دستور /reset هم حافظه چت فعلی پاک می‌شه تا مبحث جدید شروع کنیم."
    )
    await update.message.reply_text(welcome_text)

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)
    await update.message.reply_text(f"آیدی عددی تلگرام شما: `{update.effective_user.id}`", parse_mode="Markdown")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ این دستور فقط مخصوص ادمین بات است.")
        return

    users = mentor.db.get_all_users_stats()
    if not users:
        await update.message.reply_text("هنوز هیچ کاربری ثبت نشده است.")
        return

    active_count = sum(1 for u in users if u["is_active_7d"] == 1)
    report = (
        f"👥 پنل مدیریت کاربران بات\n"
        f"کل کاربران: {len(users)} نفر | فعال در ۷ روز اخیر: {active_count} نفر\n"
        f"{'-'*30}\n\n"
    )

    for i, u in enumerate(users, 1):
        status_icon = "🟢 فعال" if u["is_active_7d"] else "⚪ غیرفعال"
        username_str = f"@{u['username']}" if u["username"] != "بدون_یوزرنیم" else "ندارد"
        report += (
            f"{i}. {u['first_name']} ({username_str}) — {u['user_id']}\n"
            f"   وضعیت: {status_icon} | پیام‌ها: {u['msg_count']}\n"
            f"   عضویت: {u['joined_date']} | آخرین فعالیت: {u['last_active']}\n\n"
        )

    for i in range(0, len(report), 4000):
        await update.message.reply_text(report[i:i+4000])

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)
    user_id = update.effective_user.id
    records = mentor.db.get_progress(user_id)

    if not records:
        await update.message.reply_text(
            "هنوز هیچ تسک کدنویسی رو کامل نکردی! 🧐\n"
            "یک مبحث رو شروع کن، به ۳ سوالش جواب بده و کدِ تسکش رو بفرست تا اولین نمره‌ات ثبت بشه."
        )
        return

    total_score = sum(r["score"] for r in records)
    avg_score = total_score / len(records)

    report = "📊 **کارنامه و مباحث تمرین‌شده تو تا امروز:**\n\n"
    for i, r in enumerate(records, 1):
        report += f"{i}. 📌 **{r['topic']}** — نمره: `{r['score']}/100` ({r['date']})\n"

    report += f"\n🏆 **تعداد مباحث تکمیل‌شده:** {len(records)} مبحث"
    report += f"\n⭐ **میانگین کل نمرات:** {avg_score:.1f} از 100"

    await update.message.reply_text(report, parse_mode="Markdown")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)
    user_id = update.effective_user.id
    with mentor.db as cursor:
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    await update.message.reply_text("حافظه چت فعلی پاک شد (نمره‌هات توی کارنامه محفوظه)! 🔄\nخب، سراغ کدوم مبحث بعدی بریم؟")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)  # ثبت/آپدیت کاربر در دیتابیس
    user_id = update.effective_user.id
    user_text = update.message.text
    print(f"پیام جدید از کاربر {user_id}: {user_text}")

    # --- تغییر کلیدی اینجاست ---
    # فعال کردن اکشن "typing..." در تلگرام
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    # ------------------------

    try:
        # درخواست به هوش مصنوعی (این بخش ممکن است چند ثانیه طول بکشد)
        reply = mentor.ask(user_id=user_id, user_message=user_text)

        # تقسیم پیام اگر طولانی‌تر از حد مجاز تلگرام (4000 کاراکتر) باشد
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i + 4000])

    except Exception as e:
        print(f"خطا در پردازش پیام: {e}")
        await update.message.reply_text(f"خطایی رخ داد: {e}")

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("توکن TELEGRAM_TOKEN در فایل .env پیدا نشد!")

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Mentor Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()