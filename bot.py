import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_mentor import AIMentor

# بارگذاری توکن‌ها از فایل .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ساختن یک نمونه از کلاس منتور هوش مصنوعی
mentor = AIMentor()

# ۱. تابع مربوط به دستور /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "سلام همکار! من منتور شخصی تو هستم. 🚀\n\n"
        "هر مبحثی از پایتون، OOP، SQL، لینوکس یا Git رو که می‌خوای با هم کار کنیم بگو "
        "(مثلاً بنویس: «بیا Context Manager رو شروع کنیم»).\n\n"
        "هر وقت هم خواستی حافظه‌ام پاک بشه و مبحث جدید شروع کنیم، دستور /reset رو بزن."
    )
    await update.message.reply_text(welcome_text)

# ۲. تابع مربوط به دستور /reset (پاک کردن حافظه دیتابیس)
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with mentor.db as cursor:
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    await update.message.reply_text("حافظه جلسه قبلی پاک شد! خب، سراغ کدوم مبحث بریم؟")

# ۳. تابع دریافت پیام‌های معمولی و ارسال به جمینای
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # نشان دادن عبارت "typing..." بالای صفحه تلگرام تا جواب آماده شود
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # گرفتن جواب از هوش مصنوعی و دیتابیس
        reply = mentor.ask(user_id=user_id, user_message=user_text)
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"خطایی رخ داد: {e}")

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("توکن TELEGRAM_TOKEN در فایل .env پیدا نشد!")

    # ساختن اپلیکیشن تلگرام و معرفی دستورات به آن
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Mentor Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()