import os
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_mentor import AIMentor

# بارگذاری توکن‌ها از فایل .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ساختن یک نمونه از کلاس منتور هوش مصنوعی
mentor = AIMentor()


# تنظیم خودکار دکمه‌های منوی پایین تلگرام هنگام روشن شدن بات
async def post_init(application: Application):
    commands = [
        BotCommand("start", "شروع و راهنمای بات 🚀"),
        BotCommand("reset", "پاک کردن حافظه و شروع مبحث جدید 🔄"),
    ]
    await application.bot.set_my_commands(commands)


# ۱. تابع مربوط به دستور /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "سلام همکار! من منتور شخصی تو هستم. 🚀\n\n"
        "هر مبحثی از پایتون، OOP، SQL، لینوکس یا Git رو که می‌خوای با هم کار کنیم بگو "
        "(مثلاً بنویس: «بیا Context Manager رو شروع کنیم»).\n\n"
        "هر وقت هم خواستی حافظه‌ام پاک بشه و مبحث جدید شروع کنیم، از منوی پایین دستور /reset رو بزن."
    )
    await update.message.reply_text(welcome_text)


# ۲. تابع مربوط به دستور /reset (پاک کردن حافظه دیتابیس)
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with mentor.db as cursor:
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    await update.message.reply_text("حافظه جلسه قبلی پاک شد! 🔄\nخب، سراغ کدوم مبحث بریم؟")


# ۳. تابع دریافت پیام‌های معمولی و ارسال به جمینای
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    print(f"پیام جدید از کاربر {user_id}: {user_text}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = mentor.ask(user_id=user_id, user_message=user_text)
        print("پاسخ از جمینای دریافت شد، در حال ارسال به تلگرام...")

        # تقسیم پیام اگر طولانی‌تر از حد مجاز تلگرام (4000 کاراکتر) باشد
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i + 4000])

    except Exception as e:
        print(f"خطا در پردازش پیام: {e}")
        await update.message.reply_text(f"خطایی رخ داد: {e}")


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("توکن TELEGRAM_TOKEN در فایل .env پیدا نشد!")

    # ساختن اپلیکیشن تلگرام و اتصال تابع منوساز (post_init)
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Mentor Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()