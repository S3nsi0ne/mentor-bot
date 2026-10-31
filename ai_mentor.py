import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import DatabaseManager

load_dotenv()

SYSTEM_PROMPT = """
تو یک منتور، همکار ارشد و معلم دلسوز مهندسی نرم‌افزار (پایتون، OOP، SQL، لینوکس و Git) هستی.
دانشجوی تو در بوت‌کمپ مکتب شریف است و می‌خواهد تا ۳ ماه دیگر آماده بازار کار شود.

قانون تو برای آموزش هر مبحث این ۳ مرحله است (هر بار فقط یک مرحله را جلو ببر و منتظر پاسخ دانشجو بمان):
۱. آموزش و پرسش: مبحث درخواستی را به زبان ساده و با مثال کاربردی توضیح بده. در انتهای پیام، دقیقا ۳ سوال مفهومی کوتاه بپرس تا مطمئن شوی مطلب را گرفته است.
۲. بررسی و تعریف تسک: پاسخ دانشجو به ۳ سوال را بررسی کن. اگر اشتباهی داشت اصلاح کن و سپس ۱ تسک کدنویسی عملی مرتبط با همان مبحث به او بده.
۳. ریویو کد (Code Review): کدی که دانشجو می‌فرستد را خط‌به‌خط بررسی کن. اگر باگ داشت راهنمایی کن تا خودش اصلاح کند، و اگر تمیز بود تشویقش کن و بپرس سراغ کدام مبحث بعدی برویم.
"""


class AIMentor:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("کلید GEMINI_API_KEY در فایل .env پیدا نشد!")

        self.client = genai.Client(api_key=api_key)
        self.db = DatabaseManager()
        # لیست مدل‌ها به ترتیب اولویت (اگر اولی شلوغ بود، دومی و سومی تست می‌شوند)
        self.models = ["gemini-3.8-flash", "gemini-3.8-flash-lite", "gemini-3.8-pro"]

    def ask(self, user_id: int, user_message: str) -> str:
        # ۱. خواندن تاریخچه قبلی از دیتابیس
        history_rows = self.db.get_history(user_id, limit=10)

        contents = []
        for row in history_rows:
            role = "user" if row["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=row["content"])])
            )

        # اضافه کردن پیام فعلی کاربر به لیست ارسالی
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
        )

        # ۲. تلاش برای گرفتن جواب از مدل‌ها به ترتیب لیست
        last_error = None
        reply_text = None

        for model_name in self.models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.4,
                    )
                )
                reply_text = response.text
                break  # به محض اینکه یکی از مدل‌ها جواب داد، از حلقه خارج شو
            except Exception as e:
                print(f"مدل {model_name} در دسترس نبود: {e}")
                last_error = e

        if reply_text is None:
            raise last_error

        # ۳. حالا که جواب با موفقیت گرفته شد، هر دو پیام را در دیتابیس ذخیره کن
        self.db.add_message(user_id, "user", user_message)
        self.db.add_message(user_id, "model", reply_text)
        return reply_text