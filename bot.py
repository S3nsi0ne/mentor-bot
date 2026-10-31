import os
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_mentor import AIMentor

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

mentor = AIMentor()

async def post_init(application: Application):
    commands = [
        BotCommand("start", "شروع و راهنمای بات 🚀"),
        BotCommand("stats", "کارنامه و مباحث تمرین‌شده 📊"),
        BotCommand("reset", "پاک کردن حافظه چت فعلی 🔄"),
    ]
    await application.bot.set_my_commands(commands)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "سلام همکار! من منتور شخصی تو هستم. 🚀\n\n"
        "هر مبحثی از پایتون، OOP، SQL، لینوکس یا Git رو که می‌خوای با هم کار کنیم بگو.\n"
        "📊 با دستور /stats می‌تونی کارنامه و لیست مباحثی که تا الان یاد گرفتی رو ببینی.\n"
        "🔄 با دستور /reset هم حافظه چت فعلی پاک می‌شه تا مبحث جدید شروع کنیم (نمره‌هات پاک نمی‌شن!)."
    )
    await update.message.reply_text(welcome_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    user_id = update.effective_user.id
    with mentor.db as cursor:
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    await update.message.reply_text("حافظه چت فعلی پاک شد (نمره‌هات توی کارنامه محفوظه)! 🔄\nخب، سراغ کدوم مبحث بعدی بریم؟")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    print(f"پیام جدید از کاربر {user_id}: {user_text}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = mentor.ask(user_id=user_id, user_message=user_text)
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Mentor Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()